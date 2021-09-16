# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
from odoo import models, _, fields, api, tools
from odoo.exceptions import UserError,ValidationError
from odoo.tools.safe_eval import safe_eval
import datetime
import math

class AccountTax(models.Model):
    _inherit = 'account.tax'

    def _compute_amount(self, base_amount, price_unit, quantity=1.0, product=None, partner=None):
        """ Returns the amount of a single tax. base_amount is the actual amount on which the tax is applied, which is
            price_unit * quantity eventually affected by previous taxes (if tax is include_base_amount XOR price_include)
        """
        self.ensure_one()
        if self.amount_type == 'fixed':
            # Use copysign to take into account the sign of the base amount which includes the sign
            # of the quantity and the sign of the price_unit
            # Amount is the fixed price for the tax, it can be negative
            # Base amount included the sign of the quantity and the sign of the unit price and when
            # a product is returned, it can be done either by changing the sign of quantity or by changing the
            # sign of the price unit.
            # When the price unit is equal to 0, the sign of the quantity is absorbed in base_amount then
            # a "else" case is needed.
            if base_amount:
                return math.copysign(quantity, base_amount) * self.amount
            else:
                return quantity * self.amount

        price_include = self._context.get('force_price_include', self.price_include)

        # base * (1 + tax_amount) = new_base
        if self.amount_type == 'percent' and not price_include:
            #if self.id == 8:
            #    raise ValidatoinError('estamos aca')
            if self.is_padron:
                amount = self.amount
                if partner and partner.perception_ids:
                    for perception in partner.perception_ids:
                        if perception.tax_id.id == self.id:
                            amount = perception.percent
                return base_amount * amount / 100
            else:
                return base_amount * self.amount / 100
        # <=> new_base = base / (1 + tax_amount)
        if self.amount_type == 'percent' and price_include:
            return base_amount - (base_amount / (1 + self.amount / 100))
        # base / (1 - tax_amount) = new_base
        if self.amount_type == 'division' and not price_include:
            return base_amount / (1 - self.amount / 100) - base_amount if (1 - self.amount / 100) else 0.0
        # <=> new_base * (1 - tax_amount) = base
        if self.amount_type == 'division' and price_include:
            return base_amount - (base_amount * (self.amount / 100))


    is_padron = fields.Boolean('Es padron?')
    padron_prefix = fields.Char('Prefijo padron',default='')
    pefijo_padron = fields.Char('Prefijo padron')
