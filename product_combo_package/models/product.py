from odoo import api, models, fields


class ProductTemplate(models.Model):

    _inherit = 'product.template'

    is_combo_package = fields.Boolean('Combo Package', 
                                      compute='_compute_is_combo_package', 
                                      inverse='_set_is_combo_package',
                                      search='_search_is_combo_package')
    combo_package_ids = fields.One2many(comodel_name='product.combo.package.item', 
                                        string='Combo Package Items', 
                                        compute='_compute_combo_package_ids',
                                        inverse='_set_combo_package_ids',
                                        help='Combo Items included in this product.',
                                        search='search_combo_package_ids')

    @api.depends('product_variant_ids', 'product_variant_ids.is_combo_package') 
    def _compute_is_combo_package(self):
        for template in self:
            for template in self:
                if len(template.product_variant_ids) == 1:
                    template.is_combo_package = template.product_variant_id.is_combo_package
                else:
                    template.is_combo_package = False
    
    def _set_is_combo_package(self):
        for template in self:
            if len(template.product_variant_ids) == 1:
                template.product_variant_id.is_combo_package = template.is_combo_package

    @api.depends('product_variant_ids', 'product_variant_ids.combo_package_ids') 
    def _compute_combo_package_ids(self):
        for template in self:
            if len(template.product_variant_ids) == 1:
                template.combo_package_ids = template.product_variant_id.combo_package_ids
            else:
                template.combo_package_ids = False
    
    def _set_combo_package_ids(self):
        for template in self:
            if len(template.product_variant_ids) == 1:
                template.product_variant_id.combo_package_ids = template.combo_package_ids

    def _search_is_combo_package(self, operator, value):
        products = self.env['product.product'].search([('is_combo_package', operator, value)], limit=None)
        return [('id', 'in', products.mapped('product_tmpl_id').ids)]
    
    def search_combo_package_ids(self, operator, value):
        products = self.env['product.product'].search([('combo_package_ids', operator, value)], limit=None)
        return [('id', 'in', products.mapped('product_tmpl_id').ids)]

    def _prepare_variant_values(self, combination):
        values = super()._prepare_variant_values(combination)
        combo_package_ids = []
        for line in self.combo_package_ids:
            combo_package_ids.append(
                (0, 0, {
                    'item_id': line.item_id.id,
                    'quantity': line.quantity,
                    'uom_id': line.item_id.uom_id.id,
                })
            )
        values.update({
            'is_combo_package': self.is_combo_package,
            'combo_package_ids': combo_package_ids,
        })
        return values


class ProductProduct(models.Model):

    _inherit = 'product.product'

    is_combo_package = fields.Boolean('Combo Package')
    combo_package_ids = fields.One2many(comodel_name='product.combo.package.item', 
                                        inverse_name='product_id',
                                        string='Combo Package Items', 
                                        help='Combo Items included in this product.')
    
