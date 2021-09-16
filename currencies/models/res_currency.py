##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
from odoo import models, fields, api
from odoo.exceptions import ValidationError
import datetime

class ResCurrency(models.Model):
    _inherit = "res.currency"

    def _compute_inverse_rate(self):
        for rec in self:
            if rec.rate > 0:
                rec.inverse_rate = 1 / rec.rate

    inverse_rate = fields.Float('Tasa inversa',compute=_compute_inverse_rate)

    def get_currency_rate(self):
        self.ensure_one()
        res = self.get_pyafipws_currency_rate()
        raise ValidationError('%s'%(res[0]))

    @api.model
    def update_pyafipws_currency_rate(self, afip_ws='wsfe', company=False):
        # if not company, we use any that has valid certificates

        currencies = self.env['res.currency'].search([('l10n_ar_afip_code','!=',False)])
        for currency in currencies:
            if afip_ws == "wsfex":
                rate = ws.GetParamCtz(self.l10n_ar_afip_code)
            elif afip_ws == "wsfe":
                try:
                    res = currency.get_pyafipws_currency_rate()
                    if res:
                        vals = {
                                'name': str(datetime.date.today()),
                                'rate': 1 / res[0],
                                'currency_id': currency.id
                                }
                        rate_id = self.env['res.currency.rate'].search([('currency_id','=',currency.id),('name','=',str(datetime.date.today()))])
                        if not rate_id:
                            return_id = self.env['res.currency.rate'].create(vals)
                except:
                    continue


