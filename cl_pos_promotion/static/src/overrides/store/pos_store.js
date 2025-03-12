import { PosStore } from "@point_of_sale/app/store/pos_store";
import { patch } from "@web/core/utils/patch";

patch(PosStore.prototype, {
    async addLineToOrder(vals, order, opts = {}, configure = true) {
        var res = await super.addLineToOrder(...arguments);
        if(res && res.promotion_ids.length === 0){
            order.compute_cl_promotions()
        }
        return res;
    },
});
