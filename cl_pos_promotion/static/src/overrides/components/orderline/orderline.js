import { Orderline } from "@point_of_sale/app/generic_components/orderline/orderline";
import { patch } from "@web/core/utils/patch";

patch(Orderline, {
    props: {
        ...Orderline.props,
        line: {
            ...Orderline.props.line,
            shape: {
                ...Orderline.props.line.shape,
                promotion_ids: { 
                    type: Array, 
                    optional: true,
                    element: {
                        type: Object,
                        shape: {
                            id: Number,
                            name: String,
                            discount: {
                                type: String,
                                optional: true
                            },
                        }
                    },
                },
            },
        },
    },
});
