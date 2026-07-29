# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
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

# Código de jurisdicción SIFERE por código de provincia (res.country.state.code)
JURISDICCION_CODES = {
    'C': '901',  # Perc IIBB CABA
    'B': '902',  # Perc IIBB ARBA
    'S': '921',  # Perc IIBB Santa Fe
    'X': '904',  # Perc IIBB Córdoba
    'M': '913',  # Perc IIBB Mendoza
    'L': '911',  # Perc IIBB La Pampa
    'Y': '910',  # Perc IIBB Jujuy
    'A': '917',  # Perc IIBB Salta
    'P': '909',  # Perc IIBB Formosa
    'N': '914',  # Perc IIBB Misiones
    'W': '905',  # Perc IIBB Corrientes
    'E': '908',  # Perc IIBB Entre Rios
    'J': '918',  # Perc IIBB San Juan
    'D': '919',  # Perc IIBB San Luis
    'K': '903',  # Perc IIBB Catamarca
    'Q': '915',  # Perc IIBB Neuquen
    'U': '907',  # Perc IIBB Chubut
    'R': '916',  # Perc IIBB Rio Negro
    'Z': '920',  # Perc IIBB Santa Cruz
    'V': '923',  # Perc IIBB Tierra del Fuego
    'T': '924',  # Perc IIBB Tucuman
    'G': '922',  # Perc IIBB Santiago del Estero
    'H': '906',  # Perc IIBB Chaco
    'F': '912',  # Perc IIBB La Rioja
}


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
    )
    date_to = fields.Date(
        string='Fecha Hasta',
        required=True,
    )
    country_id = fields.Many2one('res.country', string='Country', default=_get_default_country)

    # --- Selección múltiple ---
    # Se pueden elegir varias provincias, varios diarios de retenciones y
    # varios impuestos de percepciones en un mismo reporte. El sistema
    # reconoce automáticamente a qué provincia corresponde cada
    # factura/pago mirando la Provincia configurada en el Impuesto o en el
    # Diario respectivo (l10n_ar_withholding_state_id), y arma un único
    # archivo combinado con todo.
    country_state_ids = fields.Many2many(
        'res.country.state',
        'report_withholdings_suffered_state_rel',
        'report_id', 'state_id',
        string='Provincias de Ret/Per',
        required=True,
    )
    journal_withholdings_suffered_ids = fields.Many2many(
        'account.journal',
        'report_withholdings_suffered_journal_rel',
        'report_id', 'journal_id',
        string='Diarios de Retenciones Sufridas',
    )
    tax_withholdings_suffered_ids = fields.Many2many(
        'account.tax',
        'report_withholdings_suffered_tax_rel',
        'report_id', 'tax_id',
        string='Impuestos de Percepciones Sufridas',
        domain=[
            ('type_tax_use', '=', 'purchase'),
            ('tax_group_id.l10n_ar_tribute_afip_code', '=', '07'),
        ],
    )

    state = fields.Selection(
        [('draft', 'Borrador'), ('presented', 'Presentado'), ('cancel', 'Cancelado')],
        'State',
        required=True,
        default='draft'
    )
    reference = fields.Char(
        'Referencia',
    )
    invoice_ids = fields.One2many('invoice.suffered.line', 'withholdings_suffered_id', 'Facturas')
    payment_ids = fields.One2many('payment.suffered.line', 'withholdings_suffered_id', 'Pagos')
    company_id = fields.Many2one(
        'res.company',
        string='Empresa',
        required=True,
        readonly=True,
        default=lambda self: self.env.company,
    )

    sifere_data_ret = fields.Text('Contenidos SIFERE Ret', default='')
    sifere_data_per = fields.Text('Contenidos SIFERE Per', default='')
    esicol_data_per = fields.Text('Contenidos E-SICOL Per', default='')

    # Retenciones
    @api.depends('sifere_data_ret')
    def _compute_files_ret(self):
        self.ensure_one()
        self.sifere_filename_ret = _('Sifere_ret_%s_%s.txt') % (str(self.date_from), str(self.date_to))
        self.sifere_file_ret = encodebytes(self.sifere_data_ret.encode('ISO-8859-1'))
    sifere_file_ret = fields.Binary('TXT SIFERE Ret', compute=_compute_files_ret)
    sifere_filename_ret = fields.Char('TXT SIFERE Ret', compute=_compute_files_ret)

    # Percepciones
    @api.depends('sifere_data_per')
    def _compute_files_per(self):
        self.ensure_one()
        self.sifere_filename_per = _('Sifere_per_%s_%s.txt') % (str(self.date_from), str(self.date_to))
        self.sifere_file_per = encodebytes(self.sifere_data_per.encode('ISO-8859-1'))
    sifere_file_per = fields.Binary('TXT SIFERE Per', compute=_compute_files_per)
    sifere_filename_per = fields.Char('TXT SIFERE Per', compute=_compute_files_per)

    # Percepciones e-Sicol
    @api.depends('esicol_data_per')
    def _compute_files_esicol_per(self):
        self.ensure_one()
        self.esicol_filename_per = _('e-SICOL_%s_%s.txt') % (str(self.date_from), str(self.date_to))
        self.esicol_file_per = encodebytes(self.esicol_data_per.encode('ISO-8859-1'))
    esicol_file_per = fields.Binary('TXT e-SICOL Per', compute=_compute_files_esicol_per)
    esicol_filename_per = fields.Char('TXT e-SICOL Per', compute=_compute_files_esicol_per)

    def _get_name(self):
        for rec in self:
            provincias = ', '.join(rec.country_state_ids.mapped('name')) or ''
            name = _("Reporte de %s | %s hasta %s") % (
                provincias,
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

    # Metodo que dispara la captura de pagos y facturas
    def get_payment_invoice(self):
        self.get_payment_withholdings()
        self.get_invoice_withholdings()

    def get_payment_withholdings(self):
        self.ensure_one()
        if not self.journal_withholdings_suffered_ids:
            self.payment_ids.unlink()
            return

        payments = self.env['account.payment'].search([
            ('company_id', '=', self.company_id.id),
            ('journal_id', 'in', self.journal_withholdings_suffered_ids.ids),
            ('payment_type', '=', 'inbound'),
            ('state', 'not in', ['cancel', 'draft']),
            ('date', '<=', self.date_to),
            ('date', '>=', self.date_from),
        ])

        self.payment_ids.unlink()
        lines = []
        for payment in payments:
            journal_state = payment.journal_id.l10n_ar_withholding_state_id
            if not journal_state:
                raise ValidationError(
                    _('El diario "%s" no tiene configurada una Provincia. '
                      'Configurala en Contabilidad > Configuración > Diarios '
                      'antes de generar el reporte.') % payment.journal_id.name
                )
            if journal_state not in self.country_state_ids:
                continue
            lines.append((0, 0, {
                'payment': payment.id,
                'country_state_id': journal_state.id,
            }))
        self.payment_ids = lines

        self.set_txt_sifere_ret()

    def set_txt_sifere_ret(self):
        self.ensure_one()
        windows_line_ending = '\r' + '\n'

        string = ''
        for rec in self.payment_ids:
            # https://cpcecba.org.ar/media/download/noticias/anexoIV.pdf
            # Jurisdiccion
            string = string + self.get_jurisdiccion(rec.country_state_id)
            # CUIT del Agente de Retencion
            string = string + rec.payment.partner_id.vat[0:2] + '-' + rec.payment.partner_id.vat[2:10] + '-' + rec.payment.partner_id.vat[-1]
            # Fecha de la Retencion
            string = string + str(rec.payment.date)[8:10] + '/' + str(rec.payment.date)[5:7] + '/' + str(rec.payment.date)[:4]
            # Número de la Sucursal
            if rec.payment.payment_group_id.branch_op:
                string = string + rec.payment.payment_group_id.branch_op[:4].zfill(4)
            else:
                string = string + '0000'
            # Número de la Constancia
            # En Odoo 19 account.payment ya no tiene el campo "ref": el dato
            # equivalente está en payment_reference o en el asiento (move_id.ref)
            if rec.payment.payment_reference:
                string = string + str(rec.payment.payment_reference).zfill(16)
            elif rec.payment.move_id and rec.payment.move_id.ref:
                string = string + str(rec.payment.move_id.ref).zfill(16)
            else:
                string = string + '#SIN Nº DE CONSTANCIA, REEMPLACE ESTO POR EL CORRESPONDIENTE (16 CAMPOS)'
            # Tipo de Comprobante
            string = string + 'R'
            # Letra del comprobante
            string = string + ' '
            # Número de Comprobante Original
            if rec.payment.payment_group_id.num_op:
                string = string + rec.payment.payment_group_id.num_op[:20].zfill(20)
            elif rec.payment.payment_group_id.communication:
                string = string + rec.payment.payment_group_id.communication[:20].zfill(20)
            else:
                string = string + '00000000000000000000'
            # Importe retenido
            try:
                if rec.payment.payment_group_id.matched_move_line_ids[0].move_id.l10n_latam_document_type_id.internal_type == 'credit_note':
                    string = string + '-' + (("%.2f" % rec.total_withholdings_suffered).zfill(10)).replace('.', ',')
                else:
                    string = string + (("%.2f" % rec.total_withholdings_suffered).zfill(11)).replace('.', ',')
            except Exception:
                string = string + (("%.2f" % rec.total_withholdings_suffered).zfill(11)).replace('.', ',')
            string = string + windows_line_ending

        self.sifere_data_ret = string

    def _invoice_has_tax_group(self, invoice, tax_group_name):
        """Busca si un impuesto del grupo indicado está aplicado en la
        factura. En Odoo 19, invoice.tax_totals ya viene como diccionario
        Python (antes era tax_totals_json, un string que había que parsear
        con json.loads)."""
        totals = invoice.tax_totals
        if not totals or 'groups_by_subtotal' not in totals:
            return False
        for subtotal_key in totals['groups_by_subtotal']:
            for line in totals['groups_by_subtotal'][subtotal_key]:
                if line.get('tax_group_name') == tax_group_name:
                    return True
        return False

    def get_invoice_withholdings(self):
        self.ensure_one()
        if not self.tax_withholdings_suffered_ids:
            self.invoice_ids.unlink()
            return

        invoices = self.env['account.move'].search([
            ('company_id', '=', self.company_id.id),
            ('date', '>=', self.date_from),
            ('date', '<=', self.date_to),
            ('state', '=', 'posted'),
            ('move_type', 'in', ['in_invoice', 'in_refund']),
        ])

        self.invoice_ids.unlink()
        lines = []
        for invoice in invoices:
            # Una factura puede tener más de un impuesto de percepción
            # seleccionado; se genera una línea por cada coincidencia.
            for tax in self.tax_withholdings_suffered_ids:
                if not self._invoice_has_tax_group(invoice, tax.tax_group_id.name):
                    continue
                tax_state = tax.l10n_ar_withholding_state_id
                if not tax_state:
                    raise ValidationError(
                        _('El impuesto "%s" no tiene configurada una '
                          'Provincia. Configurala en Contabilidad > '
                          'Configuración > Impuestos antes de generar el '
                          'reporte.') % tax.name
                    )
                if tax_state not in self.country_state_ids:
                    continue
                lines.append((0, 0, {
                    'invoice': invoice.id,
                    'tax_id': tax.id,
                    'country_state_id': tax_state.id,
                }))
        self.invoice_ids = lines

        self.set_txt_sifere_per()
        self.set_txt_esicol_per()

    def set_txt_esicol_per(self):
        self.ensure_one()
        windows_line_ending = '\r' + '\n'

        string = ''
        for rec in self.invoice_ids:
            # https://www.agip.gob.ar/impuestos/ingresos-brutos/contribuyentes-locales/aplicativo-esicol-preguntas-utiles
            # CUIT
            string = string + rec.invoice.partner_id.vat
            # Numero de factura
            i = 0
            for n in str(rec.invoice.name)[-8:]:
                if n == '0':
                    string = string + ' '
                    i += 1
                else:
                    string = string + str(rec.invoice.name)[-(8 - i):]
                    break
            # Fecha de la Percepción
            string = string + str(rec.invoice.invoice_date)[:4] + str(rec.invoice.invoice_date)[5:7] + str(rec.invoice.invoice_date)[8:10]
            # Sucursal de factura
            i = 0
            for n in str(rec.invoice.name)[-14:-9]:
                if n == '0':
                    string = string + ' '
                    i += 1
                else:
                    string = string + str(rec.invoice.name)[(6 + i):10]
                    break
            # Monto base de la Percepcion
            string = string + ("%.2f" % rec.invoice.amount_untaxed).rjust(16, " ")
            # Monto de la Percepcion
            string = string + ("%.2f" % rec.total_withholdings_suffered).rjust(16, " ")
            # Tipo de Comprobante
            if rec.invoice.l10n_latam_document_type_id.internal_type == 'invoice':
                string = string + 'F'
            elif rec.invoice.l10n_latam_document_type_id.internal_type == 'debit_note':
                string = string + 'D'
            elif rec.invoice.l10n_latam_document_type_id.internal_type == 'credit_note':
                string = string + 'C'
            # Letra del comprobante
            string = string + rec.invoice.l10n_latam_document_type_id.l10n_ar_letter

            string = string + windows_line_ending

        self.esicol_data_per = string

    def set_txt_sifere_per(self):
        self.ensure_one()
        windows_line_ending = '\r' + '\n'

        string = ''
        for rec in self.invoice_ids:
            # https://cpcecba.org.ar/media/download/noticias/anexoIV.pdf
            # Jurisdiccion
            string = string + self.get_jurisdiccion(rec.country_state_id)
            # CUIT del Agente de Percepción
            string = string + rec.invoice.partner_id.vat[0:2] + '-' + rec.invoice.partner_id.vat[2:10] + '-' + rec.invoice.partner_id.vat[-1]
            # Fecha de la Percepción
            string = string + str(rec.invoice.invoice_date)[8:10] + '/' + str(rec.invoice.invoice_date)[5:7] + '/' + str(rec.invoice.invoice_date)[:4]
            # Número de la Sucursal
            string = string + str(rec.invoice.l10n_latam_document_number)[1:5]
            # Número de la Constancia
            string = string + str(rec.invoice.l10n_latam_document_number)[6:15]
            # Tipo de Comprobante
            if rec.invoice.l10n_latam_document_type_id.internal_type == 'invoice':
                string = string + 'F'
            elif rec.invoice.l10n_latam_document_type_id.internal_type == 'debit_note':
                string = string + 'D'
            elif rec.invoice.l10n_latam_document_type_id.internal_type == 'credit_note':
                string = string + 'C'
            # Letra del comprobante
            string = string + rec.invoice.l10n_latam_document_type_id.l10n_ar_letter
            # Importe Percibido
            if rec.invoice.l10n_latam_document_type_id.internal_type == 'credit_note':
                string = string + '-' + (("%.2f" % rec.total_withholdings_suffered).zfill(10)).replace('.', ',')
            else:
                string = string + (("%.2f" % rec.total_withholdings_suffered).zfill(11)).replace('.', ',')

            string = string + windows_line_ending

        self.sifere_data_per = string

    def get_jurisdiccion(self, state):
        """Devuelve el código de jurisdicción SIFERE para la provincia
        recibida. Se recibe por parámetro porque un mismo reporte puede
        combinar varias provincias, y cada línea del archivo necesita el
        código de SU propia provincia, no la del reporte en general."""
        code = JURISDICCION_CODES.get(state.code)
        if not code:
            raise ValidationError('No se encontro un Nº de jurisdiccion para {0}'.format(state.name))
        return code


class PaymentSufferedLine(models.Model):
    _name = "payment.suffered.line"
    _description = "Linea de pago en retenciones sufridas"

    payment = fields.Many2one('account.payment', 'Pago')
    client = fields.Many2one('res.partner', 'Proveedor', related='payment.partner_id')
    currency_id = fields.Many2one(
        comodel_name='res.currency',
        string='Moneda',
        related='payment.currency_id'
    )
    total_withholdings_suffered = fields.Monetary('Retencion Sufrida', related='payment.amount', store=True)
    payment_ref = fields.Char("N° Retención", related="payment.name")
    payment_date = fields.Date('Fecha', related='payment.date')
    # Provincia reconocida automáticamente a partir del Diario del pago.
    country_state_id = fields.Many2one('res.country.state', string='Provincia')
    withholdings_suffered_id = fields.Many2one('report.withholdings.suffered', 'Report Id', ondelete='cascade')


class InvoiceSufferedLine(models.Model):
    _name = "invoice.suffered.line"
    _description = "Linea de facturas en percepciones sufridas"

    @api.depends("invoice", "tax_id")
    def _compute_total_withholdings_suffered(self):
        for rec in self:
            per_tmp = 0
            if rec.invoice and rec.tax_id:
                totals = rec.invoice.tax_totals or {}
                taxes = totals.get('groups_by_subtotal', {}).get('Importe libre de impuestos', [])
                for tax in taxes:
                    if tax['tax_group_name'] == rec.tax_id.tax_group_id.name:
                        per_tmp = per_tmp + tax['tax_group_amount']
                if rec.invoice.currency_id.name != 'ARS':
                    per_tmp = per_tmp * rec.invoice.currency_rate
            rec.total_withholdings_suffered = per_tmp

    invoice = fields.Many2one('account.move', 'Factura')
    # Impuesto de percepción puntual que hizo matchear esta factura (una
    # factura puede tener más de un impuesto seleccionado en el reporte;
    # se guarda cuál corresponde a esta línea para calcular el monto y la
    # provincia).
    tax_id = fields.Many2one('account.tax', string='Impuesto')
    # Provincia reconocida automáticamente a partir del Impuesto.
    country_state_id = fields.Many2one('res.country.state', string='Provincia')
    withholdings_suffered_id = fields.Many2one('report.withholdings.suffered', 'Report Id', ondelete='cascade')

    supplier = fields.Many2one('res.partner', 'Proveedor', related='invoice.partner_id')
    invoice_date = fields.Date('Fecha', related='invoice.invoice_date')
    amount_total_signed = fields.Monetary('Total', related='invoice.amount_total_signed')
    currency_id = fields.Many2one(
        comodel_name='res.currency',
        string='Moneda',
        related='invoice.currency_id'
    )
    total_withholdings_suffered = fields.Monetary('Percepcion Sufrida', compute='_compute_total_withholdings_suffered', store=True)
