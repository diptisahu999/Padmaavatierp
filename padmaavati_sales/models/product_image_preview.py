# -*- coding: utf-8 -*-
from odoo import models, fields


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    product_image = fields.Image(
        string='Image',
        related='product_id.image_1920',
        readonly=True,
        help='High Definition Product Image with zoom preview',
    )


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    product_image = fields.Image(
        string='Image',
        related='product_id.image_1920',
        readonly=True,
        help='High Definition Product Image with zoom preview',
    )
