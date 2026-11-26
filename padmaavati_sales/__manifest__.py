# -*- coding: utf-8 -*-
{
    'name': 'Padmaavati Custom Sales',
    'version': '19.0.1.0.0',
    'category': 'Sales',
    'summary': 'Custom Sales, Quotations, and Invoicing Enhancements for Padmaavati ERP',
    'author': 'Techvizor',
    'depends': [
        'sale_management',
        'account',
        'stock',
    ],
    'data': [
        'security/ir.model.access.csv',
        'report/sale_report_templates.xml',
        'report/ir_actions_report.xml',
        'views/product_views.xml',
        'views/sale_order_views.xml',
        'views/account_move_views.xml',
        'views/product_image_views.xml',
        'views/sale_order_weight_views.xml',
        'views/sale_order_rates_views.xml',
        'views/product_rate_history_wizard_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
