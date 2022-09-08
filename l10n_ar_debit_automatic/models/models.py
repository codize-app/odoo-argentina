# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError
import base64
base64.encodestring = base64.encodebytes
import logging
import datetime
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
            lines_by_card_numbers=dict()
            for id, line in enumerate(txt_lines):
                if id != 0 and id != len(txt_lines)-1:
                    # Credit Card Number
                    card_num = line[26:42]
                    res_bank_partner=self.env['res.partner.bank'].search([("acc_number","=",str(card_num))])

                    # Amount to Pay
                    amount_text = line[62:77]
                    amount_cent = int(amount_text[-2:])
                    amount_round = int(amount_text[:-2])
                    amount_total = amount_round + (amount_cent / 100.0)

                    date = datetime.date(2000+int(line[54:56]),int(line[52:54]),int(line[50:52]))
                    err_code=int(line[129:132])
                    if(err_code):
                        err_msg=line[132:161]
                        if(res_bank_partner.partner_id.name):
                            self.result = self.result+res_bank_partner.partner_id.name+ ". Tarjeta " + str(card_num) + " (Monto: $"+str(amount_total)+")" + ": " + str(err_code)+'--'+err_msg + '\n'
                        else:
                            self.result =self.result+'No se encontro contacto para la tarjeta ' + str(card_num) + " (Monto: $"+str(amount_total)+")" + ": " + str(err_code)+'--'+err_msg + '\n'
                    else:
                        if (len(res_bank_partner) == 0):
                            self.result =self.result+'No se encontro contacto para la tarjeta ' + str(card_num) + " (Monto: $"+str(amount_total)+")" + ": El pago se realizo correctamente, pero no se registro en el sistema."+ '\n'
                            continue
                        elif (len(res_bank_partner)>1):
                            self.result =self.result+'Se encontraron múltiples contactos para la tarjeta ' + str(card_num) + " (Monto: $"+str(amount_total)+")" + ": El pago se realizo correctamente, pero no se registro en el sistema."+ '\n'
                            continue
                        else:
                            if(card_num not in lines_by_card_numbers.keys()):
                                lines_by_card_numbers[card_num]=[]
                            lines_by_card_numbers[card_num].append({
                                'amount_text':amount_text,
                                'amount_cent':amount_cent,
                                'amount_round':amount_round,
                                'amount_total':amount_total,
                                'date':date,
                            })
            for key in lines_by_card_numbers.keys():
                resultado = '\n' + str(key) + ":" + self.env['account.payment'].acc_payment(self,self.payment_currency,key,lines_by_card_numbers[key],self.validar)
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
    validar = fields.Boolean(string='Validar Pagos', default=True)

class AccountPayment(models.Model):
    _inherit = 'account.payment'

    def acc_payment(self, accountDebitAutomatic, currency, card_num, vals,validar=True):
        res_bank_partner=self.env['res.partner.bank'].search([("acc_number","=",str(card_num))])

        mensaje=""
        if (not res_bank_partner or len(res_bank_partner)  !=1):
            mensaje= mensaje +" Método de pago incorrecto o faltante. Cargar desde contactos->Contabilidad->Método de pago. Pago no creado(crear manualmente)\n"
            return mensaje

        if( len(res_bank_partner) == 1 and res_bank_partner.partner_id.id):
            pago=self.env['account.payment.group'].create({
                    'partner_id':res_bank_partner.partner_id.id,
                    'state':'draft',
                    'display_name':'A','pop_up':True,
                    'partner_type':'customer',
                    'account_debit_automatic_id': accountDebitAutomatic.id,
                    'state':'draft'
                    })
        for line in vals:
            if not line['amount_total']:
                mensaje= mensaje +' Monto faltante o incorrecto.('+str(line['amount_total'])+')\n'
            a_pagar=self.env['account.payment'].create(
                    {
                    'payment_type':'inbound',
                    'partner_type':'customer',
                    'partner_id': res_bank_partner.partner_id.id,
                    'destination_account_id': accountDebitAutomatic.payment_account.id,
                    'journal_id': accountDebitAutomatic.payment_journal.id,
                    'payment_method_id':1,
                    'amount': line['amount_total'],
                    'date': line['date'],
                    'currency_id': currency.id,
                    'ref': 'DA',
                    'payment_group_id':pago.id,
                     })

            if validar:
                # ''' draft -> posted '''
                try:
                    a_pagar.move_id._post(soft=False)
                    mensaje=mensaje+' - '+str(a_pagar.name) +' -> Validado.\n'
                except:
                    mensaje=mensaje +'No se pudo validar.(pago creado como borrador)\n'
        return mensaje

class ResPartner(models.Model):
    _inherit = 'res.partner'

    method_id = fields.Many2one('account.payment.method', 'Método de pago automático')

class ResCompany(models.Model):
    _inherit = 'res.company'

    debit_number = fields.Char('Número de Débito')

class AccountPaymentGroup(models.Model):
    _inherit = 'account.payment.group'

    account_debit_automatic_id = fields.Many2one('account.debit.automatic', 'Método de pago automático')
