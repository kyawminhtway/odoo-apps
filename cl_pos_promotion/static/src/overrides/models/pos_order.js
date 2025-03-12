import { PosOrder } from "@point_of_sale/app/models/pos_order";
import { patch } from "@web/core/utils/patch";
import { formatCurrency } from "@point_of_sale/app/models/utils/currency";


const TYPES_DISCOUNT = ['fixed_discount', 'percent_discount'];
const TYPES_AMOUNT = ['buy_more_than_x_amount', 'buy_more_than_x_amount_from_categories', 'buy_more_than_x_amount_from_products'];
const TYPES_QTY = ['buy_more_than_x_qty', 'buy_more_than_x_qty_from_categories', 'buy_more_than_x_qty_from_products'];
const TYPES_CATEGORY = ['buy_more_than_x_amount_from_categories', 'buy_more_than_x_qty_from_categories'];
const TYPES_PRODUCT = ['buy_more_than_x_amount_from_products', 'buy_more_than_x_qty_from_products'];


patch(PosOrder.prototype, {
    setup(vals){
        var res = super.setup(...arguments);
        this.uiState = {...this.uiState, promotionApplicable: false};
        return res;
    },
    removeOrderline(line) {
        var res = super.removeOrderline(...arguments);
        if(line.promotion_ids.length === 0){
            this.compute_cl_promotions();
        }
        return res;
    },
    remove_cl_programs(){
        var toDelete = [];
        var orderlines = this.lines;
        for(var orderline of orderlines){
            if(orderline.promotion_ids.length > 0){
                toDelete.push(orderline);
            }
        }
        toDelete.forEach(line => line.delete());
    },
    async add_promotion_product(env, vals, programs){
        var line = await env.addLineToCurrentOrder(vals, {});
        line.update({ promotion_json: JSON.stringify(programs) });
        return line;
    },
    async apply_cl_programs(program_ids, env){
        this.remove_cl_programs();
        var merged_discount=0, merged_promotions=[], merged_promotions_info=[], merged_discount_product_id=false;
        var applicable_programs = this.cl_applicable_programs;
        for(var program_id of program_ids){
            var program = applicable_programs[program_id];
            var promotion_program = this.models['promotion.program'].get(program_id);
            var item = promotion_program.item_id;
            var occurrence = program.rule_occurrence;
            occurrence = item.item_rule === 'max_occurrence' && item.max_occurrence > 0 && occurrence > item.max_occurrence ? item.max_occurrence : occurrence;
            if(TYPES_DISCOUNT.includes(item.type)){
                if(item.type === 'fixed_discount'){
                    if(item.discount_rule !== 'order'){
                        occurrence = program.item.quantity;
                        occurrence = item.item_rule === 'max_occurrence' && item.max_occurrence > 0 && occurrence > item.max_occurrence ? item.max_occurrence : occurrence;
                    }
                    var price = item.discount * occurrence;
                }else{
                    if(item.discount_rule !== 'order'){
                        var amount = program.item.amount;
                    }else{
                        var amount = this.cl_promotion_utilities.amount.overall[item.price_rule];
                    }
                    var price = Math.round((amount * (item.discount / 100)) * 100) / 100;
                }
                price = item.max_discount > 0 && price > item.max_discount ? item.max_discount : price;
                var amount_discount = `${formatCurrency(price, this.currency)}`;
                if(promotion_program.can_be_merged){
                    merged_discount += price;
                    merged_promotions.push(promotion_program);
                    merged_promotions_info.push({ id: program_id, name: promotion_program.name, discount: amount_discount });
                    merged_discount_product_id = merged_discount_product_id === false ? item.product_id : merged_discount_product_id;
                }else{
                    await this.add_promotion_product(env, {
                        product_id: item.product_id,
                        qty: 1,
                        price_unit: price * -1,
                        promotion_ids: [['link', promotion_program]]
                    }, [{ id: program_id, name: promotion_program.name, discount: amount_discount }]);
                }
            }else if(item.type === 'free_product'){
                var free_product_ids = item.free_product_ids;
                for(var free_product of free_product_ids){
                    await this.add_promotion_product(env, {
                        product_id: free_product.product_id,
                        qty: free_product.qty * occurrence,
                        price_unit: 0,
                        promotion_ids: [['link', promotion_program]]
                    }, [{id: program_id, name: promotion_program.name}]);
                }
            }
        }
        if(merged_discount > 0 && merged_discount_product_id){
            await this.add_promotion_product(env, {
                product_id: merged_discount_product_id,
                qty: 1,
                price_unit: merged_discount * -1,
                promotion_ids: [['link', ...merged_promotions]]
            }, merged_promotions_info);
        }
    },
    compute_cl_promotions(){
        this.prepare_cl_promotions_utilities();
        var applicable_programs={};
        var partner_id = this.get_partner() && this.get_partner().id || false;
        var promotion_programs = this.models['promotion.program'].readAll();
        for(var promotion_program of promotion_programs){
            // Check Customer
            var partner_ids = promotion_program.partner_ids.map(e => e.id);
            if(partner_ids.length > 0 && !partner_ids.includes(partner_id)){
                continue;
            }

            // Check Rule
            var occurrence=0;
            var rule = promotion_program.rule_id;
            if(TYPES_AMOUNT.includes(rule.type)){
                occurrence = this.get_cl_promotion_x_occurrence('amount', rule, rule.min_amt);
            }else if(TYPES_QTY.includes(rule.type)){
                occurrence = this.get_cl_promotion_x_occurrence('quantity', rule, rule.min_qty);
            }else if(rule.type === 'buy_combo_products'){
                occurrence = this.get_cl_promotion_combo_products_occurrence(rule);
            }
            var applicable = occurrence > 0;
            if(applicable){
                applicable_programs[promotion_program.id] = {rule_occurrence: occurrence};
            }

            // Check Item
            var item = promotion_program.item_id;
            if(TYPES_DISCOUNT.includes(item.type) && item.discount_rule !== 'order'){
                var { amount, quantity } = this.check_discount_applicable(item);
                if(amount <= 0 || quantity <= 0){
                    for(var program_id of item.program_ids){
                        delete applicable_programs[program_id.id];
                    }
                    continue;
                }
                if(applicable_programs[promotion_program.id] !== undefined){
                    applicable_programs[promotion_program.id].item = {amount, quantity};
                }
            }
        }

        this.cl_applicable_programs = applicable_programs;
        this.uiState.promotionApplicable = Object.keys(applicable_programs).length > 0;
    },
    prepare_cl_promotions_utilities(){
        var amount = {overall: {tax_exclusive: 0, tax_inclusive: 0, discount_inclusive: 0}, by_product: {}, by_category: {}};
        var quantity = {overall: 0, by_product: {}, by_category: {}};
        for(var orderline of this.lines){
            if(orderline.promotion_ids.length > 0){
                continue;
            }
            var product_id = orderline.product_id.id;
            var category_ids = orderline.product_id.pos_categ_ids.map(e => e.id);
            
            // Grouped Amount & Quantity By Product, By Category & Overall
            var prices = orderline.get_all_prices();
            var tax_exclusive = prices.priceWithoutTax;
            var tax_inclusive = prices.priceWithTaxBeforeDiscount;
            var discount_inclusive = prices.priceWithTax;
            var qty = orderline.get_quantity();
            
            amount.overall.tax_exclusive += tax_exclusive;
            amount.overall.tax_inclusive += tax_inclusive;
            amount.overall.discount_inclusive += discount_inclusive;
            quantity.overall += qty;

            var grouped_by_product = this.get_grouped_value(amount.by_product, product_id);
            grouped_by_product.tax_exclusive += tax_exclusive;
            grouped_by_product.tax_inclusive += tax_inclusive;
            grouped_by_product.discount_inclusive += discount_inclusive;
            amount.by_product[product_id] = grouped_by_product;
            quantity.by_product[product_id] = (quantity.by_product[product_id] || 0) + qty;
            
            for(var category_id of category_ids){
                var grouped_by_category= this.get_grouped_value(amount.by_category, category_id);
                grouped_by_category.tax_exclusive += tax_exclusive;
                grouped_by_category.tax_inclusive += tax_inclusive;
                grouped_by_category.discount_inclusive += discount_inclusive;
                amount.by_category[category_id] = grouped_by_category;
                quantity.by_category[category_id] = (quantity.by_category[category_id] || 0) + qty;
            }
        }
        this.cl_promotion_utilities = {amount, quantity};
    },
    prepare_occurrence(value, min_value){
        return Math.floor(parseFloat(value) / parseFloat(min_value)) 
    },
    get_grouped_value(grouped_value, record_id){
        var values = grouped_value[record_id];
        if(values === undefined){
            values = {tax_exclusive: 0, tax_inclusive: 0, discount_inclusive: 0};
        }else{
            values = {
                tax_exclusive: values.tax_exclusive || 0, 
                tax_inclusive: values.tax_inclusive || 0, 
                discount_inclusive: values.discount_inclusive || 0
            };
        }
        return values;
    },
    check_discount_applicable(item){
        var amount=0, quantity=0;
        var utilities = this.cl_promotion_utilities;
        var item_record_ids = item.discount_rule === 'product' ? item.product_ids.map(e => e.id) : item.category_ids.map(e => e.id);
        var order_records = item.discount_rule === 'product' ? utilities.amount.by_product : utilities.amount.by_category;
        for(var order_record in order_records){
            var record_id = parseInt(order_record);
            if((new Set(item_record_ids)).has(record_id)){
                amount += utilities.amount[`by_${item.discount_rule}`][record_id][item.price_rule];
                quantity += utilities.quantity[`by_${item.discount_rule}`][record_id];
            }
        }
        return {amount, quantity};
    },
    get_cl_promotion_x_occurrence(type, rule, min_value){
        var utilities = this.cl_promotion_utilities;
        var value=0, rule_record_ids=[], order_record_ids=[];
        if(TYPES_CATEGORY.includes(rule.type)){
            rule_record_ids = rule.category_ids.map(e => e.id);
        }else if(TYPES_PRODUCT.includes(rule.type)){
            rule_record_ids = rule.product_ids.map(e => e.id);
        }else{
            value = type === 'amount' ? utilities.amount.overall[rule.price_rule] : utilities.quantity.overall;
            return this.prepare_occurrence(value, min_value);
        }

        if(TYPES_CATEGORY.includes(rule.type)){
            order_record_ids = type === 'amount' ? utilities.amount.by_category : utilities.quantity.by_category;
        }else if(TYPES_PRODUCT.includes(rule.type)){
            order_record_ids = type === 'amount' ? utilities.amount.by_product : utilities.quantity.by_product;
        }

        for(var order_record_id in order_record_ids){
            order_record_id = parseInt(order_record_id);
            var record = order_record_ids[order_record_id];
            if((new Set(rule_record_ids)).has(order_record_id)){
                value += type === 'amount' ? record[rule.price_rule] : record;
            }
        }
        return this.prepare_occurrence(value, min_value);
    },
    get_cl_promotion_combo_products_occurrence(rule){
        var occurrence = 0;
        var utilities = this.cl_promotion_utilities;
        for(var combo_line of rule.combo_line_ids){
            var qty = 0;
            var record_ids = combo_line.based_on === 'product' ? combo_line.product_ids : combo_line.category_ids;
            for(var record_id of record_ids){
                qty += utilities.quantity[`by_${combo_line.based_on}`][record_id.id] || 0;
            }
            var line_occurrence = this.prepare_occurrence(qty, combo_line.qty);
            if(line_occurrence <= 0){
                occurrence = 0;
                break;
            }else if(occurrence === 0 || line_occurrence < occurrence){
                occurrence = line_occurrence;
            }
        }
        return occurrence;
    },
});