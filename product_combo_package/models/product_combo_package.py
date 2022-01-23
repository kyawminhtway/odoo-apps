from re import I
from odoo import api, models, fields
from odoo.exceptions import UserError


class ProductComboPackage(models.Model):

    _name = 'product.combo.package'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Product Combo Package'

    def _get_default_location(self):
        return self.env['stock.location'].search([('usage', '=', 'internal')], order='id', limit=1).id

    name = fields.Char('Name', default='Draft')
    date = fields.Datetime('Date', default=fields.Datetime.now)
    product_id = fields.Many2one('product.product', domain=[('is_combo_package', '=', True)])
    quantity = fields.Float('Quantity', digits='Product Unit of Measure', default=1)
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.company.id)
    user_id = fields.Many2one('res.users', 'Responsible', default=lambda self: self.env.user.id)
    item_location_id = fields.Many2one('stock.location', 'Item Location', 
                                       domain=[('usage', '=', 'internal')],
                                       default=_get_default_location)
    combo_product_loc_id = fields.Many2one('stock.location', 'Package Location', 
                                           domain=[('usage', '=', 'internal')],
                                           default=_get_default_location)
    item_ids = fields.One2many('product.combo.package.item', 'package_id', 'Items')
    extra_cost_ids = fields.One2many('product.combo.extra.cost', 'package_id', 'Extra Cost')
    remarks = fields.Text('Remarks')
    state = fields.Selection([('draft', 'Draft'),
                              ('confirm', 'In Progress'),
                              ('validate', 'Done'),
                              ('cancel', 'Cancelled')], default='draft')

    def btn_confirm(self):
        self.write({'state': 'confirm'})
    
    def btn_validate(self):
        stock.insufficient.warning
        out_of_stock_items = []
        self.ensure_one()
        if not self.state == 'confirm':
            return
        for item in self.item_ids:
            item_qty = item.uom_id._compute_quantity(item.quantity, item.item_id.uom_id)
            quants = self.env['stock.quant']._gather(item.item_id.id, item.location_id.id)
            on_hand_qty = sum(quants.mapped('quantity'))
            if item_qty > on_hand_qty:
                out_of_stock_items.append(
                    (0, 0, {
                        'product_id': item.item_id,
                        'requested_qty': item_qty,
                        'on_hand_qty': on_hand_qty,
                    })
                )
        if out_of_stock_items:
            return {
                'name': 'Infusfficient Stock',
                'type': 'ir.actions.act_window',
                'res_model': 'stock.insufficient.warning',
                'view_mode': 'form',
                'context': {
                    'default_package_id': self.id,
                    'default_line_ids': out_of_stock_items,
                },
            }
    
    def btn_cancel(self):
        self.write({'state': 'cancel'})
    
    def unlink(self):
        if any([rec.state not in ['draft', 'cancel'] for rec in self]):
            raise UserError('You can only delete draft and cancelled records.')
        return super().unlink()


class ProductComboPackageItem(models.Model):

    _name = 'product.combo.package.item'
    _description = 'Combo Package Items'

    @api.model
    def _get_default_location(self):
        return self.env.context.get('location', self.env['stock.locatoin']).id

    item_id = fields.Many2one('product.product', 'Item')
    quantity = fields.Float('Quantity', digits='Product Unit of Measure', default=1)
    uom_id = fields.Many2one('uom.uom', 'UoM')
    unit_cost = fields.Float('Unit Cost', digits='Product Price', compute='compute_unit_cost', store=True)
    total_cost = fields.Float('Total Cost', digits='Product Price', compute='compute_total_cost', store=True)
    product_id = fields.Many2one('product.product', 'Product', ondelete='cascade')
    package_id = fields.Many2one('product.combo.package', 'Package', ondelete='cascade')
    location_id = fields.Many2one('stock.location', 'Location', domain=[('usage', '=', 'internal')], default=_get_default_location)

    @api.onchange('item_id')
    def onchange_product(self):
        self.uom_id = self.item_id.uom_id.id

    @api.depends('item_id')
    def compute_unit_cost(self):
        for rec in self:
            rec.unit_cost = rec.item_id.standard_price
    
    @api.depends('quantity', 'uom_id', 'unit_cost')
    def compute_total_cost(self):
        for rec in self:
            qty = rec.uom_id._compute_quantity(rec.quantity, rec.item_id.uom_id)
            rec.total_cost = rec.unit_cost * qty


class ProductComboExtraCost(models.Model):

    _name = 'product.combo.extra.cost'
    _description = 'Combo Package Extra Cost'
    _rec_name = 'description'

    description = fields.Char('Description')
    cost = fields.Float('Cost')
    package_id = fields.Many2one('product.combo.package', 'Package', ondelete='cascade')
