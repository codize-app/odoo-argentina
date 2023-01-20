# -*- coding: utf-8 -*-
from odoo import models, fields
import odoo.addons.decimal_precision as dp

class AccountTaxWithholdingRule(models.Model):
    _name = "account.tax.withholding.rule"
    _order = "sequence"

    sequence = fields.Integer(
        default=10,
    )
    # name = fields.Char(
    #     required=True,
    #     )
    domain = fields.Char(
        required=True,
        default="[]",
        help='Dominio del pago en el que se aplica'
    )
    tax_withholding_id = fields.Many2one(
        'account.tax',
        'Impuesto de retención',
        required=True,
        ondelete='cascade',
    )
    percentage = fields.Float(
        'Porcentaje',
        digits=(16, 4),
        help="Enter % ratio between 0-1."
    )
    fix_amount = fields.Float(
        'Importe fijo',
        digits=dp.get_precision('Account'),
        help="Monto fijo después del porcentaje"
    )
