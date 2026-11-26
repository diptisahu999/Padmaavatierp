# -*- coding: utf-8 -*-
import os
import base64
from odoo import models, fields, api


def format_inr(val):
    if val is None:
        return '0.00'
    val = float(val)
    is_neg = val < 0
    val = abs(val)
    parts = f'{val:.2f}'.split('.')
    integer_part = parts[0]
    decimal_part = parts[1]
    if len(integer_part) <= 3:
        res = integer_part
    else:
        last3 = integer_part[-3:]
        rest = integer_part[:-3]
        groups = []
        while len(rest) > 2:
            groups.insert(0, rest[-2:])
            rest = rest[:-2]
        if rest:
            groups.insert(0, rest)
        res = ','.join(groups) + ',' + last3
    formatted = f'{res}.{decimal_part}'
    return f'-{formatted}' if is_neg else formatted


def amount_to_indian_words(amount):
    if not amount:
        return 'Rupees Zero Only'
    amount = round(float(amount), 2)
    rupees = int(amount)
    paise = int(round((amount - rupees) * 100))

    def _three_digits(n):
        ones = ['', 'One', 'Two', 'Three', 'Four', 'Five', 'Six', 'Seven', 'Eight', 'Nine', 'Ten',
                'Eleven', 'Twelve', 'Thirteen', 'Fourteen', 'Fifteen', 'Sixteen', 'Seventeen', 'Eighteen', 'Nineteen']
        tens = ['', '', 'Twenty', 'Thirty', 'Forty', 'Fifty', 'Sixty', 'Seventy', 'Eighty', 'Ninety']
        res = []
        if n >= 100:
            res.append(ones[n // 100] + ' Hundred')
            n %= 100
        if n >= 20:
            res.append(tens[n // 10])
            n %= 10
        if n > 0:
            res.append(ones[n])
        return ' '.join(res)

    parts = []
    crores = rupees // 10000000
    rupees %= 10000000
    lakhs = rupees // 100000
    rupees %= 100000
    thousands = rupees // 1000
    rupees %= 1000
    hundreds = rupees

    if crores:
        parts.append(_three_digits(crores) + ' Crore')
    if lakhs:
        parts.append(_three_digits(lakhs) + ' Lakh')
    if thousands:
        parts.append(_three_digits(thousands) + ' Thousand')
    if hundreds:
        parts.append(_three_digits(hundreds))

    rupees_str = ' '.join(parts) if parts else 'Zero'
    res = f'Rupees {rupees_str}'
    if paise:
        res += f' and {_three_digits(paise)} Paise'
    res += ' Only'
    return res


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    lr_no = fields.Char(
        string='LR No.',
        copy=False,
        help='Lorry Receipt (LR) / Consignment / Tracking Number',
    )
    lr_date = fields.Date(
        string='LR Date',
        copy=False,
        help='Date of LR document',
    )
    terms_of_delivery = fields.Char(
        string='Terms of Delivery',
        copy=False,
        default='Ex-Works / Door Delivery',
        help='Terms of delivery e.g. Ex-Works / Door Delivery',
    )
    payment_terms_note = fields.Char(
        string='Payment Terms Note',
        default='100% Advance',
        copy=False,
        help='Payment terms note shown in details box (e.g. 100% Advance)',
    )
    cash_discount_percent = fields.Float(
        string='Cash Discount (%)',
        default=0.0,
        digits=(5, 2),
        help='Cash discount percentage applied after trade discount',
    )
    cash_discount_amount = fields.Monetary(
        string='Cash Discount (₹)',
        compute='_compute_cash_discount_amount',
        store=True,
        readonly=False,
        help='Cash discount amount',
    )
    freight_amount = fields.Monetary(
        string='Freight Amount',
        default=0.0,
        help='Freight / Shipping charges',
    )
    freight_tax_rate = fields.Float(
        string='Freight GST (%)',
        default=18.0,
        digits=(5, 2),
        help='Applicable GST rate on freight charges',
    )

    # Bank Details for document printing
    bank_name = fields.Char(
        string='Bank Name',
        default='State Bank of India',
        help='Bank name printed on documents',
    )
    bank_account_name = fields.Char(
        string='A/c Name',
        default='Padmaavati Engineers LLP',
        help='Account holder name printed on documents',
    )
    bank_account_no = fields.Char(
        string='A/c No.',
        default='1234567890123',
        help='Bank account number printed on documents',
    )
    bank_ifsc = fields.Char(
        string='IFSC Code',
        default='SBIN0001234',
        help='Bank IFSC code printed on documents',
    )
    bank_branch = fields.Char(
        string='Branch',
        default='Surat Main',
        help='Bank branch name printed on documents',
    )

    @api.depends('order_line.price_unit', 'order_line.product_uom_qty', 'order_line.discount', 'cash_discount_percent')
    def _compute_cash_discount_amount(self):
        for order in self:
            net_val = sum(
                (line.product_uom_qty or 0.0) * (line.price_unit or 0.0) * (1.0 - (line.discount or 0.0) / 100.0)
                for line in order.order_line if not line.display_type
            )
            if order.cash_discount_percent:
                order.cash_discount_amount = round(net_val * (order.cash_discount_percent / 100.0), 2)
            else:
                if not order.cash_discount_amount:
                    order.cash_discount_amount = 0.0

    def _get_report_gross_amount(self):
        self.ensure_one()
        return sum(
            (line.product_uom_qty or 0.0) * (line.price_unit or 0.0)
            for line in self.order_line if not line.display_type
        )

    def _get_report_trade_discount_amount(self):
        self.ensure_one()
        return sum(
            (line.product_uom_qty or 0.0) * (line.price_unit or 0.0) * ((line.discount or 0.0) / 100.0)
            for line in self.order_line if not line.display_type
        )

    def _get_report_net_after_trade_discount(self):
        self.ensure_one()
        return self._get_report_gross_amount() - self._get_report_trade_discount_amount()

    def _get_report_taxable_value(self):
        self.ensure_one()
        net = self._get_report_net_after_trade_discount()
        cash_disc = self.cash_discount_amount or 0.0
        freight = self.freight_amount or 0.0
        return round((net - cash_disc) + freight, 2)

    def _is_interstate_sale(self):
        self.ensure_one()
        company_state = self.company_id.state_id
        partner_state = self.partner_shipping_id.state_id or self.partner_id.state_id
        applied_taxes = self.order_line.mapped('tax_ids') if hasattr(self.order_line, 'tax_ids') else []
        if any('IGST' in (t.name or '').upper() for t in applied_taxes):
            return True
        if company_state and partner_state and company_state != partner_state:
            return True
        return False

    def _get_report_gst_summary(self):
        self.ensure_one()
        is_interstate = self._is_interstate_sale()
        order_lines = self.order_line.filtered(lambda l: not l.display_type)
        total_net = self._get_report_net_after_trade_discount()
        cash_disc = self.cash_discount_amount or 0.0
        freight = self.freight_amount or 0.0
        freight_tax_rate = self.freight_tax_rate or 0.0

        # Group lines by HSN Code and tax rate
        groups = {}
        for line in order_lines:
            hsn = line.hsn_code or line.product_id.hsn_code or '84484990'
            rate = line._get_line_tax_rate()
            key = (hsn, rate)
            if key not in groups:
                groups[key] = {
                    'hsn_code': hsn,
                    'tax_rate': rate,
                    'line_net': 0.0,
                    'taxable_value': 0.0,
                }
            gross = (line.product_uom_qty or 0.0) * (line.price_unit or 0.0)
            net_line = gross * (1.0 - (line.discount or 0.0) / 100.0)
            groups[key]['line_net'] += net_line

        # Allocate cash discount proportionally across HSN groups
        total_allocated_taxable = 0.0
        group_list = list(groups.values())
        for idx, g in enumerate(group_list):
            if total_net > 0:
                fraction = g['line_net'] / total_net
                g['taxable_value'] = round(g['line_net'] - (cash_disc * fraction), 2)
            else:
                g['taxable_value'] = round(g['line_net'], 2)
            total_allocated_taxable += g['taxable_value']

        # Include freight in taxable value
        if freight > 0:
            if group_list:
                # Add freight to the first group or group matching freight rate
                matched_g = next((g for g in group_list if abs(g['tax_rate'] - freight_tax_rate) < 0.01), group_list[0])
                matched_g['taxable_value'] = round(matched_g['taxable_value'] + freight, 2)
            else:
                group_list.append({
                    'hsn_code': '996511',
                    'tax_rate': freight_tax_rate,
                    'line_net': freight,
                    'taxable_value': freight,
                })

        # Calculate CGST, SGST, IGST per group
        total_taxable = 0.0
        total_cgst = 0.0
        total_sgst = 0.0
        total_igst = 0.0
        total_tax = 0.0

        summary_rows = []
        for g in group_list:
            taxable = g['taxable_value']
            rate = g['tax_rate']
            total_taxable += taxable

            if is_interstate:
                igst_rate = f"{rate:g}%"
                igst_amt = round(taxable * (rate / 100.0), 2)
                row_tax = igst_amt
                total_igst += igst_amt
                summary_rows.append({
                    'hsn_code': g['hsn_code'],
                    'taxable_value': taxable,
                    'taxable_value_fmt': format_inr(taxable),
                    'igst_rate': igst_rate,
                    'igst_amount': igst_amt,
                    'igst_amount_fmt': format_inr(igst_amt),
                    'total_tax': row_tax,
                    'total_tax_fmt': format_inr(row_tax),
                })
            else:
                half_rate = rate / 2.0
                cgst_rate = f"{half_rate:g}%"
                sgst_rate = f"{half_rate:g}%"
                row_tax = round(taxable * (rate / 100.0), 2)
                cgst_amt = round(row_tax / 2.0, 2)
                sgst_amt = round(row_tax - cgst_amt, 2)
                total_cgst += cgst_amt
                total_sgst += sgst_amt
                summary_rows.append({
                    'hsn_code': g['hsn_code'],
                    'taxable_value': taxable,
                    'taxable_value_fmt': format_inr(taxable),
                    'cgst_rate': cgst_rate,
                    'cgst_amount': cgst_amt,
                    'cgst_amount_fmt': format_inr(cgst_amt),
                    'sgst_rate': sgst_rate,
                    'sgst_amount': sgst_amt,
                    'sgst_amount_fmt': format_inr(sgst_amt),
                    'total_tax': row_tax,
                    'total_tax_fmt': format_inr(row_tax),
                })
            total_tax += row_tax

        grand_total = round(total_taxable + total_tax, 2)

        return {
            'is_interstate': is_interstate,
            'rows': summary_rows,
            'total_taxable': total_taxable,
            'total_taxable_fmt': format_inr(total_taxable),
            'total_cgst': total_cgst,
            'total_cgst_fmt': format_inr(total_cgst),
            'total_sgst': total_sgst,
            'total_sgst_fmt': format_inr(total_sgst),
            'total_igst': total_igst,
            'total_igst_fmt': format_inr(total_igst),
            'total_tax': total_tax,
            'total_tax_fmt': format_inr(total_tax),
            'grand_total': grand_total,
            'grand_total_fmt': format_inr(grand_total),
        }

    def _get_report_amount_in_words(self):
        self.ensure_one()
        summary = self._get_report_gst_summary()
        return amount_to_indian_words(summary['grand_total'])

    def _get_report_logo_src(self):
        self.ensure_one()
        if self.company_id.logo:
            logo_val = self.company_id.logo
            b64_str = logo_val.decode('utf-8') if isinstance(logo_val, bytes) else logo_val
            return f"data:image/png;base64,{b64_str}"

        static_logo = os.path.join(os.path.dirname(__file__), '..', 'static', 'src', 'img', 'logo.jpeg')
        if os.path.exists(static_logo):
            with open(static_logo, 'rb') as f:
                b64 = base64.b64encode(f.read()).decode('utf-8')
                return f"data:image/jpeg;base64,{b64}"

        fallback_logo = r"d:\Padmaavatierp\logo.jpeg"
        if os.path.exists(fallback_logo):
            with open(fallback_logo, 'rb') as f:
                b64 = base64.b64encode(f.read()).decode('utf-8')
                return f"data:image/jpeg;base64,{b64}"
        return ""

    def format_inr(self, val):
        return format_inr(val)


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
    hsn_code = fields.Char(
        string='HSN Code',
        related='product_id.hsn_code',
        readonly=False,
        store=True,
        help='Harmonized System Nomenclature (HSN) Code for GST',
    )

    def _get_line_tax_rate(self):
        self.ensure_one()
        if hasattr(self, 'tax_ids') and self.tax_ids:
            return sum(self.tax_ids.mapped('amount'))
        return 0.0

    def _get_line_taxable_value(self):
        self.ensure_one()
        gross = (self.product_uom_qty or 0.0) * (self.price_unit or 0.0)
        net_after_trade = gross * (1.0 - (self.discount or 0.0) / 100.0)
        order = self.order_id
        if order.cash_discount_percent:
            return round(net_after_trade * (1.0 - (order.cash_discount_percent / 100.0)), 2)
        elif order.cash_discount_amount:
            total_net = order._get_report_net_after_trade_discount()
            if total_net > 0:
                fraction = net_after_trade / total_net
                return round(net_after_trade - (order.cash_discount_amount * fraction), 2)
        return round(net_after_trade, 2)

    def _get_line_total_with_tax(self):
        self.ensure_one()
        taxable = self._get_line_taxable_value()
        rate = self._get_line_tax_rate()
        return round(taxable * (1.0 + rate / 100.0), 2)

    def format_inr(self, val):
        return format_inr(val)
