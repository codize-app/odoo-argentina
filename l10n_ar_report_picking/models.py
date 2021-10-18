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

    def _default_picking_journal(self):
        journal_id = self.env['account.journal'].search([('is_afip_picking_journal', '=', True)], limit=1)
        return journal_id.id

    afip_cai = fields.Char('CAI', size=18)
    afip_cai_due = fields.Date('Fecha de Vencimiento CAI')
    afip_picking_journal = fields.Many2one('account.journal', 'Diario de Remitos Electrónicos', default=_default_picking_journal)

