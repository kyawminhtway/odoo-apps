from string import digits
from odoo import api, models, fields


class StockInsufficientWarning(models.TransientModel):

    _name = 'stock.insufficient.warning'
    _description = 'Stock Insufficient Warning'

    package_id = fields.Many2one('product.combo.package', 'Package', required=1)
    line_ids = fields.One2many('stock.insufficient.warning.line', 'wizard_id', 'Lines')

    def btn_confirm(self):
        pass


class StockInsufficientWarningLine(models.TransientModel):

    _name = 'stock.insufficient.warning.line'
    _description = 'Stock Insufficient Warning Line'

    product_id = fields.Many2one('product.product', 'Product')
    requested_qty = fields.Float('Requested Qty', digits='Product Unit of Measure')
    on_hand_qty = fields.Float('On Hand Qty', digits='Product Unit of Measure')
    wizard_id = fields.Many2one('stock.insufficient.warning', 'Wizard')

