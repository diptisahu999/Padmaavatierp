# -*- coding: utf-8 -*-
from odoo import models, fields


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    sap_code = fields.Char(
        string='SAP Code',
        related='product_id.sap_code',
        readonly=True,
        store=True,
        help='SAP Code from Product',
    )
    part_number = fields.Char(
        string='Part No.',
        related='product_id.part_number',
        readonly=True,
        store=True,
        help='Part Number from Product',
    )
