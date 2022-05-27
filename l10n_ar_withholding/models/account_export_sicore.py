# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime,date,timedelta
from dateutil import relativedelta
import base64
import logging
_logger = logging.getLogger(__name__)

class AccountExportSicore(models.Model):
    _name = 'account.export.sicore'
    _description = 'account.export.sicore'

    name = fields.Char('Name')
    date_from = fields.Date('Fecha desde')
    date_to = fields.Date('Fecha hasta')
    export_sicore_data = fields.Text('Contenidos archivo SICORE', default='')
    
    @api.depends('export_sicore_data')
    def _compute_files(self):
        self.ensure_one()
        # segun vimos aca la afip espera "ISO-8859-1" en vez de utf-8
        # http://www.planillasutiles.com.ar/2015/08/
        # como-descargar-los-archivos-de.html
        self.export_sicore_filename = _('Sicore_%s_%s.txt') % (str(self.date_from),str(self.date_to))
        self.export_sicore_file = base64.encodestring(self.export_sicore_data.encode('ISO-8859-1'))

    export_sicore_file = fields.Binary('Archivo SICORE',compute=_compute_files)
    export_sicore_filename = fields.Char('Archivo SICORE',compute=_compute_files)


    def compute_sicore_data(self):
        self.ensure_one()
        windows_line_ending = '\r' + '\n'
        payments = self.env['account.payment'].search([('payment_type','=','outbound'),('state','not in',['cancel','draft']),('date','<=',self.date_to),('date','>=',self.date_from)])
        #,('payment_date','<=',self.date_to),('payment_date','>=',self.date_from)])
        string = ''
        _logger.warning('***** payments: {0}'.format(payments))
        for payment in payments:
            if not payment.communication or not payment.withholding_number:
                _logger.warning('***** if2: {0}'.format(payment.name))
                continue
            if 'Retenciones' not in payment.journal_id.name:
                _logger.warning('***** if3: {0}'.format(payment.name))
                continue
            # 1er campo codigo de comprobante: pago 06
            string = string + '06'
            # 2do campo fecha de emision de comprobante
            string = string + str(payment.date)[8:10] + '/' + str(payment.date)[5:7] + '/' + str(payment.date)[:4]
            # 3er campo nro de comprobante - imprimimos nro de retenciontring = string + payment_data['withholding_number'].zfill(16)
            string = string + '    ' + payment.withholding_number[10:].zfill(12)
            # 4to campo amount	
            if payment.withholding_base_amount > 0:
                cadena = "%.2f"%payment.withholding_base_amount
                cadena = cadena.replace('.',',')
            else:
                cadena = '0,00'
            #string = string + cadena.rjust(16)
            string = string + cadena.zfill(16)
            #string = string + str(payment_data['withholding_base_amount']).zfill(16)
            # 5to Campo - Codigo de Impuesto - 217 tomado de tabla de codigos de sicore
            if payment.tax_withholding_id.tax_group_id.l10n_ar_vat_afip_code:
                string = string + str(payment.tax_withholding_id.tax_group_id.l10n_ar_vat_afip_code).zfill(4)[:3]
            else:
                string = string + '0000'
            # 6to campo - Codigo de regimen 078 tomado de tabla de codigos de sicore - Enajenacion de bienes de cambio
            #string = string + '078'
            #string = string + partner_data[0]['default_regimen_ganancias_id'][1].zfill(3)[:3]
            concepto = int(payment.communication[:3])
            string = string + str(concepto).zfill(4)
            # 7mo campo - codigo de operacion 1 tomado de ejemplo XLS
            string = string + '1'
            # 8vo campo - base de calculo (52 a 65)
            cadena = "%.2f"%payment.withholding_base_amount
            cadena = cadena.replace('.',',')
            string = string + cadena.zfill(14)
            # 9vo campo - fecha de emision de la retencion (66 a 75)
            string = string + str(payment.date)[8:10] + '/' + str(payment.date)[5:7] + '/' + str(payment.date)[:4]
            # (76 a 77) codigo de condicioon
            if payment.tax_withholding_id.condicion_sicore == 'withholding':
                string = string + '01'
            elif payment.tax_withholding_id.condicion_sicore == 'perception':
                string = string + '02'
            else:
                string = string + '99'
            #(78 a 78) - retencion a sujetos suspendidos
            string = string + ' '
            # 11mo campo - importe retencion - 79 a 92
            #    cadena = str(round(payment_data['amount'],2))
            cadena = "%.2f"%payment.amount
            cadena = cadena.replace('.',',')
            #string = string + str(payment_data['amount']).zfill(14)
            string = string + cadena.zfill(14)
            # 12vo campo - porcentaje de la exclusion
            cadena = '000,00'
            string = string + cadena
            # 13vo campo - fecha de emision del boletin
            #string = string + payment_data['payment_date'][8:10] + '/' + payment_data['payment_date'][5:7] + '/' + payment_data['payment_date'][:4]
            string = string + ' '.rjust(10)
            # 14 tipo de documento del retenido
            string = string + '80'
            # 15vo campo - ro de CUIT
            string = string + payment.partner_id.vat + '         '
            # 16vo campo nro certificado original
            #string = string + payment_data['withholding_number'].zfill(14)
            string = string + '0'.zfill(14)
            # Denominacion del ordenante
            #string = string + partner_data[0]['name'][:30].ljust(30)
            string = string + ' '.ljust(30)
            # Acrecentamiento
            string = string + '0'
            # cuit pais retenido
            string = string + '00000000000'
            # cuit del ordenante
            string = string + '00000000000'
            # CRLF
            string = string + windows_line_ending
            
        _logger.warning('******* string: {0}'.format(string))
        self.export_sicore_data = string

