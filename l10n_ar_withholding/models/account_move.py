# -*- coding: utf-8 -*-
from odoo import models, api, fields
from collections import defaultdict
from odoo.tools.misc import formatLang, format_date, get_lang
import logging
_logger = logging.getLogger(__name__)

class AccountMove(models.Model):
	_inherit = "account.move"

	def _get_tax_factor(self):
		tax_factor = (self.amount_untaxed / self.amount_total) or 1.0
		doc_letter = self.l10n_latam_document_type_id.l10n_ar_letter
		# if we receive B invoices, then we take out 21 of vat
	        # this use of case if when company is except on vat for eg.
		if tax_factor == 1.0 and doc_letter == 'B':
			tax_factor = 1.0 / 1.21
		return tax_factor
	
	def _check_balanced(self):
		for rec in self:
			if rec.move_type == 'out_invoice' or rec.move_type == 'out_refund':
				if rec.invoice_line_ids:
					if rec.partner_id:
						if len(rec.partner_id.percepciones_ids) > 0:
							return True
		res = super(AccountMove, self)._check_balanced()
		return res

	def calculate_perceptions(self):
		if self.move_type == 'out_invoice' or self.move_type == 'out_refund':
			if self.invoice_line_ids:
				if self.partner_id:
					if len(self.partner_id.percepciones_ids) > 0:
						# Recomerremos las lineas en busca de si ya se encuentra el impuesto de percepcion, de caso contrario se agrega
						for iline in self.invoice_line_ids:
							_tiene_precepcion = 0
							for tax in iline.tax_ids:
								if str(self.partner_id.percepciones_ids[0].tax_id.id) == str(tax.id)[-2:]:
									_tiene_precepcion = 1
							if not _tiene_precepcion:
								iline.write({'tax_ids': [(4, self.partner_id.percepciones_ids[0].tax_id.id)]})
						# Recomputamos Apuntes contables y actualizamos el valor de Cuenta a Pagar por el total de la factura
						self._recompute_tax_lines(recompute_tax_base_amount=False)
						for lac in self.line_ids:
							if lac.account_id.id == self.partner_id.property_account_receivable_id.id:
								lac.write({'debit' : self.amount_total})