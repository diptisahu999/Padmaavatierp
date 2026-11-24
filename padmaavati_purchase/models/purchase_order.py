# -*- coding: utf-8 -*-
from odoo import models, fields, api


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    # --- TRANSPORTER DETAILS ---
    transporter_id = fields.Many2one(
        comodel_name='res.partner',
        string='Transporter',
        help='Transporter partner for E-Way Bill',
    )
    transport_id = fields.Many2one(
        comodel_name='padmaavati.transport',
        string='Transporter',
        help='Select registered transport carrier agency',
    )
    transport_name = fields.Char(
        string='Transport Name',
        compute='_compute_transport_details',
        store=True,
        readonly=False,
        help='Name of the transport carrier agency',
    )
    transporter_code = fields.Char(
        string='Transporter ID / GSTIN',
        compute='_compute_transport_details',
        store=True,
        readonly=False,
        help='Transporter GSTIN or Transporter ID for E-Way Bill',
    )

    # --- TRANSPORTATION DETAILS (PART B) ---
    transportation_mode = fields.Selection([
        ('1', 'By Road'),
        ('2', 'Rail'),
        ('3', 'Air'),
        ('4', 'Ship or Ship Cum Road/Rail'),
    ], string='Transportation Mode', default='1', copy=False, help='Mode of transport for E-Way Bill')

    vehicle_type = fields.Selection([
        ('R', 'Regular'),
        ('O', 'Over Dimensional Cargo'),
    ], string='Vehicle Type', default='R', copy=False, help='Vehicle type for E-Way Bill (Regular or Over Dimensional Cargo)')

    vehicle_no = fields.Char(
        string='Vehicle Number',
        copy=False,
        help='Vehicle registration number e.g. MH04 AB 1234',
    )
    tempo_no = fields.Char(
        string='Tempo / Vehicle No.',
        compute='_compute_vehicle_details',
        store=True,
        readonly=False,
        help='Vehicle / Tempo registration number',
    )
    transport_vehicle_id = fields.Many2one(
        comodel_name='padmaavati.transport.vehicle',
        string='Registered Vehicle / Tempo',
        domain="[('transport_id', '=', transport_id)] if transport_id else []",
        help='Select vehicle / tempo associated with this transport agency',
    )
    vehicle_name = fields.Char(
        string='Vehicle Model',
        compute='_compute_vehicle_details',
        store=True,
        readonly=False,
        help='Vehicle model e.g. Tata Ace, Bolero Pickup, Eicher 17ft',
    )
    distance = fields.Integer(
        string='Distance (km)',
        copy=False,
        help='Distance in kilometers for E-Way Bill calculation',
    )

    # --- CONSIGNMENT & LR DETAILS ---
    lr_no = fields.Char(
        string='LR No.',
        copy=False,
        help='Lorry Receipt (LR) / Bilty / Consignment tracking number.',
    )
    lr_date = fields.Date(
        string='LR Date',
        copy=False,
        help='Date of LR / Bilty / Consignment document.',
    )
    transportation_doc_no = fields.Char(
        string='Transporter Doc No.',
        compute='_compute_doc_details',
        store=True,
        readonly=False,
        help='Transporter document number for E-Way Bill (same as LR No.)',
    )
    transportation_doc_date = fields.Date(
        string='Transporter Doc Date',
        compute='_compute_doc_details',
        store=True,
        readonly=False,
        help='Transporter document date for E-Way Bill (same as LR Date)',
    )
    parcel_qty = fields.Integer(
        string='Parcel Qty',
        copy=False,
        help='Total number of parcels / boxes received.',
    )
    lr_amount = fields.Monetary(
        string='LR Amount',
        currency_field='currency_id',
        copy=False,
        help='LR freight amount. Strictly informational; does not affect invoice totals or accounting.',
    )

    # --- DRIVER DETAILS ---
    driver_name = fields.Char(
        string='Driver Name',
        compute='_compute_vehicle_details',
        store=True,
        readonly=False,
    )
    driver_phone = fields.Char(
        string='Driver Phone',
        compute='_compute_vehicle_details',
        store=True,
        readonly=False,
    )

    # -------------------------------------------------------------
    # COMPUTES & ONCHANGES
    # -------------------------------------------------------------

    @api.depends('transporter_id', 'transport_id')
    def _compute_transport_details(self):
        for order in self:
            if order.transporter_id:
                if not order.transport_name:
                    order.transport_name = order.transporter_id.name
                if not order.transporter_code and order.transporter_id.vat:
                    order.transporter_code = order.transporter_id.vat
            elif order.transport_id:
                if not order.transport_name:
                    order.transport_name = order.transport_id.name
                if not order.transporter_code and order.transport_id.code:
                    order.transporter_code = order.transport_id.code

    @api.onchange('transporter_id')
    def _onchange_transporter_id(self):
        if self.transporter_id:
            self.transport_name = self.transporter_id.name
            if self.transporter_id.vat:
                self.transporter_code = self.transporter_id.vat

    @api.onchange('transport_id')
    def _onchange_transport_id(self):
        if self.transport_id:
            self.transport_name = self.transport_id.name
            if self.transport_id.code:
                self.transporter_code = self.transport_id.code
            if self.transport_id.partner_id:
                self.transporter_id = self.transport_id.partner_id
            if self.transport_vehicle_id and self.transport_vehicle_id.transport_id != self.transport_id:
                self.transport_vehicle_id = False
        else:
            self.transport_vehicle_id = False

    @api.depends('transport_vehicle_id', 'vehicle_no')
    def _compute_vehicle_details(self):
        for order in self:
            if order.transport_vehicle_id:
                veh = order.transport_vehicle_id
                order.vehicle_no = veh.vehicle_no
                order.tempo_no = veh.vehicle_no
                order.vehicle_name = veh.name
                order.driver_name = veh.driver_name
                order.driver_phone = veh.driver_phone
                if veh.ewaybill_vehicle_type:
                    order.vehicle_type = veh.ewaybill_vehicle_type
                if veh.transport_id and not order.transport_id:
                    order.transport_id = veh.transport_id
            elif order.vehicle_no:
                order.tempo_no = order.vehicle_no

    @api.onchange('transport_vehicle_id')
    def _onchange_transport_vehicle_id(self):
        if self.transport_vehicle_id:
            veh = self.transport_vehicle_id
            self.vehicle_no = veh.vehicle_no
            self.tempo_no = veh.vehicle_no
            self.vehicle_name = veh.name
            self.driver_name = veh.driver_name
            self.driver_phone = veh.driver_phone
            if veh.ewaybill_vehicle_type:
                self.vehicle_type = veh.ewaybill_vehicle_type
            if veh.transport_id:
                if not self.transport_id:
                    self.transport_id = veh.transport_id
                if not self.transport_name:
                    self.transport_name = veh.transport_id.name
                if veh.transport_id.code and not self.transporter_code:
                    self.transporter_code = veh.transport_id.code
                if veh.transport_id.partner_id and not self.transporter_id:
                    self.transporter_id = veh.transport_id.partner_id

    @api.onchange('vehicle_no')
    def _onchange_vehicle_no(self):
        if self.vehicle_no:
            self.tempo_no = self.vehicle_no

    @api.onchange('tempo_no')
    def _onchange_tempo_no(self):
        if self.tempo_no and not self.vehicle_no:
            self.vehicle_no = self.tempo_no

    @api.depends('lr_no', 'lr_date')
    def _compute_doc_details(self):
        for order in self:
            if order.lr_no and not order.transportation_doc_no:
                order.transportation_doc_no = order.lr_no
            if order.lr_date and not order.transportation_doc_date:
                order.transportation_doc_date = order.lr_date

    @api.onchange('lr_no')
    def _onchange_lr_no(self):
        if self.lr_no:
            self.transportation_doc_no = self.lr_no

    @api.onchange('lr_date')
    def _onchange_lr_date(self):
        if self.lr_date:
            self.transportation_doc_date = self.lr_date

    # -------------------------------------------------------------
    # INVOICE / BILL PREPARATION
    # -------------------------------------------------------------
    def _prepare_invoice(self):
        """Pass full transport & E-Way Bill details from Purchase Order to Vendor Bill"""
        invoice_vals = super(PurchaseOrder, self)._prepare_invoice()
        invoice_vals.update({
            'transporter_id': self.transporter_id.id if self.transporter_id else False,
            'transport_id': self.transport_id.id if self.transport_id else False,
            'transport_name': self.transport_name,
            'transporter_code': self.transporter_code,
            'transportation_mode': self.transportation_mode or '1',
            'vehicle_type': self.vehicle_type or 'R',
            'vehicle_no': self.vehicle_no or self.tempo_no,
            'tempo_no': self.tempo_no or self.vehicle_no,
            'transport_vehicle_id': self.transport_vehicle_id.id if self.transport_vehicle_id else False,
            'vehicle_name': self.vehicle_name,
            'distance': self.distance,
            'lr_no': self.lr_no,
            'lr_date': self.lr_date,
            'transportation_doc_no': self.transportation_doc_no or self.lr_no,
            'transportation_doc_date': self.transportation_doc_date or self.lr_date,
            'parcel_qty': self.parcel_qty,
            'lr_amount': self.lr_amount,
            'driver_name': self.driver_name,
            'driver_phone': self.driver_phone,
        })
        return invoice_vals
