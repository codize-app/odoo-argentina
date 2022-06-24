# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class AccountTax(models.Model):
    _inherit = "account.tax"

    tax_arba_ret = fields.Boolean('Imp. Ret ARBA', default = False)