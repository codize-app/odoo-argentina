from odoo import fields, models

class ResCompany(models.Model):
    _inherit = "res.company"

    arca_activity = fields.Char(string='Actividad Principal', help="Actividad Principal de la Compañía, se utiliza para generar los reportes de IVA Simple.")
