# -*- coding: utf-8 -*-
from odoo import models, api, fields
from collections import defaultdict
from odoo.tools.misc import formatLang, format_date, get_lang
import logging
_logger = logging.getLogger(__name__)

class AccountMove(models.Model):
	_inherit = "account.move"

	def _get_tax_factor(self):
		tax_factor = (self.amount_untaxed / self.amount_total) if self.amount_total > 0 else 1
		doc_letter = self.l10n_latam_document_type_id.l10n_ar_letter
		# if we receive B invoices, then we take out 21 of vat
	        # this use of case if when company is except on vat for eg.
		if tax_factor == 1.0 and doc_letter == 'B':
			tax_factor = 1.0 / 1.21
		return tax_factor

	def calculate_perceptions(self):
		#Esta funcion se utiliza para todos los submodulos de percepciones
		_logger.warning('**** Se calcular Per')
