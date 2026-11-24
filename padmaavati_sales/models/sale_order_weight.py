# -*- coding: utf-8 -*-
from odoo import models, fields, api


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    total_weight = fields.Float(
        string='Total Order Weight',
        compute='_compute_total_weight',
        store=True,
        digits='Stock Weight',
        help='Total weight of all order lines',
    )
    weight_uom_name = fields.Char(
        string='Weight UoM',
        compute='_compute_weight_uom_name',
    )

    def _compute_weight_uom_name(self):
        weight_uom = self.env['product.template']._get_weight_uom_name_from_ir_config_parameter()
        for order in self:
            order.weight_uom_name = weight_uom

    @api.depends('order_line.total_weight')
    def _compute_total_weight(self):
        for order in self:
            order.total_weight = sum(order.order_line.mapped('total_weight'))


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    weight_per_nos = fields.Float(
        string='Weight / Nos',
        compute='_compute_weight_per_nos',
        store=True,
        readonly=False,
        digits='Stock Weight',
        help='Weight per nos / unit (pulled from product, can be adjusted)',
    )
    total_weight = fields.Float(
        string='Total Weight',
        compute='_compute_total_weight',
        store=True,
        digits='Stock Weight',
        help='Total weight for this line (Quantity * Weight / Nos)',
    )
    weight_uom_name = fields.Char(
        string='Weight UoM',
        related='order_id.weight_uom_name',
    )

    @api.depends('product_id')
    def _compute_weight_per_nos(self):
        for line in self:
            if line.product_id:
                line.weight_per_nos = line.product_id.weight
            else:
                line.weight_per_nos = 0.0

    @api.depends('product_uom_qty', 'weight_per_nos')
    def _compute_total_weight(self):
        for line in self:
            line.total_weight = (line.product_uom_qty or 0.0) * (line.weight_per_nos or 0.0)


class AccountMove(models.Model):
    _inherit = 'account.move'

    total_weight = fields.Float(
        string='Total Invoice Weight',
        compute='_compute_total_weight',
        store=True,
        digits='Stock Weight',
        help='Total weight of all invoice lines',
    )
    weight_uom_name = fields.Char(
        string='Weight UoM',
        compute='_compute_weight_uom_name',
    )

    def _compute_weight_uom_name(self):
        weight_uom = self.env['product.template']._get_weight_uom_name_from_ir_config_parameter()
        for move in self:
            move.weight_uom_name = weight_uom

    @api.depends('invoice_line_ids.total_weight')
    def _compute_total_weight(self):
        for move in self:
            move.total_weight = sum(move.invoice_line_ids.mapped('total_weight'))


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    weight_per_nos = fields.Float(
        string='Weight / Nos',
        compute='_compute_weight_per_nos',
        store=True,
        readonly=False,
        digits='Stock Weight',
        help='Weight per nos / unit (pulled from product, can be adjusted)',
    )
    total_weight = fields.Float(
        string='Total Weight',
        compute='_compute_total_weight',
        store=True,
        digits='Stock Weight',
        help='Total weight for this line (Quantity * Weight / Nos)',
    )
    weight_uom_name = fields.Char(
        string='Weight UoM',
        related='move_id.weight_uom_name',
    )

    @api.depends('product_id')
    def _compute_weight_per_nos(self):
        for line in self:
            if line.product_id:
                line.weight_per_nos = line.product_id.weight
            else:
                line.weight_per_nos = 0.0

    @api.depends('quantity', 'weight_per_nos')
    def _compute_total_weight(self):
        for line in self:
            line.total_weight = (line.quantity or 0.0) * (line.weight_per_nos or 0.0)
