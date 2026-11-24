# -*- coding: utf-8 -*-
from odoo import models, fields, _
from odoo.exceptions import UserError


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    purchase_price = fields.Float(
        string='Purchase Rate',
        digits='Product Price',
        copy=False,
        help='Purchase rate / cost price of the product',
    )

    def action_open_rate_history(self):
        self.ensure_one()
        if not self.product_id:
            raise UserError(_("Please select a product first to view its rate history."))

        # Pre-create the transient wizard in the database so it has a real ID
        wizard = self.env['product.rate.history.wizard'].create({
            'product_id': self.product_id.id,
            'sale_line_id': self.id,
        })
        wizard._populate_history()

        return {
            'name': _("Price & Rate History - %s") % self.product_id.display_name,
            'type': 'ir.actions.act_window',
            'res_model': 'product.rate.history.wizard',
            'res_id': wizard.id,
            'view_mode': 'form',
            'target': 'new',
        }


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    purchase_price = fields.Float(
        string='Purchase Rate',
        digits='Product Price',
        copy=False,
        help='Purchase rate / cost price of the product',
    )

    def action_open_rate_history(self):
        self.ensure_one()
        if not self.product_id:
            raise UserError(_("Please select a product first to view its rate history."))

        # Pre-create the transient wizard in the database so it has a real ID
        wizard = self.env['product.rate.history.wizard'].create({
            'product_id': self.product_id.id,
            'invoice_line_id': self.id,
        })
        wizard._populate_history()

        return {
            'name': _("Price & Rate History - %s") % self.product_id.display_name,
            'type': 'ir.actions.act_window',
            'res_model': 'product.rate.history.wizard',
            'res_id': wizard.id,
            'view_mode': 'form',
            'target': 'new',
        }
