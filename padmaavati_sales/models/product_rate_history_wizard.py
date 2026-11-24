# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class ProductRateHistoryWizard(models.TransientModel):
    _name = 'product.rate.history.wizard'
    _description = 'Product Sale and Purchase Rate History Wizard'

    product_id = fields.Many2one('product.product', string='Product', required=True, readonly=True)
    product_tmpl_id = fields.Many2one('product.template', string='Product Template', related='product_id.product_tmpl_id', readonly=True)
    sap_code = fields.Char(string='SAP Code', related='product_id.sap_code', readonly=True)
    part_number = fields.Char(string='Part No.', related='product_id.part_number', readonly=True)
    current_cost = fields.Float(string='Current Standard Cost', related='product_id.standard_price', readonly=True)
    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.company.currency_id, readonly=True)

    sale_line_id = fields.Many2one('sale.order.line', string='Origin Sale Order Line', readonly=True)
    invoice_line_id = fields.Many2one('account.move.line', string='Origin Invoice Line', readonly=True)

    sale_history_ids = fields.One2many('product.rate.history.sale.line', 'wizard_id', string='Previous Sales')
    purchase_history_ids = fields.One2many('product.rate.history.purchase.line', 'wizard_id', string='Previous Purchases')

    def _populate_history(self):
        self.ensure_one()
        product = self.product_id
        if not product:
            return

        SaleLineModel = self.env['product.rate.history.sale.line']
        PurchaseLineModel = self.env['product.rate.history.purchase.line']

        # 1. Gather Previous Sales History
        domain_so = [
            ('product_id', '=', product.id),
            ('order_id.state', 'in', ['sale', 'done']),
        ]
        if self.sale_line_id:
            domain_so.append(('id', '!=', self.sale_line_id.id))

        sale_orders = self.env['sale.order.line'].search(domain_so, order='create_date desc', limit=20)
        for sol in sale_orders:
            order_date = sol.order_id.date_order.date() if sol.order_id.date_order else sol.create_date.date()
            state_label = dict(sol.order_id._fields['state'].selection).get(sol.order_id.state, sol.order_id.state)
            SaleLineModel.create({
                'wizard_id': self.id,
                'order_date': order_date,
                'partner_id': sol.order_id.partner_id.id,
                'doc_ref': sol.order_id.name,
                'qty': sol.product_uom_qty,
                'unit_price': sol.price_unit,
                'currency_id': sol.currency_id.id,
                'status': state_label,
            })

        # Customer Invoices (Posted)
        domain_inv = [
            ('product_id', '=', product.id),
            ('move_id.move_type', '=', 'out_invoice'),
            ('move_id.state', '=', 'posted'),
        ]
        inv_lines = self.env['account.move.line'].search(domain_inv, order='date desc, id desc', limit=20)
        for invl in inv_lines:
            SaleLineModel.create({
                'wizard_id': self.id,
                'order_date': invl.move_id.invoice_date or invl.date,
                'partner_id': invl.move_id.partner_id.id,
                'doc_ref': invl.move_id.name,
                'qty': invl.quantity,
                'unit_price': invl.price_unit,
                'currency_id': invl.currency_id.id,
                'status': 'Invoiced',
            })

        # 2. Gather Previous Purchases History
        # From Vendor Bills (Posted)
        domain_bills = [
            ('product_id', '=', product.id),
            ('move_id.move_type', '=', 'in_invoice'),
            ('move_id.state', '=', 'posted'),
        ]
        bill_lines = self.env['account.move.line'].search(domain_bills, order='date desc, id desc', limit=20)
        for bl in bill_lines:
            PurchaseLineModel.create({
                'wizard_id': self.id,
                'order_date': bl.move_id.invoice_date or bl.date,
                'partner_id': bl.move_id.partner_id.id,
                'doc_ref': bl.move_id.name,
                'qty': bl.quantity,
                'unit_price': bl.price_unit,
                'currency_id': bl.currency_id.id,
                'status': 'Billed',
            })

        # If purchase.order.line model is available
        if 'purchase.order.line' in self.env:
            po_lines = self.env['purchase.order.line'].search([
                ('product_id', '=', product.id),
                ('order_id.state', 'in', ['purchase', 'done']),
            ], order='create_date desc', limit=20)
            for pol in po_lines:
                order_date = pol.order_id.date_approve.date() if pol.order_id.date_approve else pol.create_date.date()
                state_label = dict(pol.order_id._fields['state'].selection).get(pol.order_id.state, pol.order_id.state)
                PurchaseLineModel.create({
                    'wizard_id': self.id,
                    'order_date': order_date,
                    'partner_id': pol.order_id.partner_id.id,
                    'doc_ref': pol.order_id.name,
                    'qty': pol.product_qty,
                    'unit_price': pol.price_unit,
                    'currency_id': pol.currency_id.id,
                    'status': state_label,
                })

        # Also include Vendor Pricelists
        for seller in product.seller_ids:
            PurchaseLineModel.create({
                'wizard_id': self.id,
                'order_date': seller.date_start or fields.Date.today(),
                'partner_id': seller.partner_id.id,
                'doc_ref': _('Vendor Pricelist (Min Qty: %s)') % seller.min_qty,
                'qty': seller.min_qty,
                'unit_price': seller.price,
                'currency_id': seller.currency_id.id,
                'status': _('Supplier Price'),
            })


class ProductRateHistorySaleLine(models.TransientModel):
    _name = 'product.rate.history.sale.line'
    _description = 'Rate History Sale Line'
    _order = 'order_date desc'

    wizard_id = fields.Many2one('product.rate.history.wizard', ondelete='cascade')
    order_date = fields.Date(string='Date')
    partner_id = fields.Many2one('res.partner', string='Customer')
    doc_ref = fields.Char(string='Document')
    qty = fields.Float(string='Quantity')
    unit_price = fields.Float(string='Sell Rate', digits='Product Price')
    currency_id = fields.Many2one('res.currency', string='Currency')
    status = fields.Char(string='Status')

    def action_apply_rate(self):
        self.ensure_one()
        wizard = self.wizard_id
        if wizard.sale_line_id:
            wizard.sale_line_id.write({'price_unit': self.unit_price})
        elif wizard.invoice_line_id:
            wizard.invoice_line_id.write({'price_unit': self.unit_price})
        return {'type': 'ir.actions.act_window_close'}


class ProductRateHistoryPurchaseLine(models.TransientModel):
    _name = 'product.rate.history.purchase.line'
    _description = 'Rate History Purchase Line'
    _order = 'order_date desc'

    wizard_id = fields.Many2one('product.rate.history.wizard', ondelete='cascade')
    order_date = fields.Date(string='Date')
    partner_id = fields.Many2one('res.partner', string='Vendor')
    doc_ref = fields.Char(string='Document')
    qty = fields.Float(string='Quantity')
    unit_price = fields.Float(string='Purchase Rate', digits='Product Price')
    currency_id = fields.Many2one('res.currency', string='Currency')
    status = fields.Char(string='Status')

    def action_apply_rate(self):
        self.ensure_one()
        wizard = self.wizard_id
        if wizard.sale_line_id:
            wizard.sale_line_id.write({'price_unit': self.unit_price})
        elif wizard.invoice_line_id:
            wizard.invoice_line_id.write({'price_unit': self.unit_price})
        return {'type': 'ir.actions.act_window_close'}
