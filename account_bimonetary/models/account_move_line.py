# -*- coding: utf-8 -*-

from odoo import models, fields, api


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    amount_currency_usd = fields.Monetary(
        string='Monto en USD',
        group_operator=None,
        compute='_compute_amount_currency_usd', store=True, readonly=False, precompute=True,
        help="Monto expresado en Dólares USD")
    currency_usd = fields.Many2one('res.currency', default=2, readonly=True)

    @api.depends('balance')
    def _compute_amount_currency_usd(self):
        for line in self:
            if line.currency_id != line.currency_usd:
                line.amount_currency_usd = line.currency_usd.round( line.company_id.currency_id.with_context(date=line.date).compute(line.balance, line.currency_usd) )
            else:
                line.amount_currency_usd = line.amount_currency
