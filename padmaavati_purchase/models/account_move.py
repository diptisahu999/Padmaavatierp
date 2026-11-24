# -*- coding: utf-8 -*-
from odoo import models, fields, api


class AccountMove(models.Model):
    _inherit = 'account.move'

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
        for move in self:
            if move.transporter_id:
                if not move.transport_name:
                    move.transport_name = move.transporter_id.name
                if not move.transporter_code and move.transporter_id.vat:
                    move.transporter_code = move.transporter_id.vat
            elif move.transport_id:
                if not move.transport_name:
                    move.transport_name = move.transport_id.name
                if not move.transporter_code and move.transport_id.code:
                    move.transporter_code = move.transport_id.code

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
        for move in self:
            if move.transport_vehicle_id:
                veh = move.transport_vehicle_id
                move.vehicle_no = veh.vehicle_no
                move.tempo_no = veh.vehicle_no
                move.vehicle_name = veh.name
                move.driver_name = veh.driver_name
                move.driver_phone = veh.driver_phone
                if veh.ewaybill_vehicle_type:
                    move.vehicle_type = veh.ewaybill_vehicle_type
                if veh.transport_id and not move.transport_id:
                    move.transport_id = veh.transport_id
            elif move.vehicle_no:
                move.tempo_no = move.vehicle_no

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
        for move in self:
            if move.lr_no and not move.transportation_doc_no:
                move.transportation_doc_no = move.lr_no
            if move.lr_date and not move.transportation_doc_date:
                move.transportation_doc_date = move.lr_date

    @api.onchange('lr_no')
    def _onchange_lr_no(self):
        if self.lr_no:
            self.transportation_doc_no = self.lr_no

    @api.onchange('lr_date')
    def _onchange_lr_date(self):
        if self.lr_date:
            self.transportation_doc_date = self.lr_date

    # -------------------------------------------------------------
    # E-WAY BILL ACTION OVERRIDE
    # -------------------------------------------------------------
    def action_l10n_in_ewaybill_create(self):
        """Pass transport & vehicle details to Odoo Indian E-Way Bill wizard"""
        action = super().action_l10n_in_ewaybill_create()
        if isinstance(action, dict) and 'context' in action:
            ctx = dict(action['context'])
            partner_transporter = self.transporter_id.id if self.transporter_id else (
                self.transport_id.partner_id.id if self.transport_id and self.transport_id.partner_id else False
            )
            ctx.update({
                'default_transporter_id': partner_transporter,
                'default_mode': self.transportation_mode or '1',
                'default_vehicle_type': self.vehicle_type or 'R',
                'default_vehicle_no': self.vehicle_no or self.tempo_no or False,
                'default_distance': self.distance or 0,
                'default_transportation_doc_no': self.lr_no or self.transportation_doc_no or False,
                'default_transportation_doc_date': self.lr_date or self.transportation_doc_date or False,
            })
            action['context'] = ctx
        return action
