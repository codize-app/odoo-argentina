# -*- coding: utf-8 -*-
# 16.0 EE

from odoo import models, fields, api
from datetime import datetime
from datetime import date
from odoo.tools import format_date

class ResCurrency(models.Model):
    _inherit = 'res.currency'

    def l10n_ar_action_get_afip_ws_currency_rate_get(self):
        c = self.env['res.currency'].sudo().search([('name', '=', 'USD')], limit=1)
        for cu in c:
            date, rate = cu._l10n_ar_get_afip_ws_currency_rate()
            #date = datetime.strptime(date.today(), '%Y%m%d').date()
            date = datetime.today()
            cu.update({'rate_ids': [(0, 0, {'name': date, 'inverse_company_rate': rate})]})
