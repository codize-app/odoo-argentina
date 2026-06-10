# -*- coding: utf-8 -*-

from odoo import api, fields, models, Command
import logging
_logger = logging.getLogger(__name__)

class SaleOrder(models.Model):
    _inherit = "sale.order"

    currency_invoice_id = fields.Many2one('res.currency', string='Currency')
    tipo_cambio_othercurrency = fields.Float(string='Tipo de cambio', digits=(12, 6))

    def _set_currency_invoice(self, currency_choice, tipo_cambio_choice):
        for order in self:
            order.currency_invoice_id = currency_choice
            order.tipo_cambio_othercurrency = tipo_cambio_choice
            _logger.info("=== SO %s: Moneda Factura %s | TC: %s ===", order.name, currency_choice.name, tipo_cambio_choice)

    def _prepare_invoice(self):
        # 1. Llamamos al super para no perder la lógica nativa de Odoo
        invoice_vals = super(SaleOrder, self)._prepare_invoice()
        
        self.ensure_one()
        _logger.info('=== _prepare_invoice SO: %s ===', self.name)

        # 2. Si definimos una moneda distinta, la aplicamos al diccionario
        if self.currency_invoice_id:
            _logger.info('Cambiando moneda de factura a: %s', self.currency_invoice_id.name)
            invoice_vals['currency_id'] = self.currency_invoice_id.id
        
        return invoice_vals

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    def _prepare_invoice_line(self, **optional_values):
        self.ensure_one()
        
        # 1. Obtenemos los valores base del super()
        res = super(SaleOrderLine, self)._prepare_invoice_line(**optional_values)
        
        price_unit = self.price_unit
        _logger.info('=== _prepare_invoice_line SO: %s ===', self.order_id.name)
        _logger.info('Producto: %s | Precio Original: %s', self.product_id.name, price_unit)

        # 2. Verificamos si hay que convertir (usando el nombre de las monedas)
        currency_so = self.order_id.currency_id
        currency_inv = self.order_id.currency_invoice_id

        if currency_inv and currency_so.name != currency_inv.name:
            price_unit = self.price_unit * self.order_id.tipo_cambio_othercurrency
            _logger.info('CONVERSIÓN: %s x %s = %s', self.price_unit, self.order_id.tipo_cambio_othercurrency, price_unit)
            res['price_unit'] = price_unit
        else:
            _logger.info('Sin conversión (Misma moneda o sin moneda destino)')

        return res
