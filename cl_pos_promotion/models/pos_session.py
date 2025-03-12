from odoo import api, models, fields


class PosSession(models.Model):

    _inherit = 'pos.session'

    @api.model
    def _load_pos_data_models(self, config_id):
        res = super()._load_pos_data_models(config_id)
        res.extend([
            'promotion.program',
            'promotion.rule',
            'promotion.item',
            'promotion.combo.line',
            'promotion.free.product',
        ])
        return res

