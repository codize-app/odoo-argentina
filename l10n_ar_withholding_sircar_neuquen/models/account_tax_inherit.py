# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class AccountTax(models.Model):
    _inherit = "account.tax"

    tax_sircar_neuquen_ret = fields.Boolean('Imp. Ret SIRCAR Neuquen', default = False)

    def create_payment_withholdings(self, payment_group):
        for rec in self:
            if rec.tax_sircar_neuquen_ret:
                return
            else:
                return super(AccountTax, rec).create_payment_withholdings(payment_group)