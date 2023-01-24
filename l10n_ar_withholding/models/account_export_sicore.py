# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime,date,timedelta
from dateutil import relativedelta
import base64
import logging
_logger = logging.getLogger(__name__)
try:
    from base64 import encodebytes
except ImportError:  # 3+
    from base64 import encodestring as encodebytes

class AccountExportSicore(models.Model):
    _name = 'account.export.sicore'
    _description = 'account.export.sicore'

    name = fields.Char('Nombre')
    date_from = fields.Date('Fecha desde')
    date_to = fields.Date('Fecha hasta')
    export_sicore_data = fields.Text('Contenidos archivo SICORE', default='')
    tax_withholding = fields.Many2one('account.tax','Imp. de ret utilizado')
    
    @api.depends('export_sicore_data')
    def _compute_files(self):
        self.ensure_one()
        # segun vimos aca la afip espera "ISO-8859-1" en vez de utf-8
        # http://www.planillasutiles.com.ar/2015/08/
        # como-descargar-los-archivos-de.html
        self.export_sicore_filename = _('Sicore_%s_%s.txt') % (str(self.date_from),str(self.date_to))
        self.export_sicore_file = encodebytes(self.export_sicore_data.encode('ISO-8859-1'))

    export_sicore_file = fields.Binary('Archivo SICORE',compute=_compute_files)
    export_sicore_filename = fields.Char('Archivo SICORE',compute=_compute_files)


    def compute_sicore_data(self):
        self.ensure_one()
        windows_line_ending = '\r' + '\n'
        payments = self.env['account.payment'].search([('payment_type','=','outbound'),('state','not in',['cancel','draft']),('date','<=',self.date_to),('date','>=',self.date_from)])
        string = ''
        #Txt en basado en datos encontrados en internet
        # http://campus.zoologic.com.ar/novedades/dnvli/dnvlince_interfaces__exportacion_de_ret.htm

        for payment in payments:
            if not payment.communication or not payment.withholding_number:
                continue
            if payment.tax_withholding_id.id != self.tax_withholding.id:
                continue

            # 1er campo codigo de comprobante: pago 06
            string = string + '06'
            # 2do campo fecha de emision de comprobante
            string = string + str(payment.date)[8:10] + '/' + str(payment.date)[5:7] + '/' + str(payment.date)[:4]
            # 3er campo Número del comprobante: 16 caracteres. Exporta el número interno de la orden de pago, agregando ceros 
            # hacia la izquierda hasta completar los 16 caracteres.
            string = string + (payment.payment_group_id.display_name[-8:]).zfill(16)
            # 4to campo Importe comprobante: 16 caracteres de los cuales 13 son enteros, 2 decimales separados por una coma.
            # Monto de la orden de pago, sin sustraer las retenciones.
            string = string + ("%.2f"%payment.payment_group_id.payments_amount).replace('.',',').zfill(16)
            # 5to Campo - Código de impuesto: 4 caracteres. Exporta el Código de impuesto ingresado en el alta de la retención aplicada.
            # Impuesto 217 - SICORE - Impuesto a las Ganancias
            # Impuesto 219 - SICORE- Impuesto sobre los Bienes Personales
            string = string + '0217'
            # 6to campo - Código de régimen:  3 caracteres. Exporta el Código de régimen ingresado en el alta de la retención aplicada.
            concepto = payment.communication[:3]
            #Eliminamos elementos no numericos
            concepto = ''.join(filter(str.isnumeric, concepto))
            string = string + str(concepto).zfill(3)
            # 7mo campo - codigo de operacion 1 tomado de ejemplo XLS
            string = string + '1'
            # 8vo campo - Base de cálculo: 14 caracteres de los cuales 11 son enteros, 2 decimales separados por una coma. 
            string = string +("%.2f"%payment.withholdable_base_amount).replace('.',',').zfill(14)
            # 9vo campo - fecha de emision de la retencion (66 a 75)
            string = string + str(payment.date)[8:10] + '/' + str(payment.date)[5:7] + '/' + str(payment.date)[:4]
            # 10mo (76 a 77) codigo de condicioon
            if payment.tax_withholding_id.condicion_sicore == 'withholding':
                string = string + '01'
            elif payment.tax_withholding_id.condicion_sicore == 'perception':
                string = string + '02'
            else:
                string = string + '99'
            # 11vo(78 a 78) - retencion a sujetos suspendidos
            string = string + '0'
            # 12mo campo - importe retencion - 14 caracteres, de los cuales 11 son enteros y 2 decimales, separados por una coma. Exporta el importe a retener.
            string = string + ("%.2f"%(payment.amount)).replace('.',',').zfill(14) 
            # 13vo campo - porcentaje de la exclusion
            cadena = '000,00' + '          '
            string = string + cadena
            # 14 tipo de documento del retenido
            string = string + '80'
            # 15vo campo - Nro. de documento del sujeto: 11 caracteres. Exporta el C.U.I.T. del retenido.
            string = string + payment.partner_id.vat + '         '
            # 16vo campo nro certificado original
            string = string + payment.withholding_number.zfill(14) + '                              0                      '
            # CRLF
            string = string + windows_line_ending
            
        _logger.warning('******* string: {0}'.format(string))
        self.export_sicore_data = string

