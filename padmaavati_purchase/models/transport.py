# -*- coding: utf-8 -*-
from odoo import models, fields, api


class PadmaavatiTransport(models.Model):
    _name = 'padmaavati.transport'
    _description = 'Transport Agency / Carrier Master'
    _order = 'name'

    name = fields.Char(string='Transport Name', required=True, index=True)
    code = fields.Char(string='Transporter ID / Code', help='Transporter ID / GSTIN for E-Way Bill')
    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Transporter (Partner)',
        help='Linked contact or vendor for GST E-Way Bill',
    )
    phone = fields.Char(string='Contact Number')
    email = fields.Char(string='Email')
    contact_person = fields.Char(string='Contact Person')
    address = fields.Text(string='Address')
    vehicle_ids = fields.One2many(
        comodel_name='padmaavati.transport.vehicle',
        inverse_name='transport_id',
        string='Vehicles / Tempos',
    )
    vehicle_count = fields.Integer(string='Vehicles Count', compute='_compute_vehicle_count')
    active = fields.Boolean(default=True)

    @api.depends('vehicle_ids')
    def _compute_vehicle_count(self):
        for record in self:
            record.vehicle_count = len(record.vehicle_ids)

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        if self.partner_id:
            if not self.name:
                self.name = self.partner_id.name
            if not self.phone:
                self.phone = self.partner_id.phone or self.partner_id.mobile
            if not self.email:
                self.email = self.partner_id.email
            if not self.code and self.partner_id.vat:
                self.code = self.partner_id.vat


class PadmaavatiTransportVehicle(models.Model):
    _name = 'padmaavati.transport.vehicle'
    _description = 'Transport Vehicle / Tempo Master'
    _order = 'vehicle_no'
    _rec_name = 'display_name'

    vehicle_no = fields.Char(
        string='Vehicle / Tempo No.',
        required=True,
        index=True,
        help='Vehicle registration number e.g. MH04 AB 1234',
    )
    name = fields.Char(
        string='Vehicle Name / Model',
        help='e.g. Tata Ace, Bolero Pickup, Eicher 17ft, BharatBenz',
    )
    transport_id = fields.Many2one(
        comodel_name='padmaavati.transport',
        string='Transport / Carrier',
        ondelete='cascade',
        index=True,
    )
    ewaybill_vehicle_type = fields.Selection([
        ('R', 'Regular'),
        ('O', 'Over Dimensional Cargo'),
    ], string='Vehicle Type (E-Way Bill)', default='R', help='E-Way Bill Vehicle Type')
    vehicle_type = fields.Selection([
        ('tempo', 'Tempo / Small LCV'),
        ('pickup', 'Pickup Van'),
        ('truck', 'Truck / Heavy LCV'),
        ('trailer', 'Trailer'),
        ('other', 'Other'),
    ], string='Fleet Category', default='tempo')
    driver_name = fields.Char(string='Driver Name')
    driver_phone = fields.Char(string='Driver Phone / Mobile')
    notes = fields.Text(string='Notes')
    active = fields.Boolean(default=True)
    display_name = fields.Char(string='Display Name', compute='_compute_display_name', store=True)

    @api.depends('vehicle_no', 'name', 'transport_id.name')
    def _compute_display_name(self):
        for rec in self:
            parts = [rec.vehicle_no] if rec.vehicle_no else []
            if rec.name:
                parts.append(rec.name)
            if rec.transport_id:
                parts.append(f"({rec.transport_id.name})")
            rec.display_name = " - ".join(parts) if parts else "Vehicle"
