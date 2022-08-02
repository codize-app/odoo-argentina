# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, RedirectWarning
import logging
import datetime
from datetime import datetime, timedelta, date
import json
try:
    from base64 import encodebytes
except ImportError:  # 3+
    from base64 import encodestring as encodebytes

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    def _compute_price_subtotal_vat(self):
        for line in self:
            if line.tax_ids:
                for tax_id in line.tax_ids:
                    if tax_id.tax_group_id.tax_type == 'vat':
                        line.price_subtotal_vat = line.price_subtotal * ( 1 + tax_id.amount / 100 )
                    else:
                        line.price_subtotal_vat = line.price_subtotal
            else:
                line.price_subtotal_vat = 0


    price_subtotal_vat = fields.Float('price_subtotal_vat',compute=_compute_price_subtotal_vat)

class AccountMove(models.Model):
    _inherit = 'account.move'

    def _compute_json_qr(self):
        for rec in self:
            dict_invoice = ''
            if rec.move_type in ['out_invoice','out_refund'] and rec.state == 'posted' and rec.afip_auth_code != '':
                try:
                    dict_invoice = {
                        "ver": 1,
                        "fecha": str(rec.invoice_date),
                        "cuit": int(rec.company_id.partner_id.vat),
                        "ptoVta": rec.journal_id.l10n_ar_afip_pos_number,
                        "tipoCmp": int(rec.l10n_latam_document_type_id.code),
                        "nroCmp": int(rec.name.split('-')[2]),
                        "importe": rec.amount_total,
                        "moneda": rec.currency_id.l10n_ar_afip_code,
                        "ctz": rec.l10n_ar_currency_rate,
                        "tipoDocRec": int(rec.partner_id.l10n_latam_identification_type_id.l10n_ar_afip_code),
                        "nroDocRec": int(rec.partner_id.vat),
                        "tipoCodAut": 'E',
                        "codAut": rec.afip_auth_code,
                        }
                except:
                    dict_invoice = 'ERROR'
                    pass
                res = str(dict_invoice).replace("\n", "")
            else:
                res = 'N/A'
            rec.json_qr = res
            if type(dict_invoice) == dict:
                enc = res.encode()
                b64 = encodebytes(enc)
                b64 = encodebytes(json.dumps(dict_invoice, indent=None).encode('ascii')).decode('ascii')
                b64 = str(b64).replace("\n", "")
                rec.texto_modificado_qr = 'https://www.afip.gob.ar/fe/qr/?p=' + str(b64)
            else:
                rec.texto_modificado_qr = 'https://www.afip.gob.ar/fe/qr/?ERROR'
    
    json_qr = fields.Char("JSON QR AFIP",compute=_compute_json_qr)
    texto_modificado_qr = fields.Char('Texto Modificado QR',compute=_compute_json_qr)

class AccountJournal(models.Model):
    _inherit = "account.journal"

    def _get_journal_letter(self, counterpart_partner=False):
        """ Regarding the AFIP responsibility of the company and the type of journal (sale/purchase), get the allowed
        letters. Optionally, receive the counterpart partner (customer/supplier) and get the allowed letters to work
        with him. This method is used to populate document types on journals and also to filter document types on
        specific invoices to/from customer/supplier
        """
        self.ensure_one()
        letters_data = {
            'issued': {
                '1': ['A', 'B', 'E', 'M'],
                '3': [],
                '4': ['C'],
                '5': [],
                '6': ['A','C', 'E'],
                '9': ['I'],
                '10': [],
                '13': ['C', 'E'],
            },
            'received': {
                '1': ['A', 'B', 'C', 'M', 'I'],
                '3': ['B', 'C', 'I'],
                '4': ['B', 'C', 'I'],
                '5': ['B', 'C', 'I'],
                '6': ['A', 'C', 'I'],
                '9': ['E'],
                '10': ['E'],
                '13': ['B', 'C', 'I'],
            },
        }
        if not self.company_id.l10n_ar_afip_responsibility_type_id:
            action = self.env.ref('base.action_res_company_form')
            msg = _('Can not create chart of account until you configure your company AFIP Responsibility and VAT.')
            raise RedirectWarning(msg, action.id, _('Go to Companies'))

        letters = letters_data['issued' if self.type == 'sale' else 'received'][
            self.company_id.l10n_ar_afip_responsibility_type_id.code]
        if not counterpart_partner:
            return letters

        if not counterpart_partner.l10n_ar_afip_responsibility_type_id:
            letters = []
        else:
            counterpart_letters = letters_data['issued' if self.type == 'purchase' else 'received'][
                counterpart_partner.l10n_ar_afip_responsibility_type_id.code]
            letters = list(set(letters) & set(counterpart_letters))
        return letters
