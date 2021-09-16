# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
from odoo import models, api, fields


class AccountPayment(models.Model):
    _inherit = "account.payment"

    used_withholding = fields.Boolean('Usado en retenciones')
