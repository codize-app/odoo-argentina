# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime,date,timedelta
from dateutil import relativedelta
import base64
import logging
_logger = logging.getLogger(__name__)

class AccountExportSircarNeuquen(models.Model):
    _name = 'account.export.sircar.neuquen'
    _description = 'account.export.sircar.neuquen'

    name = fields.Char('Nombre')
    date_from = fields.Date('Fecha desde')
    date_to = fields.Date('Fecha hasta')
    export_sircar_neuquen_data_ret = fields.Text('Contenidos archivo SIRCAR Neuquen Ret', default='')
    export_sircar_neuquen_data_per = fields.Text('Contenidos archivo SIRCAR Neuquen Per', default='')
    tax_withholding = fields.Many2one('account.tax','Imp. de ret utilizado') 
    
    #Retenciones
    @api.depends('export_sircar_neuquen_data_ret')
    def _compute_files_ret(self):
        self.ensure_one()
        self.export_sircar_neuquen_filename_ret = _('Sircar_neuquen_ret_%s_%s.txt') % (str(self.date_from),str(self.date_to))
        self.export_sircar_neuquen_file_ret = base64.encodestring(self.export_sircar_neuquen_data_ret.encode('ISO-8859-1'))
    export_sircar_neuquen_file_ret = fields.Binary('TXT SIRCAR Neuquen Ret',compute=_compute_files_ret)
    export_sircar_neuquen_filename_ret = fields.Char('TXT SIRCAR Neuquen Ret',compute=_compute_files_ret) 
    
    #Percepciones
    @api.depends('export_sircar_neuquen_data_per')
    def _compute_files_per(self):
        self.ensure_one()
        self.export_sircar_neuquen_filename_per = _('Sircar_neuquen_per_%s_%s.txt') % (str(self.date_from),str(self.date_to))
        self.export_sircar_neuquen_file_per = base64.encodestring(self.export_sircar_neuquen_data_per.encode('ISO-8859-1'))
    export_sircar_neuquen_file_per = fields.Binary('TXT SIRCAR Neuquen Per',compute=_compute_files_per)
    export_sircar_neuquen_filename_per = fields.Char('TXT SIRCAR Neuquen Per',compute=_compute_files_per)


    def compute_sircar_neuquen_data(self):
        self.ensure_one()
        windows_line_ending = '\r' + '\n'

        # Retenciones
        payments = self.env['account.payment'].search([('payment_type','=','outbound'),('state','not in',['cancel','draft']),('date','<=',self.date_to),('date','>=',self.date_from)])
        string = ''
        for payment in payments:
            if not payment.withholding_number:
                continue
            if payment.tax_withholding_id.id != self.tax_withholding.id:
                continue
            # TXT segun formato de 

            # Recorrepemos todas las facturas que se pagaron mediantes el grupo de pago al que corresponde este pago
            # Esto lo hacemos para hacer una linea por factura en el TXT de SICORE
            for invoce_pay in payment.payment_group_id.matched_move_line_ids:
                # 1 campo Cuit contribuyente Retenido. Long: 13. Formato 99-99999999-9
                string = string + str(invoce_pay.move_id.partner_id.vat)[0:2] + '-' + str(invoce_pay.move_id.partner_id.vat)[2:10] + '-' + str(invoce_pay.move_id.partner_id.vat)[10:]
                # 2 campo Fecha Retención. Long: 10. Formato dd/mm/aaaa. Debe corresponder al periodo declarado.
                string = string + str(payment.date)[8:10] + '/' + str(payment.date)[5:7] + '/' + str(payment.date)[:4]
                # 3 campo Numero Sucursal. Long: 4. Mayor a cero. Completar con ceros a la izquierda
                string = string + invoce_pay.move_id.name[6:10]
                # 4 campo Numero Emisión. Long: 8. Mayor a cero. Completar con ceros a la izquierda
                string = string + payment.withholding_number.zfill(8)
                # 5 campo Importe de Retención. Long: 11. Debe ser > 0. Con separador
                # decimal (, o .). Completar con ceros a la izquierda
                porcen_en_total_ret = ((invoce_pay.move_id.amount_untaxed * 100) / payment.withholding_base_amount) / 100
                string = string + ("%.2f"%(payment.amount * porcen_en_total_ret)).zfill(11)
                # 6 campo Tipo Operación. Long: 1. A= Alta, B=Baja, M=Modificación
                string = string + 'A'
                # CRLF
                string = string + windows_line_ending
            
        self.export_sicar_data_ret = string

        # Percepciones
        invoices = self.env['account.move'].search([('move_type','in',['out_invoice','out_refund']),('state','=','posted'),('invoice_date','<=',self.date_to),('invoice_date','>=',self.date_from)])
        string = ''
        for invoice in invoices:
            for group in invoice.amount_by_group:
                if group[0] == 'Perc IIBB SIRCAR Neuquen':
                    
                    # TXT segun formato 
                    # 1 campo Cuit contribuyente Retenido. Long: 13. Formato 99-99999999-9
                    string = string + str(invoice.partner_id.vat)[0:2] + '-' + str(invoice.partner_id.vat)[2:10] + '-' + str(invoice.partner_id.vat)[10:]
                    # 2 campo Fecha Retención. Long: 10. Formato dd/mm/aaaa. Debe corresponder al periodo declarado.
                    string = string + str(invoice.invoice_date)[8:10] + '/' + str(invoice.invoice_date)[5:7] + '/' + str(invoice.invoice_date)[:4]
                    # 3 campo Tipo de Comprobante. Long: 1. Valores F=Factura, R=Recibo, C=Nota Crédito, D =Nota Debito, 
                    # V=Nota de Venta, E=Factura de Crédito Electrónica, H=Nota de Crédito Electrónica, I=Notade Débito Electrónica
                    if invoice.l10n_latam_document_type_id.internal_type == 'invoice':
                        string = string + 'F'
                    elif invoice.l10n_latam_document_type_id.internal_type == 'debit_note':
                        string = string + 'D'
                    elif invoice.l10n_latam_document_type_id.internal_type == 'credit_note':
                        string = string + 'C'
                    # 4 Letra Comprobante. Long: 1. Valores A,B,C, o “ ” (blanco)
                    string = string + invoice.l10n_latam_document_type_id.l10n_ar_letter
                    # 5 Numero Sucursal. Long: 4. Mayor a cero. Completar con ceros a la izquierda.
                    string = string + str(invoice.name)[6:10]
                    # 5 Numero Emision. Long: 8. Mayor a cero. Completar con ceros a la izquierda.
                    string = string + str(invoice.name)[-8:]
                    # 6 Monto Imponible. Long: 12. Con separador decimal (, o .). Mayor a cero, o Excepto para Nota de crédito, donde 
                    # el importe debe ser negativo y la base debe ser menor o igual a cero. Completar con ceros a la izquierda. 
                    # En las notas de crédito el signo negativo ocupará la primera posición a la izquierda.
                    if invoice.move_type == 'out_refund':
                        string = string + '-' + str(invoice.amount_untaxed).zfill(11)
                    else:
                        string = string + str(invoice.amount_untaxed).zfill(12)
                    # 7 Importe de Percepcion. Long: 11. Con separador decimal (, o .). Mayor a cero, excepto para notas de crédito donde
                    # debe ser negativo. Completar con ceros a la izquierda. En las notas de crédito el signo negativo 
                    # ocupará la primera posición a la izquierda.
                    if invoice.move_type == 'out_refund':
                        string = string + '-' + str(group[1]).zfill(10)
                    else:
                        string = string + str(group[1]).zfill(11)
                    # 8 Tipo Operación. Long: 1. A= Alta, B=Baja, M=Modificación.
                    string = string + 'A'

                    string = string + windows_line_ending
                    
        self.export_sircar_neuquen_data_per = string


