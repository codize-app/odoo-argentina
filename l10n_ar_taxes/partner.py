# -*- coding: utf-8 -*-

from odoo import models, fields, api

class ResPartner(models.Model):
    _inherit = 'product.template'

    has_internal_taxes = fields.Boolean('¿Tiene Impuestos Internos?')
    internal_taxes = fields.Float('Impuesto Interno', default=0)
