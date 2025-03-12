import { _t } from "@web/core/l10n/translation";
import { ControlButtons } from "@point_of_sale/app/screens/product_screen/control_buttons/control_buttons";
import { makeAwaitable } from "@point_of_sale/app/store/make_awaitable_dialog";
import { SelectProgramPopup } from "@cl_pos_promotion/app/utils/select_program_popup";
import { patch } from "@web/core/utils/patch";


patch(ControlButtons.prototype, {
    async onClickSelectPromotionProgram() {
        var items = [];
        var applicable_programs = this.currentOrder.cl_applicable_programs || [];
        for(var program_id of Object.keys(applicable_programs)){
            items.push(this.pos.models['promotion.program'].get(parseInt(program_id)));
        }
        const payload = await makeAwaitable(this.dialog, SelectProgramPopup, {
            title: _t("Promotion Programs"),
            items: items
        });
        if(!payload) return;
        await this.currentOrder.apply_cl_programs(payload, this.pos);
        return true;
    },
});
