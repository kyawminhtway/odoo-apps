from odoo import api, models, fields


class PromotionItem(models.Model):
 
    _name = 'promotion.item'
    _inherit = ['mail.thread']
    _description = 'Promotion Item'

    name = fields.Char('Name', required=True, tracking=1)
    type = fields.Selection([('fixed_discount', 'Fixed Discount'),
                             ('percent_discount', 'Percent Discount'),
                             ('free_product', 'Free Products')], 'Type', required=True, tracking=2)
    discount_rule = fields.Selection([('order', 'Whole Order'),
                                      ('category', 'Specific Categories'),
                                      ('product', 'Specific Products')], 'Discount Rule', tracking=3)
    price_rule = fields.Selection([('tax_exclusive', 'Price without Tax'),
                                   ('tax_inclusive', 'Price with Tax'),
                                   ('discount_inclusive', 'Price with Tax & Discount')], 'Price Calculation', tracking=4)
    discount = fields.Float('Discount', tracking=5)
    product_id = fields.Many2one('product.product', 'Product', domain=[('type', '=', 'service')], tracking=6)
    product_ids = fields.Many2many('product.product', 'promotion_item_product_rel', 'item_id', 'product_id', 'Products', domain=[('available_in_pos', '=', True)])
    category_ids = fields.Many2many('pos.category', 'promotion_item_category_rel', 'item_id', 'category_id', 'Categories')
    item_rule = fields.Selection([('every_occurrence', 'Every Occurrence'),
                                  ('max_occurrence', 'Max Occurrence')], 'Item Rule', tracking=7)
    max_occurrence = fields.Float('Max Occurrence', default=1, tracking=8)
    max_discount = fields.Float('Max Discount', tracking=9)
    free_product_ids = fields.One2many('promotion.free.product', 'item_id', 'Free Products')
    note = fields.Text('Note')
    program_ids = fields.One2many('promotion.program', 'item_id', 'Promotion Programs')

    @api.model
    def _load_pos_data_domain(self, data):
        return [('program_ids', 'in', data['promotion.program']['ids'])]

    @api.model
    def _load_pos_data_fields(self):
        return [
            'name', 'type', 'discount_rule', 'price_rule', 'discount', 'product_id', 'product_ids', 'category_ids', 
            'item_rule', 'max_occurrence', 'max_discount', 'free_product_ids', 'note', 'program_ids',
        ]

    def _load_pos_data(self, data):
        domain = self._load_pos_data_domain(data)
        fields_to_read = self._load_pos_data_fields()
        records = self.search_read(domain, fields_to_read, load=False)
        return {
            'data': records,
            'fields': fields_to_read,
            'ids': [record['id'] for record in records]
        }


class PromotionFreeProduct(models.Model):

    _name = 'promotion.free.product'
    _description = 'Promotion Free Product'

    product_id = fields.Many2one('product.product', 'Product', domain=[('available_in_pos', '=', True)], required=True)
    qty = fields.Float('Quantity', required=True, default=1)
    item_id = fields.Many2one('promotion.item', 'Item', ondelete='cascade')

    @api.model
    def _load_pos_data_domain(self, data):
        return [('item_id', 'in', data['promotion.item']['ids'])]

    @api.model
    def _load_pos_data_fields(self):
        return [
            'product_id', 'qty', 'item_id'
        ]

    def _load_pos_data(self, data):
        domain = self._load_pos_data_domain(data)
        fields_to_read = self._load_pos_data_fields()
        records = self.search_read(domain, fields_to_read, load=False)
        return {
            'data': records,
            'fields': fields_to_read
        }

