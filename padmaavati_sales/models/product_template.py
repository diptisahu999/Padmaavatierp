# -*- coding: utf-8 -*-
from odoo import models, fields


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    sap_code = fields.Char(
        string='SAP Code',
        copy=False,
        index=True,
        help='SAP Material / Item Code',
    )
    part_number = fields.Char(
        string='Part No.',
        copy=False,
        index=True,
        help='Manufacturer or Customer Part Number',
    )
    hsn_code = fields.Char(
        string='HSN Code',
        copy=False,
        index=True,
        help='Harmonized System Nomenclature (HSN) Code for GST',
    )


class ProductProduct(models.Model):
    _inherit = 'product.product'

    sap_code = fields.Char(
        string='SAP Code',
        related='product_tmpl_id.sap_code',
        readonly=False,
        store=True,
        help='SAP Material / Item Code',
    )
    part_number = fields.Char(
        string='Part No.',
        related='product_tmpl_id.part_number',
        readonly=False,
        store=True,
        help='Manufacturer or Customer Part Number',
    )
    hsn_code = fields.Char(
        string='HSN Code',
        related='product_tmpl_id.hsn_code',
        readonly=False,
        store=True,
        help='Harmonized System Nomenclature (HSN) Code for GST',
    )
