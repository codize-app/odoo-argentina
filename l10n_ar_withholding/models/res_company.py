# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
try:
    from pyafipws.iibb import IIBB
except ImportError:
    IIBB = None
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)

class ResCompany(models.Model):
    _inherit = "res.company"

    regimenes_ganancias_ids = fields.Many2many(
        'afip.tabla_ganancias.alicuotasymontos',
        'res_company_tabla_ganancias_rel',
        'company_id', 'regimen_id',
        'Regimenes Ganancia',
    )

    automatic_withholdings = fields.Boolean(
        string='Retenciones automáticas',
        help='Aplicar retenciones automáticamente en la confirmación de los pagos'
    )
