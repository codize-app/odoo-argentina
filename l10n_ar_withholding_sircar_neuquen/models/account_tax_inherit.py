# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class AccountTax(models.Model):
    _inherit = "account.tax"

    tax_sircar_neuquen_ret = fields.Boolean('Imp. Ret SIRCAR Neuquen', default = False)