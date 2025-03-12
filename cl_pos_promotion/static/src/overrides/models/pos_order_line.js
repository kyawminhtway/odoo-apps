import { PosOrderline } from "@point_of_sale/app/models/pos_order_line";
import { patch } from "@web/core/utils/patch";

patch(PosOrderline.prototype, {
    set_quantity(quantity, keep_price) {
        var res = super.set_quantity(...arguments);
        if(this.promotion_ids.length === 0){
            this.order_id.compute_cl_promotions();
        }
        return res;
    },
    set_unit_price(price){
        var res = super.set_unit_price(...arguments);
        if(this.promotion_ids.length === 0){
            this.order_id.compute_cl_promotions();
        }
        return res;
    },
    set_discount(discount){
        var res = super.set_discount(...arguments);
        if(this.promotion_ids.length === 0){
            this.order_id.compute_cl_promotions();
        }
        return res;
    },
    can_be_merged_with(orderline) {
        if(this.promotion_ids.length > 0 || orderline.promotion_ids.length > 0){
            return false;
        }
        return super.can_be_merged_with(...arguments);
    },
    getDisplayData() {
        const promotions = this.promotion_json || '[]';
        var vals = {
            ...super.getDisplayData(...arguments),
            promotion_ids: JSON.parse(promotions),
        };
        return vals;
    },
});
