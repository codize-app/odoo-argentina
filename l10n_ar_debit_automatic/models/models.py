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
            if not self.payment_account or not self.payment_journal or not self.payment_currency:
                raise ValidationError('Debe seleccionar una Cuenta, Diario de Pagos y Moneda para Registrar los Pagos.')
            txt = base64.b64decode(self.debit_automatic_txt).decode("utf-8", "ignore").strip()
            self.RG_TXT_DEBIT_AUTOMATIC = txt
            txt_lines = txt.split('\n')
            if txt_lines[0][:9] == '0RDEBLIQC':
                year = txt_lines[0][29:33]
                month = txt_lines[0][33:35]
                day = txt_lines[0][35:37]
                self.date = year + '-' + month + '-' + day
            else:
                raise ValidationError('El archivo debe tener una formato compatible con Débito Automático. Es imposible cargar este TXT, consulte con su Administrador.')
            self.result = ''
            for id, line in enumerate(txt_lines):
                if id != 0 and id != len(txt_lines)-1:
                    # Credit Card Number
                    card_num = line[26:42]

                    # Amount to Pay
                    amount_text = line[62:77]
                    amount_cent = int(amount_text[-2:])
                    amount_round = int(amount_text[:-2])
                    amount_total = amount_round + (amount_cent / 100.0)

                    resultado = '\n' + str(card_num) + ":" + self.env['account.payment'].acc_payment(self.payment_account,self.payment_journal,self.payment_currency,card_num,amount_total,'')
                    self.result = self.result + resultado
            self.state = 'register'

    name = fields.Char('Nombre', required=True)
    company_id = fields.Many2one(
        'res.company',
        string='Empresa',
        required=True,
        readonly=True,
        states={'draft': [('readonly', False)]},
        default=lambda self: self.env['res.company']._company_default_get('account.debit.automatic')
    )
    date = fields.Date('Fecha', readonly=True)
    state = fields.Selection([('draft', 'Borrador'), ('register', 'Registrado')], 'Estado', default='draft')
    debit_automatic_txt = fields.Binary('Archivo TXT de Débito Automático', help='Suba acá su archivo de Débito Automático exportado por Visa.')
    RG_TXT_DEBIT_AUTOMATIC = fields.Text('RG_TXT_DEBIT_AUTOMATIC')
    result = fields.Char("Resultado")
    payment_account = fields.Many2one('account.account', required=True, string='Cuenta del Pago')
    payment_journal = fields.Many2one('account.journal', required=True, string='Diario del Pago')
    payment_currency = fields.Many2one('res.currency', required=True, string='Moneda del Pago')

class AccountPayment(models.Model):
    _inherit = 'account.payment'

    def acc_payment(self, account, journal, currency, card_num, amount_total, mensaje=""):
        res_bank_partner=self.env['res.partner.bank'].search([("acc_number","=",str(card_num))])
        validar=True
        payment=None
        _logger.info(str(card_num))
        if (len(res_bank_partner) == 0):
            return mensaje +'\n\t No se encontro la tarjeta cargada.\n\t Pago no creado(crear manualmente)'
        elif (len(res_bank_partner)>1):
            return mensaje +'\n\t Existe mas de un contacto con la misma tarjeta.\n\t Pago no creado(crear manualmente)'
        else:
            vals={
                'payment_type':'inbound',
                'partner_type':'customer',
                'partner_id': res_bank_partner.partner_id.id,
                'destination_account_id': account.id,
                'journal_id':journal.id,
                'payment_method_id':res_bank_partner.partner_id.method_id.id,
                'amount': amount_total,
                'currency_id': currency.id,
                'ref':''
            }

            try:
                payment=self.env['account.payment'].sudo().create(vals)
            except:
                validar=False
                if not res_bank_partner.partner_id.method_id:
                    vals['ref']=vals['ref']+"Método de pago incorrecto o faltante."
                    mensaje= mensaje +'\n\t Método de pago incorrecto o faltante.\n\t Cargar desde contactos->Contabilidad->Método de pago.\n\t Pago no creado(crear manualmente)'
                    return mensaje
                if not amount_total:
                    vals['amount']= 0.0
                    vals['ref']=vals['ref']+"Monto faltante o incorrecto."
                    payment=self.env['account.payment'].sudo().create(vals)
                    mensaje= mensaje +'\n\t Monto faltante o incorrecto.'

            if validar:
                # ''' draft -> posted '''
                try:
                    payment.move_id._post(soft=False)
                except:
                    return mensaje +'\n\t No se pudo validar.(pago creado como borrador)'
            return mensaje +'\n\t Validado.\n'

class ResPartner(models.Model):
    _inherit = 'res.partner'

    method_id = fields.Many2one('account.payment.method', 'Método de pago automático')