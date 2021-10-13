# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, RedirectWarning
import logging
import datetime
from datetime import datetime, timedelta, date
import json
import base64

class AccountMoveLine(models.Model):
    _inherit = 'stock.picking'

    afip_cai = fields.Char('CAI', size=18)
    afip_cai_due = fields.Date('Fecha de Vencimiento CAI')
