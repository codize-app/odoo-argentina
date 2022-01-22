# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError
import base64
base64.encodestring = base64.encodebytes
import logging
_logger = logging.getLogger(__name__)

class AccountDebitAutomatic(models.Model):
    _name = 'account.debit.automatic'
    _inherit = ['mail.thread']

    def register_debit_automatic(self):
        if not self.debit_automatic_txt:
            raise ValidationError('¡No se ha cargado archivo TXT!')
        else:
            txt = base64.b64decode(self.debit_automatic_txt).decode("utf-8", "ignore").strip()
            self.RG_TXT_DEBIT_AUTOMATIC = txt
            txt_lines = txt.split('\n')
            if txt_lines[0][:8] == '0DEBLIQC':
                year = txt_lines[0][29:33]
                month = txt_lines[0][33:35]
                day = txt_lines[0][35:37]
                self.date = year + '-' + month + '-' + day
            else:
                raise ValidationError('El archivo debe tener una formato compatible con Débito Automático. Es imposible cargar este TXT, consulte con su Administrador.')

            for id, line in enumerate(txt_lines):
                if id != 0 and id != len(txt_lines)-1:
                    l = line.split('   ')

                    # Credit Card Number
                    card_num = l[0]

                    # Order
                    order = l[1][:8]

                    # Date
                    date = l[1][8:-34]

                    # Indicator
                    indi = l[1][16:-30]

                    # Amount to Pay
                    amount_text = l[1][20:-15]
                    amount_cent = int(amount_text[-2:])
                    amount_round = int(amount_text[:-2])
                    amout_total = amount_round + (amount_cent / 100.0)

    name = fields.Char('Nombre', required=True)
    company_id = fields.Many2one(
        'res.company',
        string='Empresa',
        required=True,
        readonly=True,
        states={'draft': [('readonly', False)]},
        default=lambda self: self.env[
            'res.company']._company_default_get('account.debit.automatic')
    )
    date = fields.Date('Fecha', readonly=True)
    state = fields.Selection([('draft', 'Borrador'), ('register', 'Registrado')], 'Estado', default='draft')
    debit_automatic_txt = fields.Binary('Archivo TXT de Débito Automático', help='Suba acá su archivo de Débito Automático exportado por Visa.')
    RG_TXT_DEBIT_AUTOMATIC = fields.Text('RG_TXT_DEBIT_AUTOMATIC')
