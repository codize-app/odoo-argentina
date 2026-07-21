# -*- coding: utf-8 -*-
from odoo import models, api
import logging
_logger = logging.getLogger(__name__)

class AccountChartTemplate(models.AbstractModel):
    _inherit = "account.chart.template"

    def _create_bank_journals(self, company, acc_template_ref):
        """
        Bank - Cash journals are created with this method.
        Inherit this function in order to add checks to cash and bank
        journals. This is because usually will be installed before chart loaded
        and they will be disabled by default.
        """
        res = super()._create_bank_journals(company, acc_template_ref)

        # each chart of account / localization should send this key if
        # they want withholding journal to be created
        if self._context.get('create_withholding_journal'):
            inbound_withholding = self.env.ref(
                'account_withholding.account_payment_method_in_withholding')
            outbound_withholding = self.env.ref(
                'account_withholding.account_payment_method_out_withholding')
            # In Odoo 19 use Command helpers for M2M fields
            journal = self.env['account.journal'].create({
                'name': 'Retenciones',
                'type': 'cash',
                'company_id': company.id,
                'inbound_payment_method_line_ids': [
                    (0, 0, {'payment_method_id': inbound_withholding.id})],
                'outbound_payment_method_line_ids': [
                    (0, 0, {'payment_method_id': outbound_withholding.id})],
            })
        return res
