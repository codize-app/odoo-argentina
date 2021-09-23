# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError

class ResPartner(models.Model):
    _inherit = 'product.template'

    has_internal_taxes = fields.Boolean('¿Tiene Impuestos Internos?')
    internal_taxes = fields.Float('Impuestos Internos', help='Suma total de los impuestos internos de este producto. Este valor se descontará del Precio de venta al ser facturado.', default=0)
