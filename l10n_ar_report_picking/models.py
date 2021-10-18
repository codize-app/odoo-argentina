# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, RedirectWarning
import logging
import datetime
from datetime import datetime, timedelta, date
import json
import base64

class AccountJournal(models.Model):
    _inherit = 'account.journal'

    is_afip_picking_journal = fields.Boolean('Es Diario de Remitos Electrónicos')

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def validate_picking(self):
        sequence = self.env['ir.sequence'].search([('journal_id', '=', self.afip_picking_journal.id)], limit=1)
        if sequence:
            if self.afip_picking_validate == False:
                self.afip_picking_number = str(sequence.number_next).zfill(sequence.padding)
                sequence.number_next_actual = sequence.number_next_actual + sequence.number_increment
                self.afip_picking_validate = True
            else:
                raise ValidationError('El Remito ya fue Validado en el pasado. Pruebe cancelarlo y crear uno nuevo.')
        else:
            raise ValidationError('La Secuencia no está configurada en el Diario del Remito. No es posible Validar el movimiento como un Remito Electrónico.')

    def _default_picking_journal(self):
        journal_id = self.env['account.journal'].search([('is_afip_picking_journal', '=', True)], limit=1)
        return journal_id.id

    afip_cai = fields.Char('CAI', size=18)
    afip_cai_due = fields.Date('Fecha de Vencimiento CAI')
    afip_picking_journal = fields.Many2one('account.journal', 'Diario de Remitos Electrónicos', default=_default_picking_journal)
    afip_picking_number = fields.Char('Número de Remito', readonly=True)
    afip_picking_validate = fields.Boolean('Remito Validado', readonly=True)
