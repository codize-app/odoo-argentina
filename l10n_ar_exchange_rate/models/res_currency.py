from odoo import models, fields
from datetime import datetime
import requests
import logging

_logger = logging.getLogger(__name__)


class ResCurrency(models.Model):
    _inherit = 'res.currency'

    use_dolar_api = fields.Boolean('Usar Dolar API')

    dolar_api_house = fields.Selection([
        ('oficial', 'Oficial'),
        ('blue', 'Blue'),
        ('bolsa', 'Bolsa'),
        ('contadoconliqui', 'CCL'),
        ('tarjeta', 'Tarjeta'),
        ('mayorista', 'Mayorista'),
        ('cripto', 'Cripto'),
    ], default='oficial')

    dolar_api_precio = fields.Selection([
        ('venta', 'Venta'),
        ('compra', 'Compra')
    ], default='venta')

    def l10n_ar_action_get_afip_ws_currency_rate_get(self):
        for currency in self:
            if currency.use_dolar_api:
                response = requests.get(f"https://dolarapi.com/v1/dolares/{currency.dolar_api_house}")

                if response.status_code == 200:
                    data = response.json()

                    rate = data['venta'] if currency.dolar_api_precio == 'venta' else data['compra']

                    currency.rate_ids = [(0, 0, {
                        'name': datetime.today(),
                        'inverse_company_rate': rate
                    })]
            else:
                usd = self.env['res.currency'].sudo().search([('name', '=', 'USD')], limit=1)

                if usd:
                    date, rate = usd._l10n_ar_get_afip_ws_currency_rate()

                    usd.rate_ids = [(0, 0, {
                        'name': datetime.today(),
                        'inverse_company_rate': rate
                    })]