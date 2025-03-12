import { _t } from "@web/core/l10n/translation";
import { Component, useState } from "@odoo/owl";
import { Dialog } from "@web/core/dialog/dialog";

export class SelectProgramPopup extends Component {
    static template = "cl_pos_promotion.SelectProgramPopup";
    static components = { Dialog };
    static props = {
        title: { type: String, optional: true },
        items: { type: Array, optional: true },
        getPayload: Function,
        close: Function,
    };
    static defaultProps = {
        title: _t("Select"),
        items: [],
    };
    setup() {
        this.state = useState({ selectedIds: new Set() });
    }
    selectAll(){
        if(this.state.selectedIds.size === this.props.items.length){
            this.state.selectedIds = new Set();
        }else{
            this.props.items.forEach(record => this.state.selectedIds.add(record.id))
        }
    }
    selectItem(itemId) {
        if(this.state.selectedIds.has(itemId)){
            this.state.selectedIds.delete(itemId);

        }else{
            this.state.selectedIds.add(itemId);
        }
    }
    confirm() {
        this.props.getPayload(this.state.selectedIds);
        this.props.close();
    }
}
