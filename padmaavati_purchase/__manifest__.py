# -*- coding: utf-8 -*-
{
    'name': 'Padmaavati Purchase',
    'version': '19.0.1.0.0',
    'category': 'Purchase',
    'summary': 'Custom Transport, Logistics & E-Way Bill details for Purchase Entries and Vendor Bills',
    'description': """
Padmaavati Purchase Logistics & E-Way Bill Enhancements
=======================================================
Adds Transport and E-Way Bill Part B logistics for Purchase Orders & Vendor Bills:
* Transport Agency Master (padmaavati.transport)
* Vehicle & Tempo Master (padmaavati.transport.vehicle)
* Transporter Partner & Agency selection
* Transportation Mode (Road, Rail, Air, Ship)
* Vehicle Type (Regular, Over Dimensional Cargo)
* Vehicle Number & Model
* LR No., LR Date, Parcel Qty
* Distance (km)
* LR Amount (Strictly informational - isolated from accounting ledgers and bill totals)
* Auto-sync to Odoo Indian E-Way Bill (l10n.in.ewaybill)
    """,
    'author': 'Techvizor',
    'depends': [
        'purchase',
        'account',
        'l10n_in_ewaybill',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/transport_views.xml',
        'views/purchase_order_views.xml',
        'views/account_move_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
