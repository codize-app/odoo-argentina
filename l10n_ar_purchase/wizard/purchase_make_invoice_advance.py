# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import time
import logging
_logger=logging.getLogger(__name__)

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class PurchaseAdvanceInvoice(models.TransientModel):
    _name = "purchase.advance.invoice"
    _description = "Purchases Advance Invoice"


    def create_invoices(self):
        purchase_orders = self.env['purchase.order'].browse(self._context.get('active_ids', []))
        purchase_orders._set_currency_invoice(self.currency_id, self.tipo_cambio)
        purchase_orders.action_create_invoice()
        return {'type': 'ir.actions.act_window_close'}

    @api.depends("currency_id")
    def _get_tasa_currency(self):
        purchase_orders = self.env['purchase.order'].browse(self._context.get('active_ids', []))
        for order in purchase_orders:
        # for rec in self:
            rate=1
            if (order.currency_id.name != self.currency_id.name):
                if order.currency_id.name == 'ARS':
                    rate = self.currency_id.rate
                else:
                    if order.tipo_cambio_othercurrency>0:
                        rate = order.tipo_cambio_othercurrency
                    else:
                        rate = 1/ order.currency_id.rate
            else:
                if order.currency_id.name != 'ARS':
                    #si guardo en dolar desde dolar igual tomo el rate para el monto en moneda de la compañia
                    if order.tipo_cambio_othercurrency>0:
                        rate = order.tipo_cambio_othercurrency
                    else:
                        rate = 1/ order.currency_id.rate
            self.tipo_cambio = rate

    @api.model
    def _default_currency_id(self):
        if self._context.get('active_model') == 'purchase.order' and self._context.get('active_id', False):
            purchase_order = self.env['purchase.order'].browse(self._context.get('active_id'))
            return purchase_order.currency_id

    tipo_cambio = fields.Float(string='Tipo de cambio', compute=_get_tasa_currency, store=True, readonly=False,
                               digits=(12, 6))
    currency_id = fields.Many2one('res.currency', string='Moneda', default=_default_currency_id)