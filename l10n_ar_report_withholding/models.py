# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import logging
import datetime
from datetime import datetime, timedelta, date

class AccountPayment(models.Model):
	_inherit = 'account.payment'

	def btn_print_withholding(self):
            self.ensure_one()
            return self.env.ref('l10n_ar_report_withholding.account_payment_withholdings').report_action(self)

	def _compute_print_withholding(self):
            for rec in self:
                if rec.state == 'posted':
                    if rec.tax_withholding_id:
                        rec.print_withholding = True
                    else:
                        rec.print_withholding = False
                else:
                    rec.print_withholding = False

	print_withholding = fields.Boolean('print_withholding',compute=_compute_print_withholding)
