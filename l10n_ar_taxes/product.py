# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    has_internal_taxes = fields.Boolean('¿Tiene Impuestos Internos?')
    internal_taxes = fields.Float('Impuestos Internos', help='Suma total de los impuestos internos de este producto. Este valor se descontará del Precio de venta al ser facturado.', default=0)

class ProductProduct(models.Model):
    _inherit = 'product.product'

    internal_taxes = fields.Float('Impuestos Internos', default=0, related='product_tmpl_id.internal_taxes', readonly=True)
