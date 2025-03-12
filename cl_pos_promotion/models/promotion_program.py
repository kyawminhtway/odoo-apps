from datetime import datetime
from odoo import api, models, fields


class PromotionProgram(models.Model):

    _name = 'promotion.program'
    _inherit = ['mail.thread']
    _description = 'Promotion Program'

    name = fields.Char('Name', required=True, tracking=1)
    active = fields.Boolean('Active', default=True, tracking=2)
    date_from = fields.Date('Date From', tracking=3)
    date_to = fields.Date('Date To', tracking=4)
    rule_id = fields.Many2one('promotion.rule', 'Rule', required=True, tracking=5)
    item_id = fields.Many2one('promotion.item', 'Item', required=True, tracking=6)
    item_type = fields.Selection(related='item_id.type', string='Item Type')
    can_be_merged = fields.Boolean('Can be merged with other Discounts', tracking=7)
    config_ids = fields.Many2many('pos.config', 'promotion_program_config_rel', 'program_id', 'config_id', 'Available Shops')
    partner_ids = fields.Many2many('res.partner', 'promotion_program_partner_rel', 'program_id', 'partner_id', 'Customers')
    note = fields.Text('Note')

    @api.model
    def _load_pos_data_domain(self, data):
        current = fields.Date.context_today(self)
        return [
            '|',
            ('config_ids', '=', False),
            ('config_ids', 'in', [data['pos.config']['data'][0]['id']]),
            '|',
            '|',
            '|',
            '&',
            ('date_from', '=', False),
            ('date_to', '>=', current),
            '&',
            ('date_from', '<=', current),
            ('date_to', '=', False),
            '&',
            ('date_from', '<=', current),
            ('date_to', '>=', current),
            '&',
            ('date_from', '=', False),
            ('date_to', '=', False)
        ]

    @api.model
    def _load_pos_data_fields(self):
        return [
            'name', 'active', 'date_from', 'date_to', 'rule_id', 'item_id', 
            'can_be_merged', 'config_ids', 'partner_ids', 'note',
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
    
