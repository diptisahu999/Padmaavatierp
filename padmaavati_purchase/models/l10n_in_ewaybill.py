# -*- coding: utf-8 -*-
from odoo import models, api


class L10nInEwaybill(models.Model):
    _inherit = 'l10n.in.ewaybill'

    @api.model
    def default_get(self, fields_list):
        """Auto-populate Transport & Part B details from the linked invoice/bill"""
        res = super(L10nInEwaybill, self).default_get(fields_list)
        move_id = res.get('account_move_id') or self.env.context.get('default_account_move_id')
        if move_id:
            move = self.env['account.move'].browse(move_id)
            if 'mode' in fields_list and getattr(move, 'transportation_mode', False):
                res['mode'] = move.transportation_mode
            if 'vehicle_type' in fields_list and getattr(move, 'vehicle_type', False):
                res['vehicle_type'] = move.vehicle_type
            if 'vehicle_no' in fields_list:
                veh_no = getattr(move, 'vehicle_no', False) or getattr(move, 'tempo_no', False)
                if veh_no:
                    res['vehicle_no'] = veh_no
            if 'distance' in fields_list and getattr(move, 'distance', False):
                res['distance'] = move.distance
            if 'transportation_doc_no' in fields_list:
                doc_no = getattr(move, 'transportation_doc_no', False) or getattr(move, 'lr_no', False)
                if doc_no:
                    res['transportation_doc_no'] = doc_no
            if 'transportation_doc_date' in fields_list:
                doc_date = getattr(move, 'transportation_doc_date', False) or getattr(move, 'lr_date', False)
                if doc_date:
                    res['transportation_doc_date'] = doc_date
            if 'transporter_id' in fields_list:
                transporter = getattr(move, 'transporter_id', False)
                if transporter:
                    res['transporter_id'] = transporter.id
                elif getattr(move, 'transport_id', False) and move.transport_id.partner_id:
                    res['transporter_id'] = move.transport_id.partner_id.id
        return res
