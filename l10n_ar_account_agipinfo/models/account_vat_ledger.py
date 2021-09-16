##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from ast import literal_eval
import base64
import logging
import re
_logger = logging.getLogger(__name__)


class AccountVatLedger(models.Model):
    _inherit = "account.vat.ledger"

    REGAGIP_CV_CBTE = fields.Text(
        'REGAGIP_CV_CBTE',
        readonly=True,
    )
    agip_vouchers_file = fields.Binary(
        compute='_compute_agip_files',
        readonly=True
    )
    agip_vouchers_filename = fields.Char(
        compute='_compute_agip_files',
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
           and invoice.type in ['in_refund', 'out_refund']:
            amount = -amount

        if amount < 0:
            template = "-{:0>%dd}" % (padding - 1)
        else:
            template = "{:0>%dd}" % (padding)
        return template.format(
            int(round(abs(amount) * 10**decimals, decimals)))

    def _compute_agip_files(self):
        self.ensure_one()
        # segun vimos aca la afip espera "ISO-8859-1" en vez de utf-8
        # http://www.planillasutiles.com.ar/2015/08/
        # como-descargar-los-archivos-de.html
        if self.REGAGIP_CV_CBTE:
            self.agip_vouchers_filename = _('AGIP_%s_%s.txt') % (
                self.type,
                self.date_to,
                # self.period_id.name
            )
            self.agip_vouchers_file = base64.encodestring(
                self.REGAGIP_CV_CBTE.encode('utf8'))
        else:
            self.agip_vouchers_file = None 
            self.agip_vouchers_filename = None


    def compute_agip_data(self):
        # sacamos todas las lineas y las juntamos
        lines = []
        self.ensure_one()
        for invoice in self.invoice_ids:
            if invoice.state != 'posted':
                continue
            move_tax = None
            vat_amount = 0
            if invoice.currency_id.id == invoice.company_id.currency_id.id:
                currency_rate = 1
            else:
                currency_rate = invoice.l10n_ar_currency_rate
            for mvt in invoice.move_tax_ids:
                if mvt.tax_id.tax_group_id.tax_type == 'withholdings':
                    move_tax = mvt
                if mvt.tax_id.tax_group_id.tax_type == 'vat':
                    vat_amount += mvt.tax_amount
            if not move_tax:
                continue
            v = ''
            # Campo 1 - tipo de operacion
            v = '2'
            # Campo 2 - Norma
            v+= '014'
            # Campo 3 - Fecha percepcion
            v+= invoice.invoice_date.strftime('%d/%m/%Y')
            # Campo 4 - Tipo Comprobante
            v+= '01'
            # Campo 5 - 
            if invoice.partner_id.l10n_ar_afip_responsibility_type_id.code == '4':
                v+= 'C'
            else:
                if invoice.l10n_latam_document_type_id.code == '1':
                    v+= 'A'
                elif invoice.l10n_latam_document_type_id.code == '6':
                    v+= 'B'
            # Campo 6
            inv_number = invoice.name[5:].replace('-','')
            v+= inv_number.zfill(16)
            # Campo 7
            v+= invoice.invoice_date.strftime('%d/%m/%Y')
            # Campo 8
            value = int(mvt.tax_amount)
            v+= str(value).zfill(16)
            # Campo 9
            v+= ' ' * 16
            # Campo 10
            v+= '3'
            # Campo 11
            v+= invoice.partner_id.vat.zfill(11)
            # Campo 12
            if invoice.partner_id.gross_income_type == 'local':
                v+= '1'
            elif invoice.partner_id.gross_income_type == 'multilateral':
                v+= '2'
            elif invoice.partner_id.gross_income_type == 'no_liquida':
                v+= '4'
            else:
                v+= '4'
            # Campo 13
            v+= str(invoice.partner_id.gross_income_number).zfill(11)
            # Campo 14
            if invoice.partner_id.l10n_ar_afip_responsibility_type_id.code == '1':
                v+= '1'
            elif invoice.partner_id.l10n_ar_afip_responsibility_type_id.code == '4':
                v+= '3'
            else:
                v+= '4'
            # Campo 15
            lastname = invoice.partner_id.name[:30]
            lastname = lastname.ljust(30)
            v+= lastname
            # Campo 16
            v+= '0'.zfill(16)
            # Campo 17
            #vat_amount = int(vat_amount * 100)
            v+= str(round(vat_amount * currency_rate,2)).replace(',','.').zfill(16)
            # Campo 18
            base_amount = mvt.base_amount * currency_rate
            v+= str(round(base_amount,2)).replace('.',',').zfill(16)
            # Campo 19
            alicuota = (mvt.tax_amount / mvt.base_amount) * currency_rate
            v+= str(round(alicuota,2)).replace('.',',').zfill(5)
            # Campo 20
            tax_amount = round(mvt.tax_amount  * currency_rate,2)
            v+= str(tax_amount).replace('.',',').zfill(16)
            v+= str(tax_amount).replace(',','.').zfill(16)
            # Campo 21
            v+= ' ' 
            # Campo 22
            v+= ' '*9

            lines.append(v)
        self.REGAGIP_CV_CBTE = '\r\n'.join(lines)


