# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError

from functools import partial

import logging
_logger = logging.getLogger(__name__)

class PosOrderLine(models.Model):
    _inherit = 'pos.order.line'

    def _order_line_fields(self, line, session_id=None):
        if line and 'name' not in line[2]:
            session = self.env['pos.session'].browse(session_id).exists() if session_id else None
            if session and session.config_id.sequence_line_id:
                # set name based on the sequence specified on the config
                line[2]['name'] = session.config_id.sequence_line_id._next()
            else:
                # fallback on any pos.order.line sequence
                line[2]['name'] = self.env['ir.sequence'].next_by_code('pos.order.line')

        if line and 'tax_ids' not in line[2]:
            product = self.env['product.product'].browse(line[2]['product_id'])
            line[2]['tax_ids'] = [(6, 0, [x.id for x in product.taxes_id])]

        # Compute Internal Taxes
        product = self.env['product.product'].browse(line[2]['product_id'])
        line[2]['internal_taxes'] = product.internal_taxes
        #line[2]['price_subtotal'] = line[2]['price_subtotal'] + (line[2]['internal_taxes'] * line[2]['qty'])
        #line[2]['price_subtotal_incl'] = line[2]['price_subtotal_incl'] + (line[2]['internal_taxes'] * line[2]['qty'])

        # Clean up fields sent by the JS
        line = [
            line[0], line[1], {k: v for k, v in line[2].items() if k in self.env['pos.order.line']._fields}
        ]
        return line

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

    @api.model
    def _order_fields(self, ui_order):
        process_line = partial(self.env['pos.order.line']._order_line_fields, session_id=ui_order['pos_session_id'])
        internal_taxes = 0

        lines = [process_line(l) for l in ui_order['lines']]
        for l in lines:
            internal_taxes = l[2]['internal_taxes'] * l[2]['qty']

        return {
            'user_id':      ui_order['user_id'] or False,
            'session_id':   ui_order['pos_session_id'],
            'lines':        [process_line(l) for l in ui_order['lines']] if ui_order['lines'] else False,
            'pos_reference': ui_order['name'],
            'sequence_number': ui_order['sequence_number'],
            'partner_id':   ui_order['partner_id'] or False,
            'date_order':   ui_order['creation_date'].replace('T', ' ')[:19],
            'fiscal_position_id': ui_order['fiscal_position_id'],
            'pricelist_id': ui_order['pricelist_id'],
            'amount_paid':  ui_order['amount_paid'] + internal_taxes,
            'amount_total':  ui_order['amount_total'] + internal_taxes,
            'amount_internal_tax': internal_taxes,
            'amount_tax':  ui_order['amount_tax'],
            'amount_return':  ui_order['amount_return'],
            'company_id': self.env['pos.session'].browse(ui_order['pos_session_id']).company_id.id,
            'to_invoice': ui_order['to_invoice'] if "to_invoice" in ui_order else False,
            'is_tipped': ui_order.get('is_tipped', False),
            'tip_amount': ui_order.get('tip_amount', 0),
        }

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
