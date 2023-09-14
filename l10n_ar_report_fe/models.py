# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, RedirectWarning
import logging
import datetime
from datetime import datetime, timedelta, date
from odoo.tools import float_repr
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
        # Faster QR generation - based on AdHoc
        for rec in self:
            if rec.afip_auth_mode in ["CAE", "CAEA"] and rec.afip_auth_code:
                number_parts = self._l10n_ar_get_document_number_parts(
                    rec.l10n_latam_document_number, rec.l10n_latam_document_type_id.code
                )

                qr_dict = {
                    "ver": 1,
                    "fecha": str(rec.invoice_date),
                    "cuit": int(rec.company_id.partner_id.l10n_ar_vat),
                    "ptoVta": number_parts["point_of_sale"],
                    "tipoCmp": int(rec.l10n_latam_document_type_id.code),
                    "nroCmp": number_parts["invoice_number"],
                    "importe": float(float_repr(rec.amount_total, 2)),
                    "moneda": rec.currency_id.l10n_ar_afip_code,
                    "ctz": float(float_repr(rec.l10n_ar_currency_rate, 2)),
                    "tipoCodAut": "E" if rec.afip_auth_mode == "CAE" else "A",
                    "codAut": int(rec.afip_auth_code),
                }
                if (
                    len(rec.commercial_partner_id.l10n_latam_identification_type_id)
                    and rec.commercial_partner_id.vat
                ):
                    qr_dict["tipoDocRec"] = int(
                        rec.commercial_partner_id.l10n_latam_identification_type_id.l10n_ar_afip_code
                    )
                    qr_dict["nroDocRec"] = int(
                        rec.commercial_partner_id.vat.replace("-", "").replace(".", "")
                    )
                qr_data = base64.encodestring(
                    json.dumps(qr_dict, indent=None).encode("ascii")
                ).decode("ascii")
                qr_data = str(qr_data).replace("\n", "")
                rec.json_qr = str(qr_dict)
                rec.texto_modificado_qr = "https://www.afip.gob.ar/fe/qr/?p=%s" % qr_data
            else:
                rec.texto_modificado_qr = False
    
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
