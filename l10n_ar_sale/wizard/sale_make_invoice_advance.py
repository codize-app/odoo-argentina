# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import time
import logging
_logger=logging.getLogger(__name__)

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = "sale.advance.payment.inv"
    _description = "Sales Advance Payment Invoice"


    def create_invoices(self):
        sale_orders = self.env['sale.order'].browse(self._context.get('active_ids', []))

        if self.advance_payment_method == 'delivered':
            sale_orders._set_currency_invoice(self.currency_id, self.tipo_cambio)
            sale_orders._create_invoices(final=self.deduct_down_payments)
        else:
            # Create deposit product if necessary
            if not self.product_id:
                vals = self._prepare_deposit_product()
                self.product_id = self.env['product.product'].create(vals)
                self.env['ir.config_parameter'].sudo().set_param('sale.default_deposit_product_id', self.product_id.id)

            sale_line_obj = self.env['sale.order.line']
            for order in sale_orders:
                amount, name = self._get_advance_details(order)

                if self.product_id.invoice_policy != 'order':
                    raise UserError(_(
                        'The product used to invoice a down payment should have an invoice policy set to "Ordered quantities". Please update your deposit product to be able to create a deposit invoice.'))
                if self.product_id.type != 'service':
                    raise UserError(_(
                        "The product used to invoice a down payment should be of type 'Service'. Please use another product or update this product."))
                taxes = self.product_id.taxes_id.filtered(
                    lambda r: not order.company_id or r.company_id == order.company_id)
                tax_ids = order.fiscal_position_id.map_tax(taxes).ids
                analytic_tag_ids = []
                for line in order.order_line:
                    analytic_tag_ids = [(4, analytic_tag.id, None) for analytic_tag in line.analytic_tag_ids]

                so_line_values = self._prepare_so_line(order, analytic_tag_ids, tax_ids, amount)
                so_line = sale_line_obj.create(so_line_values)
                self._create_invoice(order, so_line, amount)
        if self._context.get('open_invoices', False):
            return sale_orders.action_view_invoice()
        return {'type': 'ir.actions.act_window_close'}

    @api.depends("currency_id")
    def _get_tasa_currency(self):
        sale_orders = self.env['sale.order'].browse(self._context.get('active_ids', []))
        for order in sale_orders:
        # for rec in self:
            if (order.currency_id.name != self.currency_id.name):
                if order.currency_id.name == 'ARS':
                    rate = self.currency_id.rate
                else:
                    rate = 1/ order.currency_id.rate
            else:
                    rate=1
            self.tipo_cambio = rate


    tipo_cambio = fields.Float(string='Tipo de cambio', compute=_get_tasa_currency, store=True, readonly=False,
                               digits=(12, 6))
