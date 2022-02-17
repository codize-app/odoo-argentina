# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, RedirectWarning
import logging
import datetime
from datetime import datetime, timedelta, date
import json
import base64
from dateutil import parser

_logger = logging.getLogger(__name__)

class AccountJournal(models.Model):
    _inherit = 'account.journal'

    def remove_afip_cai_due(self):
        for r in self.account_journal_picking:
            if datetime.now().date() > r.afip_cai_due:
                r.unlink()

    def upload_picking_csv(self):
        if self.picking_csv:
            csv = base64.b64decode(self.picking_csv).decode("utf-8", "ignore").replace('\r', '')
            row = csv.split('\n')
            for r in row:
                col = r.split(',')
                if len(col) == 2:
                    _logger.info(col)
                    d = parser.parse(col[1])
                    self.env['account.journal.picking'].create({'res_id': self.id, 'afip_cai': col[0], 'afip_cai_due': d.strftime("%Y-%m-%d")})
            self.picking_csv = False
        else:
            raise ValidationError('Debe Cargar un Archivo CSV con formato válido.')

    is_afip_picking_journal = fields.Boolean('Es Diario de Remitos')
    picking_csv = fields.Binary('Lista de CAI en CSV')
    account_journal_picking = fields.One2many('account.journal.picking', 'res_id', string='Lista de CAI Disponibles')

class AccountJournalPicking(models.Model):
    _name = 'account.journal.picking'

    afip_cai = fields.Char('CAI', size=18)
    afip_cai_due = fields.Date('Fecha de Vencimiento CAI')
    res_id = fields.Many2one('account.journal', 'Diario')

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def validate_picking(self):
        sequence = self.env['ir.sequence'].search([('journal_id', '=', self.afip_picking_journal.id)], limit=1)
        if sequence:

            if self.afip_picking_journal.account_journal_picking:
                for r in self.afip_picking_journal.account_journal_picking:
                    self.afip_cai = r.afip_cai
                    self.afip_cai_due = r.afip_cai_due
                    r.unlink()
                    break
            else:
                raise ValidationError('No hay CAI cargados en el Diario del Remito Electrónico.')

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

    afip_cai = fields.Char('CAI', size=18, readonly=True)
    afip_cai_due = fields.Date('Fecha de Vencimiento CAI', readonly=True)
    afip_picking_journal = fields.Many2one('account.journal', 'Diario de Remitos Electrónicos', default=_default_picking_journal)
    afip_picking_number = fields.Char('Número de Remito', readonly=True)
    afip_picking_validate = fields.Boolean('Remito Validado', readonly=True)
