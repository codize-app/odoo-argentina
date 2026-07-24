# -*- coding: utf-8 -*-

from odoo import api, fields, models, Command
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    currency_invoice_id = fields.Many2one('res.currency', string='Currency')
    tipo_cambio_othercurrency = fields.Float(string='Tipo de cambio')

    @api.onchange('currency_id')
    def _get_tasa_currency(self):
        for order in self:
            _logger.info('nombre' + order.currency_id.name)
            if order.currency_id.name != 'ARS':
                _logger.info('rate' + str(order.currency_id.rate))
                order.tipo_cambio_othercurrency = 1 / order.currency_id.rate
            else:
                order.tipo_cambio_othercurrency = 1

    def _set_currency_invoice(self, currency_choice, tipo_cambio_choice):
        for purchase in self:
            purchase.currency_invoice_id = currency_choice
            purchase.tipo_cambio_othercurrency = tipo_cambio_choice

    def _prepare_invoice(self):
        self.ensure_one()
        _logger.info('=== _prepare_invoice PO: %s ===', self.name)
        _logger.info('currency_id (pedido): %s', self.currency_id.name)
        _logger.info('currency_invoice_id: %s', self.currency_invoice_id.name if self.currency_invoice_id else 'VACIO')
        _logger.info('tipo_cambio_othercurrency: %s', self.tipo_cambio_othercurrency)
        move_type = self._context.get('default_move_type', 'in_invoice')

        partner_invoice = self.env['res.partner'].browse(self.partner_id.address_get(['invoice'])['invoice'])
        partner_bank_id = self.partner_id.commercial_partner_id.bank_ids.filtered_domain(
            ['|', ('company_id', '=', False), ('company_id', '=', self.company_id.id)]
        )[:1]
        currency = self.currency_invoice_id or self.currency_id

        invoice_vals = {
            'ref': self.partner_ref or '',
            'move_type': move_type,
            'narration': self.note,
            'currency_id': currency.id,
            'invoice_user_id': self.user_id and self.user_id.id or self.env.user.id,
            'partner_id': partner_invoice.id,
            'fiscal_position_id': (self.fiscal_position_id or self.fiscal_position_id._get_fiscal_position(partner_invoice)).id,
            'payment_reference': self.partner_ref or '',
            'partner_bank_id': partner_bank_id.id,
            'invoice_origin': self.name,
            'invoice_payment_term_id': self.payment_term_id.id,
            'invoice_line_ids': [],
            'company_id': self.company_id.id,
        }
        return invoice_vals

    def button_confirm(self):
        res = super().button_confirm()
        self._exe_update_supplier_prices()
        return res

    def _exe_update_supplier_prices(self):
        for order in self:
            partner = order.partner_id
            currency = order.currency_id

            _logger.info("EXE_PURCHASE >>> Orden: %s | Proveedor: %s | Moneda: %s (id=%s)",
                         order.name, partner.name, currency.name, currency.id)

            for line in order.order_line:
                if line.display_type:
                    continue
                product = line.product_id.product_tmpl_id
                if not product:
                    continue

                price_unit = line.price_unit
                if not price_unit:
                    continue

                _logger.info("EXE_PURCHASE >>> Línea: %s | Precio: %s | Moneda orden: %s",
                             line.product_id.name, price_unit, currency.name)

                supplierinfo = self.env['product.supplierinfo'].search([
                    ('partner_id', '=', partner.id),
                    ('product_tmpl_id', '=', product.id),
                ], order='id asc', limit=1)

                if supplierinfo:
                    _logger.info("EXE_PURCHASE >>> Actualizando supplierinfo id=%s | precio=%s | currency_id=%s",
                                 supplierinfo.id, price_unit, currency.id)
                    supplierinfo.sudo().write({
                        'price': price_unit,
                        'currency_id': currency.id,
                    })
                    _logger.info("EXE_PURCHASE >>> Después del write: currency_id=%s",
                                 supplierinfo.currency_id.name)
                else:
                    self.env['product.supplierinfo'].sudo().create({
                        'partner_id': partner.id,
                        'product_tmpl_id': product.id,
                        'product_id': line.product_id.id,
                        'price': price_unit,
                        'currency_id': currency.id,
                        'delay': 1,
                    })


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    def _prepare_account_move_line(self, move=False):
        self.ensure_one()

        price_unit = self.price_unit
        _logger.info('=== _prepare_account_move_line ===')
        _logger.info('product: %s | price_unit original: %s', self.product_id.name, price_unit)
        _logger.info('currency pedido: %s | currency_invoice: %s',
                     self.order_id.currency_id.name,
                     self.order_id.currency_invoice_id.name if self.order_id.currency_invoice_id else 'VACIO')

        if self.order_id.currency_invoice_id and self.order_id.currency_id.name != self.order_id.currency_invoice_id.name:
            price_unit = self.price_unit * self.order_id.tipo_cambio_othercurrency
            _logger.info('Conversión aplicada: %s x %s = %s',
                         self.price_unit, self.order_id.tipo_cambio_othercurrency, price_unit)
        else:
            _logger.info('Sin conversión (misma moneda)')

        res = {
            'display_type': self.display_type or 'product',
            'name': '%s: %s' % (self.order_id.name, self.name),
            'product_id': self.product_id.id,
            'product_uom_id': self.product_uom_id.id,
            'quantity': self.qty_to_invoice,
            'price_unit': price_unit,
            'tax_ids': [Command.set(self.tax_ids.ids)],
            'purchase_line_id': self.id,
        }

        if self.analytic_distribution and not self.display_type:
            res['analytic_distribution'] = self.analytic_distribution

        return res