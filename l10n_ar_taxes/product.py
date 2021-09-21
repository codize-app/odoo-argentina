# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError

class ResPartner(models.Model):
    _inherit = 'product.template'

    @api.constrains('internal_taxes', 'list_price')
    def _check_internal_taxes(self):
        for rec in self:
           if rec.has_internal_taxes:
               if rec.internal_taxes > rec.list_price:
                   raise ValidationError('Los Impuestos Internos no pueden superar el Precio de Venta. El valor de Precio de Venta debe ser la Base Imponible sumado a los Impuestos Internos.')

    has_internal_taxes = fields.Boolean('¿Tiene Impuestos Internos?')
    internal_taxes = fields.Float('Impuestos Internos', help='Suma total de los impuestos internos de este producto. Este valor se descontará del Precio de venta al ser facturado.', default=0)
