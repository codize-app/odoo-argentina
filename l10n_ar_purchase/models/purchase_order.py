from odoo.exceptions import UserError
from odoo import api, fields, models
import logging
_logger=logging.getLogger(__name__)

class product_purchase_othercurrency(models.Model):
    _inherit = "purchase.order"
    currency_invoice_id = fields.Many2one('res.currency', string='Currency')
    tipo_cambio_othercurrency = fields.Float(string='Tipo de cambio')

    @api.onchange('currency_id')
    def _get_tasa_currency(self):
        for order in self:
            _logger.info('nombre' + order.currency_id.name)
            if order.currency_id.name != 'ARS':
                    _logger.info('rate'+ str(order.currency_id.rate))
                    order.tipo_cambio_othercurrency = 1 / order.currency_id.rate
            else:
                    order.tipo_cambio_othercurrency = 1

    def _set_currency_invoice(self, currency_choice,tipo_cambio_choice):
        for purchase in self:
            purchase.currency_invoice_id= currency_choice
            purchase.tipo_cambio_othercurrency = tipo_cambio_choice

    def _prepare_invoice(self):
        """Prepare the dict of values to create the new invoice for a purchase order.
        """
        self.ensure_one()
        move_type = self._context.get('default_move_type', 'in_invoice')

        partner_invoice = self.env['res.partner'].browse(self.partner_id.address_get(['invoice'])['invoice'])
        partner_bank_id = self.partner_id.commercial_partner_id.bank_ids.filtered_domain(['|', ('company_id', '=', False), ('company_id', '=', self.company_id.id)])[:1]
        currency = self.currency_invoice_id

        invoice_vals = {
            'ref': self.partner_ref or '',
            'move_type': move_type,
            'narration': self.notes,
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

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    def _prepare_account_move_line(self, move=False):
        self.ensure_one()
        aml_currency = move and move.currency_id or self.currency_id

        price_unit = self.price_unit
        if (self.order_id.currency_id.name != self.order_id.currency_invoice_id.name):
            price_unit = self.price_unit * self.order_id.tipo_cambio_othercurrency

        date = move and move.date or fields.Date.today()
        res = {
            'display_type': self.display_type or 'product',
            'name': '%s: %s' % (self.order_id.name, self.name),
            'product_id': self.product_id.id,
            'product_uom_id': self.product_uom.id,
            'quantity': self.qty_to_invoice,
            'price_unit': price_unit,
            #'price_unit': self.currency_id._convert(self.price_unit, aml_currency, self.company_id, date, round=False),
            'tax_ids': [(6, 0, self.taxes_id.ids)],
            'purchase_line_id': self.id,
        }
        if self.analytic_distribution and not self.display_type:
            res['analytic_distribution'] = self.analytic_distribution
        return res

