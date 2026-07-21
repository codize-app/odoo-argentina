# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import datetime, date, timedelta
from dateutil import relativedelta
from base64 import encodebytes
import logging
_logger = logging.getLogger(__name__)


class AccountExportSicore(models.Model):
    _name = 'account.export.sicore'
    _description = 'Exportación SICORE'

    name = fields.Char('Nombre')
    date_from = fields.Date('Fecha desde')
    date_to = fields.Date('Fecha hasta')
    export_sicore_data = fields.Text('Contenidos archivo SICORE', default='')
    tax_withholding = fields.Many2one(
        'account.tax',
        'Imp. de ret utilizado',
        default=lambda self: self.env['account.tax'].search([
            ('withholding_type', '=', 'tabla_ganancias'),
            ('type_tax_use', '=', 'purchase'),
            ('company_id', '=', self.env.company.id),
        ], limit=1),
    )

    @api.depends('export_sicore_data')
    def _compute_files(self):
        for rec in self:
            rec.export_sicore_filename = _('Sicore_%s_%s.txt') % (
                str(rec.date_from), str(rec.date_to))
            rec.export_sicore_file = encodebytes(
                rec.export_sicore_data.encode('ISO-8859-1'))

    export_sicore_file = fields.Binary('Archivo SICORE', compute='_compute_files')
    export_sicore_filename = fields.Char('Archivo SICORE', compute='_compute_files')

    def compute_sicore_data(self):
        self.ensure_one()
        windows_line_ending = '\r\n'
        payments = self.env['account.payment'].search([
            ('payment_type', '=', 'outbound'),
            ('state', 'not in', ['cancel', 'draft']),
            ('date', '<=', self.date_to),
            ('date', '>=', self.date_from),
        ])
        string = ''

        for payment in payments:
            if not payment.communication or not payment.withholding_number:
                continue
            if payment.tax_withholding_id.id != self.tax_withholding.id:
                continue

            # 1er campo codigo de comprobante: pago 06
            string += '06'
            # 2do campo fecha de emision de comprobante
            string += str(payment.date)[8:10] + '/' + str(payment.date)[5:7] + '/' + str(payment.date)[:4]
            # 3er campo Número del comprobante
            string += (payment.payment_group_id.display_name[-8:]).zfill(16)
            # 4to campo Importe comprobante
            string += ("%.2f" % payment.payment_group_id.payments_amount).replace('.', ',').zfill(16)
            # 5to Campo - Código de impuesto
            string += '0217'
            # 6to campo - Código de régimen
            concepto = payment.communication[:3]
            concepto = ''.join(filter(str.isnumeric, concepto))
            string += str(concepto).zfill(3)
            # 7mo campo - codigo de operacion
            string += '1'
            # 8vo campo - Base de cálculo
            string += ("%.2f" % payment.withholdable_base_amount).replace('.', ',').zfill(14)
            # 9vo campo - fecha de emision de la retencion
            string += str(payment.date)[8:10] + '/' + str(payment.date)[5:7] + '/' + str(payment.date)[:4]
            # 10mo codigo de condicion
            if payment.tax_withholding_id.condicion_sicore == 'withholding':
                string += '01'
            elif payment.tax_withholding_id.condicion_sicore == 'perception':
                string += '02'
            else:
                string += '99'
            # 11vo - retencion a sujetos suspendidos
            string += '0'
            # 12mo campo - importe retencion
            string += ("%.2f" % payment.amount).replace('.', ',').zfill(14)
            # 13vo campo - porcentaje de la exclusion
            string += '000,00' + '          '
            # 14 tipo de documento del retenido
            string += '80'
            # 15vo campo - Nro. de documento del sujeto
            string += payment.partner_id.vat + '         '
            # 16vo campo nro certificado original
            string += payment.withholding_number.zfill(14) + '                              0                      '
            # CRLF
            string += windows_line_ending

        _logger.warning('******* string: {0}'.format(string))
        self.export_sicore_data = string
