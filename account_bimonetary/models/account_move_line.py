# -*- coding: utf-8 -*-

from odoo import models, fields, api
import logging

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    amount_currency_usd = fields.Monetary(
        string='Monto en USD',
        compute='_compute_amount_currency_usd', readonly=False, store=True, precompute=True,
        help="Monto expresado en Dólares USD",
        currency_field='currency_usd',
        tracking=True
    )
    currency_usd = fields.Many2one(string='Moneda USD', 'res.currency', default=1, readonly=True)

    @api.depends('balance')
    def _compute_amount_currency_usd(self):
        for line in self:
            if line.currency_id != line.currency_usd:
                line.amount_currency_usd = line.company_id.currency_id._convert(line.balance, line.currency_usd, line.company_id, line.date)
            else:
                line.amount_currency_usd = line.amount_currency
