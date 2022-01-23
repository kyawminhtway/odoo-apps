# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name' : 'Product Combo Package',
    'version' : '1.0',
    'summary': 'Combo package product in Sales & Poin of Sale',
    'sequence': 10,
    'description': """
    
    """,
    'category': 'Sales',
    'images' : [],
    'depends' : ['sale'],
    'data': [
        'security/res_groups.xml',
        'security/ir.model.access.csv',
        'views/product_views.xml',
        'views/product_combo_package_views.xml',
        'wizards/stock_insufficient_warning_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    # 'assets': {
    #     'web.assets_backend': [
    #         'account/static/src/js/account_selection.js',
    #     ],
    #     'web.assets_qweb': [
    #         'account/static/src/xml/**/*',
    #     ],
    # },
    'license': 'LGPL-3',
}
