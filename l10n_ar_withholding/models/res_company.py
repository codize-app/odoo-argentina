# -*- coding: utf-8 -*-
from odoo import models, fields

class ResCompany(models.Model):
    _inherit = "res.company"

    automatic_withholdings = fields.Boolean(
        string='Retenciones automáticas',
        help='Aplicar retenciones automáticamente en la confirmación de los pagos'
    )
