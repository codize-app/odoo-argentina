# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
from odoo import models, fields, api, _
from odoo.exceptions import Warning, ValidationError
import time
import base64
base64.encodestring = base64.encodebytes
import re
import logging
import json
try:
    from base64 import encodebytes
except ImportError:  # 3+
    from base64 import encodestring as encodebytes
_logger = logging.getLogger(__name__)

class ReportWithholdingsSuffered(models.Model):
    _name = "report.withholdings.suffered"
    _description = "Reporte retenciones sufridas"
    _inherit = ['mail.thread']
    _order = 'date_from desc'

    def _get_default_country(self):
        country = self.env['res.country'].search([('code', '=', 'AR')], limit=1)
        return country

    name = fields.Char(
        'Nombre',
        compute='_get_name'
    )
    date_from = fields.Date(
        string='Fecha Desde',
        required=True,
        readonly=True,
        states={'draft': [('readonly', False)]},
    )
    date_to = fields.Date(
        string='Fecha Hasta',
        required=True,
        readonly=True,
        states={'draft': [('readonly', False)]},
    )
    country_id = fields.Many2one('res.country', string='Country', default=_get_default_country)
    country_state = fields.Many2one('res.country.state','Provincia de Ret/Per', required=True)
    journal_withholdings_suffered = fields.Many2one('account.journal', 'Diario de Retenciones Sufridas')
    tax_withholdings_suffered = fields.Many2one('account.tax', 'Impuesto de Percepciones Sufridas',domain=[('type_tax_use', '=', 'purchase'),('tax_group_id.l10n_ar_tribute_afip_code','=','07')], )
    state = fields.Selection(
        [('draft', 'Borrador'), ('presented', 'Presentado'), ('cancel', 'Cancelado')],
        'State',
        required=True,
        default='draft'
    )
    reference = fields.Char(
        'Referencia',
    )
    invoice_ids = fields.One2many('invoice.suffered.line','withholdings_suffered_id','Facturas')
    payment_ids = fields.One2many('payment.suffered.line','withholdings_suffered_id','Pagos')
    company_id = fields.Many2one(
        'res.company',
        string='Empresa',
        required=True,
        readonly=True,
        states={'draft': [('readonly', False)]},
        default=lambda self: self.env[
            'res.company']._company_default_get('report.withholdings.suffered')
    )

    sifere_data_ret = fields.Text('Contenidos SIFERE Ret', default='')
    sifere_data_per = fields.Text('Contenidos SIFERE Per', default='')
    esicol_data_per = fields.Text('Contenidos E-SICOL Per', default='')
    
    #Retenciones
    @api.depends('sifere_data_ret')
    def _compute_files_ret(self):
        self.ensure_one()
        self.sifere_filename_ret = _('Sifere_ret_%s_%s.txt') % (str(self.date_from),str(self.date_to))
        self.sifere_file_ret = encodebytes(self.sifere_data_ret.encode('ISO-8859-1'))
    sifere_file_ret = fields.Binary('TXT SIFERE Ret',compute=_compute_files_ret)
    sifere_filename_ret = fields.Char('TXT SIFERE Ret',compute=_compute_files_ret) 
    
    #Percepciones
    @api.depends('sifere_data_per')
    def _compute_files_per(self):
        self.ensure_one()
        self.sifere_filename_per = _('Sifere_per_%s_%s.txt') % (str(self.date_from),str(self.date_to))
        self.sifere_file_per = encodebytes(self.sifere_data_per.encode('ISO-8859-1'))
    sifere_file_per = fields.Binary('TXT SIFERE Per',compute=_compute_files_per)
    sifere_filename_per = fields.Char('TXT SIFERE Per',compute=_compute_files_per)
    
    #Percepciones e-Sicol
    @api.depends('esicol_data_per')
    def _compute_files_esicol_per(self):
        self.ensure_one()
        self.esicol_filename_per = _('e-SICOL_%s_%s.txt') % (str(self.date_from),str(self.date_to))
        self.esicol_file_per = encodebytes(self.esicol_data_per.encode('ISO-8859-1'))
    esicol_file_per = fields.Binary('TXT e-SICOL Per',compute=_compute_files_esicol_per)
    esicol_filename_per = fields.Char('TXT e-SICOL Per',compute=_compute_files_esicol_per)

    def _get_name(self):
        for rec in self:
            name = _("Reporte de %s | %s hasta %s") % (
                rec.country_state.name or '',
                rec.date_from and fields.Date.from_string(
                    rec.date_from).strftime("%d-%m-%Y") or '',
                rec.date_to and fields.Date.from_string(
                    rec.date_to).strftime("%d-%m-%Y") or '',
            )
            if rec.reference:
                name = "%s - %s" % (name, rec.reference)
            rec.name = name

    def action_present(self):
        if not self.invoice_ids and not self.payment_ids:
            raise ValidationError('¡Está intentando presentar un Reporte sin Facturas ni pagos!')
        self.state = 'presented'

    def action_cancel(self):
        self.state = 'cancel'

    def action_to_draft(self):
        self.state = 'draft'

    #Metodo que dispara la captura de pagos y facturas
    def get_payment_invoice(self):
        self.get_payment_withholdings()
        self.get_invoice_withholdings()

    def get_payment_withholdings(self):
        if not self.journal_withholdings_suffered:
            return
        #Buscamos los pagos de clientes donde el diario de pago sea el Diario de retenciones sufridas seleccionadas
        payments = self.env['account.payment'].search([('company_id','=',self.company_id.id),('journal_id','=',self.journal_withholdings_suffered.id),('payment_type','=','inbound'),('state','not in',['cancel','draft']),('date','<=',self.date_to),('date','>=',self.date_from)])
        for i in self.payment_ids:
            i.unlink()
        for payment in payments:
            self.payment_ids = [(0, 0, {'payment' : payment.id})]

        self.set_txt_sifere_ret()
    
    def set_txt_sifere_ret(self):
        self.ensure_one()
        windows_line_ending = '\r' + '\n'

        string = ''
        for rec in self.payment_ids:
            #https://cpcecba.org.ar/media/download/noticias/anexoIV.pdf
            #Jurisdiccion
            string = string + self.get_jurisdiccion()
            #CUIT del Agente de Retencion
            string = string + rec.payment.partner_id.vat[0:2] + '-' + rec.payment.partner_id.vat[2:10] + '-' + rec.payment.partner_id.vat[-1]
            #Fecha de la Retencion
            string = string + str(rec.payment.date)[8:10] + '/' + str(rec.payment.date)[5:7] + '/' + str(rec.payment.date)[:4]
            #Número de la Sucursal 
            if rec.payment.payment_group_id.branch_op:
                string = string + rec.payment.payment_group_id.branch_op[:4].zfill(4)
            else:
                string = string + '0000'
            #Número de la Constancia 
            if rec.payment.ref:
                string = string + str(rec.payment.ref).zfill(16)
            else:
                string = string + '#SIN Nº DE CONSTANCIA, REEMPLACE ESTO POR EL CORRESPONDIENTE (16 CAMPOS)'
            #Tipo de Comprobante
            string = string + 'R'
            #Letra del comprobante 
            string = string + ' '
            #Número de Comprobante Original
            if rec.payment.payment_group_id.num_op:
                string = string + rec.payment.payment_group_id.num_op[:20].zfill(20)
            elif rec.payment.payment_group_id.communication:
                string = string + rec.payment.payment_group_id.communication[:20].zfill(20)
            else:
                string = string + '00000000000000000000'
            #Importe retenido
            try:
                if rec.payment.payment_group_id.matched_move_line_ids[0].move_id.l10n_latam_document_type_id.internal_type == 'credit_note':
                    string = string + '-' + (("%.2f"%rec.total_withholdings_suffered).zfill(10)).replace('.',',')
                else:
                    string = string +  (("%.2f"%rec.total_withholdings_suffered).zfill(11)).replace('.',',')
            except:
                string = string +  (("%.2f"%rec.total_withholdings_suffered).zfill(11)).replace('.',',')
            string = string + windows_line_ending
            
        self.sifere_data_ret = string


    def get_invoice_withholdings(self):
        if not self.tax_withholdings_suffered:
            return
        #Buscamos facturas de proveedor dentro del rango de fechas
        invoices_tmp = self.env['account.move'].search([('company_id','=',self.company_id.id),('date','>=',self.date_from),('date','<=',self.date_to),('state','=','posted'),('move_type','in',['in_invoice','in_refound'])])
        #Filtramos solo aquellas que contengan el impuesto seleccionado para el informe
        _logger.warning('****** Facturas: {0}'.format(invoices_tmp))
        invoices = []
        for it in invoices_tmp:
            for group in it.amount_by_group:
                if group[0] == self.tax_withholdings_suffered.tax_group_id.name:
                    invoices.append(it)
        #invoices = invoices.filtered(lambda r: str(json.loads(r.tax_totals_json)).find(self.tax_withholdings_suffered.tax_group_id.name) != -1)
        _logger.warning('****** Facturas filtradas: {0}'.format(invoices))
        if len(invoices) < 1:
            return

        for i in self.invoice_ids:
            i.unlink()
        for invoice in invoices:
            self.invoice_ids = [(0, 0, {'invoice' : invoice.id})]

        self.set_txt_sifere_per()
        self.set_txt_esicol_per()
    
    def set_txt_esicol_per(self):
        self.ensure_one()
        windows_line_ending = '\r' + '\n'

        string = ''
        for rec in self.invoice_ids:		
            #https://www.agip.gob.ar/impuestos/ingresos-brutos/contribuyentes-locales/aplicativo-esicol-preguntas-utiles
            #CUIT
            string = string + rec.invoice.partner_id.vat
            #Numero de factura
            i = 0
            for n in str(rec.invoice.name)[-8:]:
                if n == '0':
                    string = string + ' '
                    i += 1
                else:
                    string = string + str(rec.invoice.name)[-(8-i):]
                    break
            #Fecha de la Percepción
            string = string + str(rec.invoice.invoice_date)[:4] + str(rec.invoice.invoice_date)[5:7] + str(rec.invoice.invoice_date)[8:10]
            #Sucursal de factura
            i = 0
            for n in str(rec.invoice.name)[-14:-9]:
                if n == '0':
                    string = string + ' '
                    i += 1
                else:
                    string = string + str(rec.invoice.name)[(6+i):10]
                    break
            #Monto base de la Percepcion
            string = string +  ("%.2f"%rec.invoice.amount_untaxed).rjust(16," ")
            #Monto de la Percepcion
            string = string +  ("%.2f"%rec.total_withholdings_suffered).rjust(16," ")
            #Tipo de Comprobante
            if rec.invoice.l10n_latam_document_type_id.internal_type == 'invoice':
                string = string + 'F'
            elif rec.invoice.l10n_latam_document_type_id.internal_type == 'debit_note':
                string = string + 'D'
            elif rec.invoice.l10n_latam_document_type_id.internal_type == 'credit_note':
                string = string + 'C'
            #Letra del comprobante
            string = string + rec.invoice.l10n_latam_document_type_id.l10n_ar_letter

            string = string + windows_line_ending
            
        self.esicol_data_per = string
    
    def set_txt_sifere_per(self):
        self.ensure_one()
        windows_line_ending = '\r' + '\n'

        string = ''
        for rec in self.invoice_ids:
            #https://cpcecba.org.ar/media/download/noticias/anexoIV.pdf
            #Jurisdiccion
            string = string + self.get_jurisdiccion()
            #CUIT del Agente de Percepción
            string = string + rec.invoice.partner_id.vat[0:2] + '-' + rec.invoice.partner_id.vat[2:10] + '-' + rec.invoice.partner_id.vat[-1]
            #Fecha de la Percepción
            string = string + str(rec.invoice.invoice_date)[8:10] + '/' + str(rec.invoice.invoice_date)[5:7] + '/' + str(rec.invoice.invoice_date)[:4]
            #Número de la Sucursal 
            string = string + str(rec.invoice.l10n_latam_document_number)[1:5]
            #Número de la Constancia 
            string = string + str(rec.invoice.l10n_latam_document_number)[6:15]
            #Tipo de Comprobante
            if rec.invoice.l10n_latam_document_type_id.internal_type == 'invoice':
                string = string + 'F'
            elif rec.invoice.l10n_latam_document_type_id.internal_type == 'debit_note':
                string = string + 'D'
            elif rec.invoice.l10n_latam_document_type_id.internal_type == 'credit_note':
                string = string + 'C'
            #Letra del comprobante
            string = string + rec.invoice.l10n_latam_document_type_id.l10n_ar_letter
            #Importe Percibido
            if rec.invoice.l10n_latam_document_type_id.internal_type == 'credit_note':
                string = string + '-' + (("%.2f"%rec.total_withholdings_suffered).zfill(10)).replace('.',',')
            else:
                string = string +  (("%.2f"%rec.total_withholdings_suffered).zfill(11)).replace('.',',')

            string = string + windows_line_ending
            
        self.sifere_data_per = string

    def get_jurisdiccion(self):
        if self.country_state.code == 'C':#'Perc IIBB CABA'
            return '901'
        elif self.country_state.code == 'B':#'Perc IIBB ARBA'
            return '902'
        elif self.country_state.code == 'S':#'Perc IIBB Santa Fe'
            return '921'
        elif self.country_state.code == 'X':#'Perc IIBB Córdoba'
            return '904'
        elif self.country_state.code == 'M':#'Perc IIBB Mendoza'
            return '913'
        elif self.country_state.code == 'L':#'Perc IIBB La Pampa'
            return '911'
        elif self.country_state.code == 'Y':#'Perc IIBB Jujuy'
            return '910'
        elif self.country_state.code == 'A':#'Perc IIBB Salta'
            return '917'
        elif self.country_state.code == 'P':#'Perc IIBB Formosa'
            return '909'
        elif self.country_state.code == 'N':#'Perc IIBB Misiones'
            return '914'
        elif self.country_state.code == 'W':#'Perc IIBB Corrientes':
            return '905'
        elif self.country_state.code == 'E':#'Perc IIBB Entre Rios':
            return '908'
        elif self.country_state.code == 'J':#'Perc IIBB San Juan'
            return '918'
        elif self.country_state.code == 'D':#'Perc IIBB San Luis'
            return '919'
        elif self.country_state.code == 'K':#'Perc IIBB Catamarca'
            return '903'
        elif self.country_state.code == 'Q':#'Perc IIBB Neuquen'
            return '915'
        elif self.country_state.code == 'U':#'Perc IIBB Chubut'
            return '907'
        elif self.country_state.code == 'R':#'Perc IIBB Rio Negro'
            return '916'
        elif self.country_state.code == 'Z':#'Perc IIBB Santa Cruz'
            return '920'
        elif self.country_state.code == 'V':#'Perc IIBB Tierra del Fuego'
            return '923'
        elif self.country_state.code == 'T':#'Perc IIBB Tucuman'
            return '924'
        else:
            raise ValidationError('No se encontro un Nº de jurisdiccion para {0}'.format(self.country_state.name))

class PaymentSufferedLine(models.Model):
    _name = "payment.suffered.line"
    _description = "Linea de pago en retenciones sufridas"

    payment = fields.Many2one('account.payment','Pago')
    client = fields.Many2one('res.partner','Proveedor',related='payment.partner_id')
    currency_id = fields.Many2one(
        comodel_name='res.currency',
        string='Moneda',
        related='payment.currency_id'
    )
    total_withholdings_suffered = fields.Monetary('Retencion Sufrida', related='payment.amount', store = True)
    payment_ref = fields.Char('Nº Retención',related='payment.ref')
    payment_date = fields.Date('Fecha',related='payment.date')
    withholdings_suffered_id = fields.Many2one('report.withholdings.suffered', 'Report Id', ondelete='cascade')

class InvoiceSufferedLine(models.Model):
    _name = "invoice.suffered.line"
    _description = "Linea de facturas en percepciones sufridas"

    @api.depends("invoice")
    def _compute_total_withholdings_suffered(self):
        for rec in self:
            taxes = rec.invoice.amount_by_group
            per_tmp = 0
            for group in taxes:
                if group[0] == self.withholdings_suffered_id.tax_withholdings_suffered.tax_group_id.name:
                    per_tmp = per_tmp + group[1]
            if rec.invoice.currency_id.name != 'ARS':
                per_tmp = per_tmp * rec.invoice.currency_rate
            rec.total_withholdings_suffered = per_tmp

    invoice = fields.Many2one('account.move','Factura')
    withholdings_suffered_id = fields.Many2one('report.withholdings.suffered', 'Report Id', ondelete='cascade')

    supplier = fields.Many2one('res.partner','Proveedor',related='invoice.partner_id')
    invoice_date = fields.Date('Fecha',related='invoice.invoice_date')
    amount_total_signed = fields.Monetary('Total',related='invoice.amount_total_signed')
    currency_id = fields.Many2one(
        comodel_name='res.currency',
        string='Moneda',
        related='invoice.currency_id'
    )
    total_withholdings_suffered = fields.Monetary('Percepcion Sufrida', compute='_compute_total_withholdings_suffered', store = True)
