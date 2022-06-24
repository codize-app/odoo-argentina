# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime,date,timedelta
from dateutil import relativedelta
import base64
import logging
_logger = logging.getLogger(__name__)

class AccountExportAgip(models.Model):
    _name = 'account.export.agip'
    _description = 'account.export.agip'

    name = fields.Char('Nombre')
    date_from = fields.Date('Fecha desde')
    date_to = fields.Date('Fecha hasta')
    export_agip_data = fields.Text('Contenidos archivo AGIP', default='')
    tax_withholding = fields.Many2one('account.tax','Imp. de ret utilizado') 
    
    @api.depends('export_agip_data')
    def _compute_files(self):
        self.ensure_one()
        # segun vimos aca la afip espera "ISO-8859-1" en vez de utf-8
        # http://www.planillasutiles.com.ar/2015/08/
        # como-descargar-los-archivos-de.html
        self.export_agip_filename = _('Agip_%s_%s.txt') % (str(self.date_from),str(self.date_to))
        self.export_agip_file = base64.encodestring(self.export_agip_data.encode('ISO-8859-1'))

    export_agip_file = fields.Binary('Archivo AGIP',compute=_compute_files)
    export_agip_filename = fields.Char('Archivo AGIP',compute=_compute_files)


    def compute_agip_data(self):
        self.ensure_one()
        windows_line_ending = '\r' + '\n'
        payments = self.env['account.payment'].search([('payment_type','=','outbound'),('state','not in',['cancel','draft']),('date','<=',self.date_to),('date','>=',self.date_from)])
        #,('payment_date','<=',self.date_to),('payment_date','>=',self.date_from)])
        string = ''
        _logger.warning('***** payments: {0}'.format(payments))
        for payment in payments:
            if not payment.withholding_number:
                _logger.warning('***** if2: {0}'.format(payment.name))
                continue
            _logger.warning('***** payment.tax_withholding_id.id: {0}'.format(payment.tax_withholding_id.id))
            _logger.warning('***** self.tax_withholding.id: {0}'.format(self.tax_withholding.id))
            if payment.tax_withholding_id.id != self.tax_withholding.id:
                _logger.warning('***** if3: {0}'.format(payment.name))
                continue
            # TXT segun formato de https://www.agip.gob.ar/agentes/agentes-de-recaudacion/ib-agentes-recaudacion/aplicativo-arciba/aclaraciones-sobre-las-adecuaciones-al-aplicativo-e-arciba-
            # 1 campo Tipo de Operación: 1: Retención / 2: Percepción
            string = string + '1'
            # 2 campo Código de Norma: Según Tipo de Operación
            string = string + '000'
            # 3 campo Fecha de Retención / Percepción : dd/mm/aaaa
            string = string + str(payment.date)[8:10] + '/' + str(payment.date)[5:7] + '/' + str(payment.date)[:4]
            # 4 campo Tipo de comprobante origen de la Retención / Percepción : Según Tipo de Operación
            #Si Tipo de Operación = 1
                #01- Factura
                #02- Nota de Débito
                #03- Orden de Pago
                #04- Boleta de Depósito
                #05- Liquidación de pago
                #06- Certificado de obra
                #07- Recibo
                #08- Cont de Loc de Servic.
                #09- Otro Comprobante
                #10- Factura de Crédito Electrónica MiPyMEs.
                #11- Nota de Débito Electrónica MiPyMEs.
                #12- Orden de Pago de Comp. Electrónica MiPyMEs
                #13- Otro Comp. de Crédito Electrónicas MiPyMEs.
            #Si Tipo de Operación = 2
                #01- Factura
                #09- Otro Comprobante
                #10- Factura de Crédito Electrónica MiPyMEs.
                #13- Otro Comp de Crédito Electrónicas MiPyMEs
            string = string + '01'
            # 5 campo Letra del Comprobante
            #Operación Retenciones
                #Si Agente=R.I y Suj.Ret = R.I : Letra = A, M, B
                #Si Agente=R.I y Suj.Ret = Exento : Letra = C
                #Si Agente=R.I y Suj.Ret = Monot : Letra = C
                #Si Agente=Exento y Suj.Ret=R.I : Letra = B
                #Si Agente=Exento y Suj.Ret=Exento : Letra = C
                #Si Agente=Exento y Suj.Ret=Monot. : Letra = C
            #Operación Percepción
                #Si Agente=R.I y Suj.Perc = R.I : Letra = A, M, B
                #Si Agente=R.I y Suj.Perc = Exento : Letra = B
                #Si Agente=R.I y Suj.Perc = Monot. : Letra = A, M
                #Si Agente=R.I y Suj.Perc = No Cat. : Letra = B
                #Si Agente=Exento y Suj.Perc=R.I : Letra = C
                #Si Agente=Exento y Suj.Perc=Exento : Letra = C
                #Si Agente=Exento y Suj.Perc=Monot. : Letra = C
                #Si Agente=Exento y Suj.Perc=No Cat. : Letra = C
            #Operación Retenciones/Percepciones
                #Si Tipo Comprobante = (01,06,07) : A,B,C,M sino dejar 1 espacio en blanco
                #Si Tipo Comprobante = (10) : A,B,C sino dejar 1 espacio en blanco
            string = string + 'A'
            # 6 campo Nro de comprobante: Largo: 16
            string = string + '    ' + payment.withholding_number[10:].zfill(12)
            # 7 campo Fecha de Comprobante : dd/mm/aaaa
            string = string + str(payment.date)[8:10] + '/' + str(payment.date)[5:7] + '/' + str(payment.date)[:4]
            # 8 campo Monto del comprobante: Máximo: 9999999999999,99
            cadena = "%.2f"%payment.amount
            cadena = cadena.replace('.',',')
            string = string + cadena.zfill(16)
            # 9 campo Nro de certificado propio:
            # Si Tipo de Operación =1 se
            # carga el N° de certificado o
            # blancos.
            # Si Tipo de Operación = 2 se
            # completa con blancos. Largo: 16
            string = string + '                ' # Verificar
            # 10 campo Tipo de documento del Retenido / Percibido. 3: CUIT 2: CUIL 1: CDI
            if payment.partner_id.l10n_latam_identification_type_id.name == 'CUIT':
                string = string + '3'
            elif payment.partner_id.l10n_latam_identification_type_id.name == 'CUIL':
                string = string + '2'
            elif payment.partner_id.l10n_latam_identification_type_id.name == 'Cédula Extranjera':
                string = string + '1'
            # 11 campo Nro de documento del Retenido / Percibido. Largo: 11
            string = string + payment.partner_id.vat
            # 12 campo Situación IB del Retenido / Percibido. 1: Local 2: Convenio Multilateral 4: No inscripto 5: Reg.Simplificado
            if payment.partner_id.gross_income_type == 'local':
                string = string + '1'
            elif payment.partner_id.gross_income_type == 'multilateral':
                string = string + '2'
            elif payment.partner_id.gross_income_type == 'no_liquida':
                string = string + '4'
            elif payment.partner_id.gross_income_type == 'reg_simplificado':
                string = string + '5'
            # 13 Nro Inscripción IB del Retenido / Percibido. Si Situación IB del Retenido=4 : 00000000000
            if payment.partner_id.gross_income_type == 'no_liquida':
                string = string + '00000000000'
            else:
                string = string + payment.partner_id.gross_income_number
            # 14 Situación frente al IVA del Retenido / Percibido. 1 - Responsable Inscripto 3 - Exento 4 - Monotributo
            if payment.partner_id.l10n_ar_afip_responsibility_type_id.code == '1':
                string = string + '1'
            elif payment.partner_id.l10n_ar_afip_responsibility_type_id.code == '4':
                string = string + '3'
            elif payment.partner_id.l10n_ar_afip_responsibility_type_id.code == '6':
                string = string + '4'
            # 15 Razón Social del Retenido/Percibido. Largo 30
            string = string + payment.partner_id.name.ljust(30)
            # 16 Importe otros conceptos . Largo 16
            string = string + '0000000000000,00' # VERIFICAR
            # 17 Importe IVA . Largo 16. Sólo completar si emisor es R.I.
                                        #y receptor R.I. y letra del
                                        #Comprobante = (A, M.)
                                        #Si emisor es R.I. y Receptor
                                        #Monotributo, no completar
            string = string + '0000000000000,00' # VERIFICAR
            # 18 Monto Sujeto a Retención / Percepción . Largo 16. Monto Sujeto a Retención/
                                                                    #Percepción = (Monto del comp -
                                                                    #Importe Iva - Importe otros
                                                                    #conceptos)
            string = string + '0000000000000,00' # VERIFICAR
            # 19 Alicuota. Largo 5. Mayor a 0(cero) - Excepto Código de Norma 28 y 29. Según el Tipo de Op. ,Código de Norma y Tipo de Agente
            string = string + '00,00' # VERIFICAR
            # 20 Retención / Percepción Practicada. Largo 16. Retención/Percepción
                                                                #Practicada = Monto Sujeto a
                                                                #Retención/ Percepción *
                                                                #Alícuota /100
            string = string + '0000000000000,00' # VERIFICAR
            # 21 Monto Total Retenido/Percibido. Largo 16. Igual a Retención / Percepción Practicada
            string = string + '0000000000000,00' # VERIFICAR
            # 22 Aceptación. Largo 1. Solo en los casos de Retenciones por el "Régimen de Factura de Crédito Electrónica Mi
                                        #PyMEs" (Tipo de Comprobante = 10, 11, 12, 13), debe informar: E: Aceptación Expresa,
                                        #T: Aceptación Tácita. En los demás casos de retenciones y/o percepciones dejar 1 (un) espacio en blanco.
            string = string + ' '
            # 23 Fecha Aceptación "Expresa". Largo 10. Formato: dd/mm/aaaa. Sí, en Orden 22, E: Aceptación Expresa, informar Fecha de "Aceptación Expresa", en caso
            #de aceptación Tacita y para el resto de las retenciones y/o percepciones, dejar 10 (diez)espacios en blanco.
            string = string + '         '
            



            
            # CRLF
            string = string + windows_line_ending
            
        _logger.warning('******* string: {0}'.format(string))
        self.export_agip_data = string

