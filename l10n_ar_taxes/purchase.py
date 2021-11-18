# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    """@api.onchange('product_id')
    def _add_internal_taxes(self):
        if not self.product_id:
            return
        vals = {}
        if self.product_id.product_tmpl_id.has_internal_taxes:
            vals['internal_taxes'] = self.product_id.product_tmpl_id.internal_taxes
            self.update(vals)
        else:
            return

    def _prepare_account_move_line(self, move=False):
        self.ensure_one()
        aml_currency = move and move.currency_id or self.currency_id
        date = move and move.date or fields.Date.today()
        res = {
            'display_type': self.display_type,
            'sequence': self.sequence,
            'name': '%s: %s' % (self.order_id.name, self.name),
            'product_id': self.product_id.id,
            'product_uom_id': self.product_uom.id,
            'quantity': self.qty_to_invoice,
            'price_unit': self.currency_id._convert(self.price_unit, aml_currency, self.company_id, date, round=False),
            'internal_taxes': self.internal_taxes,
            'tax_ids': [(6, 0, self.taxes_id.ids)],
            'analytic_account_id': self.account_analytic_id.id,
            'analytic_tag_ids': [(6, 0, self.analytic_tag_ids.ids)],
            'purchase_line_id': self.id,
        }
        if not move:
            return res

        if self.currency_id == move.company_id.currency_id:
            currency = False
        else:
            currency = move.currency_id

        res.update({
            'move_id': move.id,
            'currency_id': currency and currency.id or False,
            'date_maturity': move.invoice_date_due,
            'partner_id': move.partner_id.id,
        })
        return res"""

    internal_taxes = fields.Float('Impuestos Internos', default=0.0)

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    """@api.depends('order_line.price_total')
    def _amount_all(self):
        for order in self:
            amount_untaxed = amount_tax = amount_internal_tax = 0.0
            for line in order.order_line:
                amount_untaxed += line.price_subtotal
                amount_tax += line.price_tax
                amount_internal_tax += line.internal_taxes
            order.update({
                'amount_untaxed': amount_untaxed,
                'amount_tax': amount_tax,
                'amount_internal_tax': amount_internal_tax,
                'amount_total': amount_untaxed + amount_tax + amount_internal_tax,
            })"""

    amount_internal_tax = fields.Float('Impuestos Internos', readonly=True)
