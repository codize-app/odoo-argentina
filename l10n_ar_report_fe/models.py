# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
import logging
import datetime
from datetime import datetime, timedelta, date

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


"""
class AccountMove(models.Model):
	_inherit = 'account.move'

	def _compute_cae_barcode(self):
                #company.partner_id.document_number,
                #o.journal_id.journal_class_id.afip_code,
                #o.journal_id.point_of_sale,
                #int(o.afip_cae or 0),
                #int(o.afip_cae_due is not False and flatdate(o.afip_cae_due) or 0)
		for inv in self:
			inv.cae_barcode = str(inv.company_id.partner_id.main_id_number) + str(inv.journal_document_type_id.document_type_id.code) + \
				str(inv.journal_id.point_of_sale_number) + str(inv.afip_auth_code or 0) + str(inv.afip_auth_code_due or 0).replace('-','')

	cae_barcode = fields.Char('CAE Barcode',compute=_compute_cae_barcode)
"""
