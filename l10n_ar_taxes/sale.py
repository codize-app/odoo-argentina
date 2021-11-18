# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

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

    def _prepare_invoice_line(self, **optional_values):
        self.ensure_one()
        res = {
            'display_type': self.display_type,
            'sequence': self.sequence,
            'name': self.name,
            'product_id': self.product_id.id,
            'product_uom_id': self.product_uom.id,
            'quantity': self.qty_to_invoice,
            'discount': self.discount,
            'price_unit': self.price_unit,
            'internal_taxes': self.internal_taxes,
            'tax_ids': [(6, 0, self.tax_id.ids)],
            'analytic_account_id': self.order_id.analytic_account_id.id,
            'analytic_tag_ids': [(6, 0, self.analytic_tag_ids.ids)],
            'sale_line_ids': [(4, self.id)],
        }
        if optional_values:
            res.update(optional_values)
        if self.display_type:
            res['account_id'] = False
        return res"""

    internal_taxes = fields.Float('Impuestos Internos', default=0.0)

class SaleOrder(models.Model):
    _inherit = 'sale.order'

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
