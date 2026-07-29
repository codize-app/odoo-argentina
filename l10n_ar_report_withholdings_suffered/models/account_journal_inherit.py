# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
from odoo import models, fields


class AccountJournal(models.Model):
    _inherit = 'account.journal'

    l10n_ar_withholding_state_id = fields.Many2one(
        'res.country.state',
        string='Provincia (Retenciones Sufridas)',
        help='Provincia a la que corresponden las retenciones sufridas '
             'registradas mediante cobranzas de este diario. Se usa para '
             'que el Reporte de Retenciones y Percepciones Sufridas '
             'reconozca automáticamente a qué jurisdicción pertenece cada '
             'pago, sin tener que elegirlo manualmente cada vez.',
    )
