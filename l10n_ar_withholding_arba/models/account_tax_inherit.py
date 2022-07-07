# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class AccountTax(models.Model):
    _inherit = "account.tax"

    tax_arba_ret = fields.Boolean('Imp. Ret ARBA', default = False)

    def create_payment_withholdings(self, payment_group):
        for rec in self:
            if rec.tax_arba_ret:
                return
            else:
                return super(AccountTax, rec).create_payment_withholdings(payment_group)