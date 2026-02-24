# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import datetime
from datetime import date
from odoo.tools import format_date
import requests
import logging
import json
_logger = logging.getLogger(__name__)

class ResCurrency(models.Model):
    _inherit = 'res.currency'

    use_dolar_api = fields.Boolean('Usar Dolar API', help='Usar Dolar API en lugar de WebService de ARCA para obtener Tasa de Cambio')
    dolar_api_house = fields.Selection([
        ('oficial', 'Oficial'),
        ('blue', 'Blue'),
        ('bolsa', 'Bolsa'),
        ('contadoconliqui', 'CCL'),
        ('tarjeta', 'Tarjeta'),
        ('mayorista', 'Mayorista'),
        ('cripto', 'Cripto'),
    ], string='Casa', default='oficial')
    dolar_api_precio = fields.Selection([
        ('venta', 'Venta'),
        ('compra', 'Compra')
    ], string='Precio de', default='venta')

    def l10n_ar_action_get_afip_ws_currency_rate_get(self):
        if self.use_dolar_api:
            dolar_api = requests.get("https://dolarapi.com/v1/dolares/" + self.dolar_api_house)
            if dolar_api.status_code == 200:
                data = dolar_api.json()
                rate = 0
                if self.dolar_api_precio == 'venta':
                    rate = data['venta']
                else:
                    rate = data['compra']
                date = datetime.today()
                self.update({'rate_ids': [(0, 0, {'name': date, 'inverse_company_rate': rate})]})
        else:
            c = self.env['res.currency'].sudo().search([('name', '=', 'USD')], limit=1)
            for cu in c:
                date, rate = cu._l10n_ar_get_afip_ws_currency_rate()
                #date = datetime.strptime(date.today(), '%Y%m%d').date()
                date = datetime.today()
                cu.update({'rate_ids': [(0, 0, {'name': date, 'inverse_company_rate': rate})]})
