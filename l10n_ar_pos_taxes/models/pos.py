# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError
import logging
_logger = logging.getLogger(__name__)

class PosOrderLine(models.Model):
    _inherit = 'pos.order.line'

    @api.onchange('product_id')
    def _add_internal_taxes_pos(self):
        if not self.product_id:
            return
        vals = {}
        if self.product_id.product_tmpl_id.has_internal_taxes:
            vals['internal_taxes'] = self.product_id.product_tmpl_id.internal_taxes
            self.update(vals)
        else:
            return

    def _prepare_invoice_line_pos(self, **optional_values):
        """
        Prepare the dict of values to create the new invoice line for a sales order line.
        :param qty: float quantity to invoice
        :param optional_values: any parameter that should be added to the returned invoice line
        """
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
        _logger.info(res)
        return res

    internal_taxes = fields.Float('Impuestos Internos', default=0.0)



class PosOrder(models.Model):
    _inherit = 'pos.order'

    @api.depends('lines.internal_taxes')
    def _amount_all_pos(self):
        """
        Compute the total amounts of the SO.
        """        
        for order in self:
            amount_sub = amount_tax = amount_internal_tax = 0.0
            for line in order.order_line:
                amount_sub += line.price_subtotal
                amount_tax += line.price_tax
                amount_internal_tax += line.internal_taxes
            order.update({
                'amount_subtotal': amount_sub,
                'amount_tax': amount_tax,
                'amount_internal_tax': amount_internal_tax,
                'amount_total': amount_sub + amount_tax + amount_internal_tax,
            })

    amount_subtotal = fields.Float('Subtotal', readonly=True)
    amount_internal_tax = fields.Float('Impuestos Internos', readonly=True)
