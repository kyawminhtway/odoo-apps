from odoo import api, models, fields


class PosOrderLine(models.Model):

    _inherit = 'pos.order.line'

    promotion_ids = fields.Many2many('promotion.program', 'pos_order_line_promotion_rel', 'line_id', 'promotion_id', 'Promotion Programs')
    promotion_json = fields.Text('Promotion JSON')

    @api.model
    def _load_pos_data_fields(self, config_id):
        fields_to_load = super()._load_pos_data_fields(config_id)
        fields_to_load.extend(['promotion_ids', 'promotion_json'])
        return fields_to_load

