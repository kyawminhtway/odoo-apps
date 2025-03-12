from odoo import api, models, fields


class PosConfig(models.Model):

    _inherit = 'pos.config'

    @api.model
    def _get_special_products(self):
        res = super()._get_special_products()
        domain = self.env['promotion.program']._load_pos_data_domain({'pos.config': {'data': [{'id': self.id}]}})
        res |= self.env['promotion.program'].search(domain).item_id.product_id
        return res

