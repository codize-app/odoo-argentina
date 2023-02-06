from odoo import api, fields, models, SUPERUSER_ID
from odoo.exceptions import AccessError, UserError, ValidationError
import logging
_logger = logging.getLogger(__name__)

class AccountMove(models.Model):
    _inherit = "account.move"

    @api.depends('currency_id')
    def _get_currency_rate(self):
        for record in self:
            rate = 1
            if record.currency_id.rate > 0:
                if record.currency_id.name != 'ARS':
                    rate = 1 / record.currency_id.rate
                else:
                    rate = 1
                record.currency_rate = rate

    def _check_balanced(self):
            for rec in self:
                if rec.move_type == 'in_invoice' or rec.move_type == 'in_refund':
                    if rec.es_manual_rate==True:
                            return True
            res = super(AccountMove, self)._check_balanced()
            return res

    currency_rate = fields.Float(string='Tasa de cambio', readonly=False ,compute='_get_currency_rate', store=True)
    es_manual_rate = fields.Boolean(string='Usar TC manual')

