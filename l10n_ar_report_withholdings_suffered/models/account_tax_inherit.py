# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
from odoo import models, fields


class AccountTax(models.Model):
    _inherit = 'account.tax'

    l10n_ar_withholding_state_id = fields.Many2one(
        'res.country.state',
        string='Provincia (Percepciones Sufridas)',
        help='Provincia a la que corresponde este impuesto de percepción '
             'IIBB. Se usa para que el Reporte de Retenciones y '
             'Percepciones Sufridas reconozca automáticamente a qué '
             'jurisdicción pertenece cada factura, sin tener que elegirlo '
             'manualmente cada vez.',
    )
