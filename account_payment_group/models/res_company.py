from odoo import models, fields

class ResCompany(models.Model):
    _inherit = "res.company"

    double_validation = fields.Boolean(
        '¿Doble validación en los pagos?',
        help='Utilizar validación en dos pasos para pagos a proveedores'
    )
