# -*- coding: utf-8 -*-
from odoo import api, fields, models, _, Command

# In Odoo 17+, inbound_payment_method_ids and outbound_payment_method_ids
# as Many2many fields were removed from account.journal.
# The payment methods are now accessed via inbound_payment_method_line_ids
# and outbound_payment_method_line_ids (One2many to account.payment.method.line).
# The at_least_one_inbound/outbound fields were also removed from core.

class AccountJournal(models.Model):
    _inherit = "account.journal"

    at_least_one_inbound = fields.Boolean(
        compute='_methods_compute',
        store=True,
    )
    at_least_one_outbound = fields.Boolean(
        compute='_methods_compute',
        store=True,
    )

    @api.depends('inbound_payment_method_line_ids', 'outbound_payment_method_line_ids')
    def _methods_compute(self):
        for journal in self:
            journal.at_least_one_inbound = bool(journal.inbound_payment_method_line_ids)
            journal.at_least_one_outbound = bool(journal.outbound_payment_method_line_ids)
