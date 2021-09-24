# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    @api.onchange('product_id')
    def _add_internal_taxes(self):
        if not self.product_id:
            return
        vals = {}
        if self.product_id.product_tmpl_id.has_internal_taxes:
            vals['internal_taxes'] = self.product_id.product_tmpl_id.internal_ta                                                                                                                                                                                               xes
            self.update(vals)
        else:
            return

    internal_taxes = fields.Float('Impuestos Internos', default=0.0)

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    @api.depends('order_line.price_total')
    def _amount_all(self):
        """
        Compute the total amounts of the SO.
        """
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
            })

    amount_internal_tax = fields.Float('Impuestos Internos', readonly=True)
