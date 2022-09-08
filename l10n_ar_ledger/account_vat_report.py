# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
from odoo import models, fields, api, _
from odoo.exceptions import Warning, ValidationError
import time
from ast import literal_eval
import base64
base64.encodestring = base64.encodebytes
import re
import logging
_logger = logging.getLogger(__name__)

class AccountVatLedger(models.Model):

    _name = "account.vat.ledger"
    _description = "Account VAT Ledger"
    _inherit = ['mail.thread']
    _order = 'date_from desc'

    digital_skip_invoice_tests = fields.Boolean(
        string='Saltear tests a facturas?',
        help='If you skip invoice tests probably you will have errors when '
        'loading the files in digital.'
    )
    digital_skip_lines = fields.Char(
        string="Lista de lineas a saltear con los archivos del digital",
        help="Enter a list of lines, for eg '1, 2, 3'. If you skip some lines "
        "you would need to enter them manually"
    )
    REGDIGITAL_CV_ALICUOTAS = fields.Text(
        'REGDIGITAL_CV_ALICUOTAS',
        readonly=True,
    )
    REGDIGITAL_CV_COMPRAS_IMPORTACIONES = fields.Text(
        'REGDIGITAL_CV_COMPRAS_IMPORTACIONES',
        readonly=True,
    )
    REGDIGITAL_CV_CBTE = fields.Text(
        'REGDIGITAL_CV_CBTE',
        readonly=True,
    )
    REGDIGITAL_CV_CABECERA = fields.Text(
        'REGDIGITAL_CV_CABECERA',
        readonly=True,
    )
    digital_vouchers_file = fields.Binary(
        compute='_compute_digital_files',
        readonly=True
    )
    digital_vouchers_filename = fields.Char(
        compute='_compute_digital_files',
    )
    digital_aliquots_file = fields.Binary(
        compute='_compute_digital_files',
        readonly=True
    )
    digital_aliquots_filename = fields.Char(
        readonly=True,
        compute='_compute_digital_files',
    )
    digital_import_aliquots_file = fields.Binary(
        compute='_compute_digital_files',
        readonly=True
    )
    digital_import_aliquots_filename = fields.Char(
        readonly=True,
        compute='_compute_digital_files',
    )
    prorate_tax_credit = fields.Boolean()

    company_id = fields.Many2one(
        'res.company',
        string='Empresa',
        required=True,
        readonly=True,
        states={'draft': [('readonly', False)]},
        default=lambda self: self.env[
            'res.company']._company_default_get('account.vat.ledger')
    )
    type = fields.Selection(
        [('sale', 'Sale'), ('purchase', 'Purchase')],
        "Type",
        required=True
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
    journal_ids = fields.Many2many(
        'account.journal', 'account_vat_ledger_journal_rel',
        'vat_ledger_id', 'journal_id',
        string='Diarios',
        required=True,
        readonly=True,
        states={'draft': [('readonly', False)]},
    )
    presented_ledger = fields.Binary(
        "Presented Ledger",
        readonly=True,
        states={'draft': [('readonly', False)]},
    )
    presented_ledger_name = fields.Char(
    )
    state = fields.Selection(
        [('draft', 'Borrador'), ('presented', 'Presentado'), ('cancel', 'Cancelado')],
        'State',
        required=True,
        default='draft'
    )
    note = fields.Html(
        "Notas"
    )

    # Computed fields
    name = fields.Char(
        'Nombre',
        compute='_get_name'
    )
    reference = fields.Char(
        'Referencia',
    )
    invoice_ids = fields.Many2many(
        'account.move',
        string="Facturas",
        compute="_get_data"
    )

    def format_amount(self, amount, padding=15, decimals=2, invoice=False):
        # get amounts on correct sign despite conifiguration on taxes and tax
        # codes
        # TODO
        # remove this and perhups invoice argument (we always send invoice)
        # for invoice refund we dont change sign (we do this before)
        # if invoice:
        #     amount = abs(amount)
        #     if invoice.type in ['in_refund', 'out_refund']:
        #         amount = -1.0 * amount
        # Al final volvimos a agregar esto, lo necesitabamos por ej si se pasa
        # base negativa de no gravado
        # si se usa alguno de estos tipos de doc para rectificativa hay que pasarlos restando
        # seguramente para algunos otros tambien pero realmente no se usan y el digital tiende a depreciarse
        # y el uso de internal_type a cambiar
        if invoice and invoice.l10n_latam_document_type_id.code in ['39', '40', '41', '66', '99'] \
           and invoice.move_type in ['in_refund', 'out_refund']:
            amount = -amount

        if amount < 0:
            template = "-{:0>%dd}" % (padding - 1)
        else:
            template = "{:0>%dd}" % (padding)
        return template.format(
            int(round(abs(amount) * 10**decimals, decimals)))

    def _compute_digital_files(self):
        self.ensure_one()
        # segun vimos aca la afip espera "ISO-8859-1" en vez de utf-8
        # http://www.planillasutiles.com.ar/2015/08/
        # como-descargar-los-archivos-de.html
        if self.REGDIGITAL_CV_ALICUOTAS:
            self.digital_aliquots_filename = _('Alicuots_%s_%s.txt') % (
                self.type,
                self.date_to,
                # self.period_id.name
            )
            self.digital_aliquots_file = base64.encodestring(
                self.REGDIGITAL_CV_ALICUOTAS.encode('ISO-8859-1'))
        else:
            self.digital_aliquots_file = False
            self.digital_aliquots_filename = False
        if self.REGDIGITAL_CV_COMPRAS_IMPORTACIONES:
            self.digital_import_aliquots_filename = _('Import_Alicuots_%s_%s.txt') % (
                self.type,
                self.date_to,
                # self.period_id.name
            )
            self.digital_import_aliquots_file = base64.encodestring(
                self.REGDIGITAL_CV_COMPRAS_IMPORTACIONES.encode('ISO-8859-1'))
        else:
            self.digital_import_aliquots_file = False
            self.digital_import_aliquots_filename = False
        if self.REGDIGITAL_CV_CBTE:
            self.digital_vouchers_filename = _('Vouchers_%s_%s.txt') % (
                self.type,
                self.date_to,
                # self.period_id.name
            )
            self.digital_vouchers_file = base64.encodestring(
                self.REGDIGITAL_CV_CBTE.encode('ISO-8859-1'))
        else:
            self.digital_vouchers_file = False
            self.digital_vouchers_filename = False


    def compute_digital_data(self):
        alicuotas = self.get_REGDIGITAL_CV_ALICUOTAS()
        # sacamos todas las lineas y las juntamos
        lines = []
        for k, v in alicuotas.items():
            lines += v
        self.REGDIGITAL_CV_ALICUOTAS = '\r\n'.join(lines)

        impo_alicuotas = {}
        if self.type == 'purchase':
            impo_alicuotas = self.get_REGDIGITAL_CV_ALICUOTAS(impo=True)
            # sacamos todas las lineas y las juntamos
            lines = []
            for k, v in impo_alicuotas.items():
                lines += v
            self.REGDIGITAL_CV_COMPRAS_IMPORTACIONES = '\r\n'.join(lines)
        alicuotas.update(impo_alicuotas)
        self.get_REGDIGITAL_CV_CBTE(alicuotas)

    def get_partner_document_code(self, partner):
        # se exige cuit para todo menos consumidor final.
        # TODO si es mayor a 1000 habria que validar reportar
        # DNI, LE, LC, CI o pasaporte
        if partner.l10n_ar_afip_responsibility_type_id.code == '5':
            #return "{:0>2d}".format(partner.l10n_latam_identification_type_id.l10n_ar_afip_code)
            res = str(partner.l10n_latam_identification_type_id.l10n_ar_afip_code).zfill(2)
            return res
        return '80'

    @api.model
    def get_partner_document_number(self, partner):
        # se exige cuit para todo menos consumidor final.
        # TODO si es mayor a 1000 habria que validar reportar
        # DNI, LE, LC, CI o pasaporte
        #if partner.l10n_ar_afip_responsibility_type_id.l10n_ar_afip_code == '5':
        if partner.l10n_ar_afip_responsibility_type_id.code == '5':
            number = partner.vat or ''
            # por las dudas limpiamos letras
            number = re.sub("[^0-9]", "", number)
        else:
            #number = partner.cuit_required()
            number = partner.vat
        if number != False:
            return number.rjust(20, '0')
        else:
            raise ValidationError('El contacto ' + partner.name + ' no posee CUIT/CUIL o DNI. Agréguelo para poder generar el Libro de IVA.')

    @api.model
    def get_point_of_sale(self, invoice):
        if self.type == 'sale':
            return "{:0>5d}".format(invoice.journal_id.l10n_ar_afip_pos_number)
        else:
            return invoice.l10n_latam_document_number[:5]

    def action_see_skiped_invoices(self):
        invoices = self.get_digital_invoices(return_skiped=True)
        raise ValidationError(_('Facturas salteadas:\n%s') % ', '.join(invoices.mapped('display_name')))

    @api.constrains('digital_skip_lines')
    def _check_digital_skip_lines(self):
        for rec in self.filtered('digital_skip_lines'):
            try:
                res = literal_eval(rec.digital_skip_lines)
                if not isinstance(res, int):
                    assert isinstance(res, tuple)
            except Exception as e:
                raise ValidationError(_(
                    'Bad format for Skip Lines. You need to enter a list of '
                    'numbers like "1, 2, 3". This is the error we get: %s') % (
                        repr(e)))

    def get_digital_invoices(self, return_skiped=False):
        self.ensure_one()
        invoices = self.env['account.move'].search([
            ('l10n_latam_document_type_id.export_to_digital', '=', True),
            ('id', 'in', self.invoice_ids.ids)], order='invoice_date asc')
        if self.digital_skip_lines:
            skip_lines = literal_eval(self.digital_skip_lines)
            if isinstance(skip_lines, int):
                skip_lines = [skip_lines]
            to_skip = invoices.browse()
            for line in skip_lines:
                to_skip += invoices[line - 1]
            if return_skiped:
                return to_skip
            invoices -= to_skip
        return invoices

    def get_REGDIGITAL_CV_CBTE(self, alicuotas):
        self.ensure_one()
        res = []
        invoices = self.get_digital_invoices().filtered(
                lambda r: r.state != 'cancel')
        #if not self.digital_skip_invoice_tests:
        #    invoices.check_argentinian_invoice_taxes()
        if self.type == 'purchase':
            partners = invoices.mapped('commercial_partner_id').filtered(
                lambda r: r.l10n_latam_identification_type_id.l10n_ar_afip_code in (
                    False, 99) or not r.vat)
            if partners:
                raise ValidationError(_(
                    "On purchase digital, partner document type is mandatory "
                    "and it must be different from 99. "
                    "Partners: \r\n\r\n"
                    "%s") % '\r\n'.join(
                        ['[%i] %s' % (p.id, p.display_name)
                            for p in partners]))

        for inv in invoices:
            # si no existe la factura en alicuotas es porque no tienen ninguna
            #cant_alicuotas = len(alicuotas.get(inv.))
            cant_alicuotas = 0
            vat_taxes = []
            vat_exempt_base_amount = 0
            if inv.l10n_latam_document_type_id.code != '11' and inv.l10n_latam_document_type_id.code != '12' and inv.l10n_latam_document_type_id.code != '13':
                for invl in inv.invoice_line_ids:
                    for tax in invl.tax_ids:
                        if tax.tax_group_id.tax_type == 'vat' and tax.tax_group_id.l10n_ar_vat_afip_code not in ['1','2']:
                            if tax.id not in vat_taxes:
                                vat_taxes.append(tax.id)
                        if self.type == 'purchase':
                            if tax.amount == 0:
                                vat_exempt_base_amount += invl.price_subtotal

            cant_alicuotas = len(vat_taxes)

            currency_rate = inv.l10n_ar_currency_rate
            currency_code = inv.currency_id.l10n_ar_afip_code
            doc_number = int(inv.name.split('-')[2])

            row = [
                # Campo 1: Fecha de comprobante
                fields.Date.from_string(inv.invoice_date).strftime('%Y%m%d'),

                # Campo 2: Tipo de Comprobante.
                "{:0>3d}".format(int(inv.l10n_latam_document_type_id.code)),

                # Campo 3: Punto de Venta
                self.get_point_of_sale(inv),

                # Campo 4: Número de Comprobante
                # TODO agregar estos casos de uso
                # Si se trata de un comprobante de varias hojas, se deberá
                # informar el número de documento de la primera hoja, teniendo
                # en cuenta lo normado en el  artículo 23, inciso a), punto
                # 6., de la Resolución General N° 1.415, sus modificatorias y
                # complementarias.
                # En el supuesto de registrar de manera agrupada por totales
                # diarios, se deberá consignar el primer número de comprobante
                # del rango a considerar.
                "{:0>20d}".format(doc_number)
            ]

            if self.type == 'sale':
                # Campo 5: Número de Comprobante Hasta.
                # TODO agregar esto En el resto de los casos se consignará el
                # dato registrado en el campo 4
                row.append("{:0>20d}".format(doc_number))
            else:
                # Campo 5: Despacho de importación
                if inv.l10n_latam_document_type_id.code == '66':
                    row.append(
                        (inv.l10n_latam_document_number or inv.number or '').rjust(
                            16, '0'))
                else:
                    row.append(''.rjust(16, ' '))

            row += [
                # Campo 6: Código de documento del comprador.
                self.get_partner_document_code(inv.commercial_partner_id),

                # Campo 7: Número de Identificación del comprador
                self.get_partner_document_number(inv.commercial_partner_id),

                # Campo 8: Apellido y Nombre del comprador.
                inv.commercial_partner_id.name.ljust(30, ' ')[:30],
                # inv.commercial_partner_id.name.encode(
                #     'ascii', 'replace').ljust(30, ' ')[:30],

                # Campo 9: Importe Total de la Operación.
                #self.format_amount(inv.cc_amount_total, invoice=inv),
                self.format_amount(inv.amount_total, invoice=inv),

                # Campo 10: Importe total de conceptos que no integran el
                # precio neto gravado
                #self.format_amount(
                #    inv.cc_vat_untaxed_base_amount, invoice=inv),
                #self.format_amount(
                #    inv.vat_untaxed_base_amount, invoice=inv),
            ]
            #if inv.id == 10:
            #    raise ValidationError('estamos aca %s'%(inv.l10n_latam_tax_ids[1].tax_line_id))

            if self.type == 'sale':
                row += [
                    # Campo 10: Importe total de conceptos que no integran el
                    # precio neto gravado
                    self.format_amount(
                        inv.vat_untaxed_base_amount, invoice=inv),
                    # Campo 11: Percepción a no categorizados
                    self.format_amount(
                        sum(inv.move_tax_ids.filtered(lambda r: (
                            r.tax_id.tax_group_id.tax_type == 'withholding' and
                            r.tax_id.tax_group_id.tax == 'vat' and
                            r.tax_id.tax_group_id.l10n_ar_tribute_afip_code \
                            == '01')
                        ).mapped('tax_amount')), invoice=inv),

                    # Campo 12: Importe de operaciones exentas
                    #self.format_amount(
                    #    inv.vat_exempt_base_amount, invoice=inv),
                    self.format_amount(
                        inv.vat_untaxed_base_amount, invoice=inv),
                    # Campo 13: Importe de percepciones o pagos a cuenta de
                    # impuestos nacionales
                    self.format_amount(
                        sum(inv.move_tax_ids.filtered(lambda r: (
                            r.tax_id.tax_group_id.tax_type == 'withholding' and
                            r.tax_id.tax_group_id.tax != 'vat' and
                            r.tax_id.tax_group_id.l10n_ar_tribute_afip_code == '01')
                        ).mapped('tax_amount')), invoice=inv),

                    # Campo 14: Importe de percepciones de ingresos brutos
                    self.format_amount(
                        sum(inv.move_tax_ids.filtered(lambda r: (
                            r.tax_id.tax_group_id.tax_type == 'withholding' and
                            r.tax_id.tax_group_id.l10n_ar_tribute_afip_code \
                            == '02')
                        ).mapped('tax_amount')), invoice=inv),

                ]
            else:
                type_internal = 'debit'
                if inv.l10n_latam_document_type_id.internal_type == 'credit_note':
                    type_internal = 'credit'
                #if inv.id == 200:
                #    raise ValidationError('estamos aca %s'%(inv.l10n_latam_tax_ids[1].tax_ids))
                row += [
                    # Campo 10: Importe total de conceptos que no integran el
                    # precio neto gravado
                    self.format_amount(
                        vat_exempt_base_amount, invoice=inv),
                    # Campo 11: Importe de operaciones exentas
                    #self.format_amount(
                    #    inv.vat_exempt_base_amount, invoice=inv),
                    self.format_amount(
                        inv.vat_untaxed_base_amount, invoice=inv),

                    # Campo 12: Importe de percepciones o pagos a cuenta del
                    # Impuesto al Valor Agregado
                    self.format_amount(
                        sum(inv.move_tax_ids.filtered(lambda r: (
                            r.tax_id.tax_group_id.tax_type == 'withholding' and
                            r.tax_id.tax_group_id.tax == 'vat' and
                            r.tax_id.tax_group_id.l10n_ar_tribute_afip_code == '01' or
                            r.tax_id.tax_group_id.l10n_ar_tribute_afip_code == '06'
                            )
                        ).mapped(
                            'tax_amount')), invoice=inv),
                    # Campo 13: Importe de percepciones o pagos a cuenta de
                    # impuestos nacionales
                    self.format_amount(
                        sum(inv.move_tax_ids.filtered(lambda r: (
                            r.tax_id.tax_group_id.tax_type == 'withholding' and
                            r.tax_id.tax_group_id.tax != 'vat' and
                            r.tax_id.tax_group_id.l10n_ar_tribute_afip_code == '01')
                        ).mapped('tax_amount')), invoice=inv),

                    # Campo 14: Importe de percepciones de ingresos brutos
                        self.format_amount(
                            sum(inv.l10n_latam_tax_ids.filtered(lambda r: (
                                r.tax_line_id.tax_group_id.tax_type == 'withholdings' and
                                r.tax_line_id.tax_group_id.l10n_ar_tribute_afip_code \
                                == '07')
                            ).mapped(type_internal)), invoice=inv),
                ]

            row += [
                # Campo 15: Importe de percepciones de impuestos municipales
                self.format_amount(
                    sum(inv.move_tax_ids.filtered(lambda r: (
                        r.tax_id.tax_group_id.tax_type == 'withholding' and
                        r.tax_id.tax_group_id.l10n_ar_tribute_afip_code == '03')
                    ).mapped('tax_amount')), invoice=inv),

                # Campo 16: Importe de impuestos internos
                self.format_amount(
                    sum(inv.move_tax_ids.filtered(
                        lambda r: r.tax_id.tax_group_id.l10n_ar_tribute_afip_code \
                        == '04'
                    ).mapped('tax_amount')), invoice=inv),

                # Campo 17: Código de Moneda
                str(currency_code),

                # Campo 18: Tipo de Cambio
                # nueva modalidad de currency_rate
                self.format_amount(currency_rate, padding=10, decimals=6),

                # Campo 19: Cantidad de alícuotas de IVA
                str(cant_alicuotas),

                # Campo 20: Código de operación.
                # WARNING. segun la plantilla es 0 si no es ninguna
                # TODO ver que no se informe un codigo si no correpsonde,
                # tal vez da error
                # TODO ADIVINAR E IMPLEMENTAR, VA A DAR ERROR
                #inv.fiscal_position_id.afip_code or '0',
                '0',
            ]

            if self.type == 'sale':
                row += [
                    # Campo 21: Otros Tributos
                    self.format_amount(
                        sum(inv.move_tax_ids.filtered(
                            lambda r: r.tax_id.tax_group_id.l10n_ar_tribute_afip_code \
                            == '99'
                        ).mapped('tax_amount')), invoice=inv),

                    # Campo 22: vencimiento comprobante (no figura en
                    # instructivo pero si en aplicativo) para tique y factura
                    # de exportacion no se informa, tmb para algunos otros
                    # pero que tampoco tenemos implementados
                    (inv.l10n_latam_document_type_id.code in [
                        '19', '20', '21', '16', '55', '81', '82', '83',
                        '110', '111', '112', '113', '114', '115', '116',
                        '117', '118', '119', '120', '201', '202', '203',
                        '206', '207', '208', '211', '212', '213'] and
                        '00000000' or
                        fields.Date.from_string(
                            inv.invoice_date_due or inv.invoice_date).strftime(
                            '%Y%m%d')),
                ]
            else:
                # Campo 21: Crédito Fiscal Computable
                if self.prorate_tax_credit:
                    if self.prorate_type == 'global':
                        row.append(self.format_amount(0, invoice=inv))
                    else:
                        # row.append(self.format_amount(0))
                        # por ahora no implementado pero seria lo mismo que
                        # sacar si prorrateo y que el cliente entre en el digital
                        # en cada comprobante y complete cuando es en
                        # credito fiscal computable
                        raise ValidationError(_(
                            'Para utilizar el prorrateo por comprobante:\n'
                            '1) Exporte los archivos sin la opción "Proratear '
                            'Crédito de Impuestos"\n2) Importe los mismos '
                            'en el aplicativo\n3) En el aplicativo de afip, '
                            'comprobante por comprobante, indique el valor '
                            'correspondiente en el campo "Crédito Fiscal '
                            'Computable"'))
                else:
                    vat_taxes = self.env['account.move.line']
                    imp_neto = 0
                    imp_liquidado = 0
                    for mvl_tax in inv.l10n_latam_tax_ids:
                        #raise ValidationError('estamos aca %s %s %s'%(inv,mvl_tax.tax_group_id.l10n_ar_vat_afip_code + 'X',mvl_tax.tax_group_id.tax_type))
                        #if not mvl_tax.l10n_latam_tax_ids:
                        #    continue
                        tax_group_id = mvl_tax.tax_group_id
                        #if tax_group_id.tax_type == 'vat' and (tax_group_id.l10n_ar_vat_afip_code == 3 or (tax_group_id.l10n_ar_vat_afip_code in [4, 5, 6, 8, 9])):
                        if tax_group_id.tax_type == 'vat':
                            imp_neto += mvl_tax.tax_base_amount
                            imp_liquidado += mvl_tax.price_subtotal
                    #if inv.id == 904:
                    #    raise ValidationError('%s %s %s %s %s'%(inv.amount_total,inv.amount_untaxed,imp_neto,imp_liquidado,inv.id))
                    row.append(self.format_amount(round(imp_liquidado,2), invoice=inv))
                    # row.append(self.format_amount(
                        #    inv.vat_amount, invoice=inv))

                row += [
                    # Campo 22: Otros Tributos
                    #self.format_amount(
                    #    sum(inv.l10n_latam_tax_ids.filtered(lambda r: (
                    #        r.l10n_latam_tax_ids[0].tax_group_id.tax_type \
                    #        == 'others')).mapped(
                    #        'cc_amount')), invoice=inv),
                    self.format_amount(0),
                        #sum(inv.l10n_latam_tax_ids.filtered(lambda r: (
                        #    r.l10n_latam_tax_ids[0].tax_group_id.tax_type \
                        #    == 'others')).mapped(
                        #    'cc_amount')), invoice=inv),

                    # TODO implementar estos 3
                    # Campo 23: CUIT Emisor / Corredor
                    # Se informará sólo si en el campo "Tipo de Comprobante" se
                    # consigna '033', '058', '059', '060' ó '063'. Si para
                    # éstos comprobantes no interviene un tercero en la
                    # operación, se consignará la C.U.I.T. del informante. Para
                    # el resto de los comprobantes se completará con ceros
                    self.format_amount(0, padding=11, invoice=inv),

                    # Campo 24: Denominación Emisor / Corredor
                    ''.ljust(30, ' ')[:30],

                    # Campo 25: IVA Comisión
                    # Si el campo 23 es distinto de cero se consignará el
                    # importe del I.V.A. de la comisión
                    self.format_amount(0, invoice=inv),
                ]
            res.append(''.join(row))
        self.REGDIGITAL_CV_CBTE = '\r\n'.join(res)

    def get_tax_row(self, invoice, base, code, tax_amount, impo=False):
        self.ensure_one()
        inv = invoice
        if self.type == 'sale':
            doc_number = int(inv.name.split('-')[2])
            row = [
                # Campo 1: Tipo de Comprobante
                "{:0>3d}".format(int(inv.l10n_latam_document_type_id.code)),

                # Campo 2: Punto de Venta
                self.get_point_of_sale(inv),

                # Campo 3: Número de Comprobante
                "{:0>20d}".format(doc_number),

                # Campo 4: Importe Neto Gravado
                self.format_amount(base, invoice=inv),

                # Campo 5: Alícuota de IVA.
                str(code).rjust(4, '0'),

                # Campo 6: Impuesto Liquidado.
                self.format_amount(tax_amount, invoice=inv),
            ]
        elif impo:
            row = [
                # Campo 1: Despacho de importación.
                (inv.document_number or inv.number or '').rjust(16, '0'),

                # Campo 2: Importe Neto Gravado
                self.format_amount(base, invoice=inv),

                # Campo 3: Alícuota de IVA
                str(code).rjust(4, '0'),

                # Campo 4: Impuesto Liquidado.
                self.format_amount(tax_amount, invoice=inv),
            ]
        else:
            doc_number = int(inv.name.split('-')[2])
            #raise ValidationError('estamos aca %s'%(doc_number))
            row = [
                # Campo 1: Tipo de Comprobante
                #"{:0>3d}".format(int(inv.document_type_id.code)),
                str(inv.l10n_latam_document_type_id.code).zfill(3),

                # Campo 2: Punto de Venta
                #self.get_point_of_sale(inv),
                "{:0>5d}".format(int(inv.l10n_latam_document_number[:inv.l10n_latam_document_number.find('-')])),

                # Campo 3: Número de Comprobante
                #"{:0>19d}".format(int(inv.l10n_latam_document_number[inv.l10n_latam_document_number.find('-')+1:])),
                "{:0>20d}".format(doc_number),

                ## Campo 4: Código de documento del vendedor
                self.get_partner_document_code(
                    inv.commercial_partner_id),

                ## Campo 5: Número de identificación del vendedor
                self.get_partner_document_number(
                    inv.commercial_partner_id),

                # Campo 4: Importe Neto Gravado
                self.format_amount(base, invoice=inv),

                # Campo 5: Alícuota de IVA.
                str(code).rjust(4, '0'),

                # Campo 6: Impuesto Liquidado.
                self.format_amount(tax_amount, invoice=inv),
            ]
        return row

    def get_REGDIGITAL_CV_ALICUOTAS(self, impo=False):
        """
        Devolvemos un dict para calcular la cantidad de alicuotas cuando
        hacemos los comprobantes
        """
        self.ensure_one()
        res = {}
        # only vat taxes with codes 3, 4, 5, 6, 8, 9
        # segun: http://contadoresenred.com/regimen-de-informacion-de-
        # compras-y-ventas-rg-3685-como-cargar-la-informacion/
        # empezamos a contar los codigos 1 (no gravado) y 2 (exento)
        # si no hay alicuotas, sumamos una de esta con 0, 0, 0 en detalle
        # usamos mapped por si hay afip codes duplicados (ej. manual y
        # auto)
        if impo:
            invoices = self.get_digital_invoices().filtered(
                lambda r: r.l10n_latam_document_type_id.code == '66' and r.state != 'cancel')
        else:
            invoices = self.get_digital_invoices().filtered(
                lambda r: r.l10n_latam_document_type_id.code != '66' and r.l10n_latam_document_type_id.code != '11' and r.l10n_latam_document_type_id.code != '12' and r.l10n_latam_document_type_id.code != '13' and r.state != 'cancel')

        for inv in invoices:
            lines = []
            is_zero = inv.currency_id.is_zero

            vat_taxes = self.env['account.move.tax']
            for mvl_tax in inv.move_tax_ids:
                tax_group_id = mvl_tax.tax_id.tax_group_id
                if tax_group_id.tax_type == 'vat' and tax_group_id.l10n_ar_vat_afip_code in ['1','2','3', '4', '5', '6', '8', '9']:
                    vat_taxes += mvl_tax

            for mvl_tax in inv.line_ids:
                if mvl_tax.tax_ids and mvl_tax.tax_ids[0].tax_group_id.l10n_ar_vat_afip_code == '3':
                    lines.append(''.join(self.get_tax_row(
                        inv, 0.0, 3, 0.0, impo=impo)))

            if not vat_taxes and inv.move_tax_ids.filtered(
                    lambda r: r.tax_id.tax_group_id.tax_type == 'vat' and r.tax_id.tax_group_id.l10n_ar_vat_afip_code):
                lines.append(''.join(self.get_tax_row(
                    inv, 0.0, 3, 0.0, impo=impo)))

            for afip_code in vat_taxes.mapped('tax_id.tax_group_id.l10n_ar_vat_afip_code'):
                taxes = vat_taxes.filtered(lambda x: x.tax_id.tax_group_id.l10n_ar_vat_afip_code == afip_code)
                imp_neto = sum(taxes.mapped('tax_amount'))
                imp_liquidado = sum(taxes.mapped('base_amount'))
                lines.append(''.join(self.get_tax_row(
                    inv,
                    imp_neto,
                    afip_code,
                    imp_liquidado,
                    impo=impo,
                )))
            res[inv] = lines
        return res

    def _get_data(self):

        if self.type == 'sale':
            invoices_domain = [
                # cancel invoices with internal number are invoices
                ('state', '!=', 'draft'),
                ('l10n_latam_document_number', '!=', False),
                #('internal_number', '!=', False),
                ('journal_id', 'in', self.journal_ids.ids),
                ('date', '>=', self.date_from),
                ('date', '<=', self.date_to),
            ]
            invoices = self.env['account.move'].search(
                invoices_domain,
                order='invoice_date asc, document_number asc, id asc')
        else:
            invoices_domain = [
                # cancel invoices with internal number are invoices
                ('state', '!=', 'draft'),
                ('name', '!=', False),
                # ('internal_number', '!=', False),
                ('journal_id', 'in', self.journal_ids.ids),
                ('date', '>=', self.date_from),
                ('date', '<=', self.date_to),
            ]
            invoices = self.env['account.move'].search(
                invoices_domain,
                order='invoice_date asc, name asc, id asc')

        self.invoice_ids = invoices

    def _get_name(self):
        for rec in self:
            if rec.type == 'sale':
                ledger_type = _('Ventas')
            elif rec.type == 'purchase':
                ledger_type = _('Compras')

            lang = self.env['res.lang']

            name = _("%s Libro de IVA %s - %s") % (
                ledger_type,
                rec.date_from and fields.Date.from_string(
                    rec.date_from).strftime("%d-%m-%Y") or '',
                rec.date_to and fields.Date.from_string(
                    rec.date_to).strftime("%d-%m-%Y") or '',
            )
            if rec.reference:
                name = "%s - %s" % (name, rec.reference)
            rec.name = name

    @api.onchange('company_id')
    def change_company(self):
        now = time.strftime('%Y-%m-%d')
        company_id = self.company_id.id
        domain = [('company_id', '=', company_id),
                  ('date_start', '<', now), ('date_stop', '>', now)]
        # fiscalyears = self.env['account.fiscalyear'].search(domain, limit=1)
        # self.fiscalyear_id = fiscalyears
        if self.type == 'sale':
            domain = [('type', '=', 'sale')]
        elif self.type == 'purchase':
            domain = [('type', '=', 'purchase')]
        domain += [
            ('l10n_latam_use_documents', '=', True),
            ('company_id', '=', self.company_id.id),
        ]
        journals = self.env['account.journal'].search(domain)
        self.journal_ids = journals

    def action_present(self):
        if not self.invoice_ids:
            raise ValidationError('¡Está intentando presentar un Libro IVA sin Facturas!')
        self.state = 'presented'

    def action_cancel(self):
        self.state = 'cancel'

    def action_to_draft(self):
        self.state = 'draft'

class L10nLatamDocumentType(models.Model):
    _inherit = "l10n_latam.document.type"

    export_to_digital = fields.Boolean(
        help='Seleccionar para que este documento sea importado en el Libro IVA Digital'
    )
