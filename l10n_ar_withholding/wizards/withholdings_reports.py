import logging
import json
from odoo import api, fields, models, _

_logger = logging.getLogger(__name__)

class WithholdingsReports(models.TransientModel):
    _name="ar.withholdings.reports"
    _description="Withholdings Reports"

    type_report = fields.Selection([('withholdings', 'Retenciones y Percepciones')], string="Reporte", default='withholdings')
    date_from = fields.Date (string="Fecha Inicio")
    date_to = fields.Date (string="Fecha Fin")

    def download_xls(self):
        return {
            'type': 'ir.actions.act_url',
            'url': '/withholding/report/%s' % (self.id),
            'target': 'new',
        }

    def print_report(self):
        if self.type_report == 'withholdings':
            invoices_ids = self.env['account.move'].search([('state','=','posted'),('move_type','in',['out_invoice','out_refund']),('invoice_date','>=',self.date_from),('invoice_date','<=',self.date_to)])
            payments_ids = self.env['account.payment.group'].search([('state','=','posted'),('payment_date','>=',self.date_from),('payment_date','<=',self.date_to)])
            payments_whit_withholdings = []
            payments_whit_profit_withholdings = []
            invoices_whit_perceptions = []
            _valsP = [] 
            _valsPG = [] 

            #Percepciones en Facturas
            for invoice in invoices_ids:
                taxes = json.loads(invoice.tax_totals_json)['groups_by_subtotal']['Importe libre de impuestos']
                for tax in taxes:
                    if 'Per' in tax['tax_group_name']  or 'PER' in tax['tax_group_name'] or 'per' in tax['tax_group_name']:
                        _valsI = []     
                        _valsI.append(tax['tax_group_name'])#Tipo
                        _valsI.append(invoice.name)#Factura
                        _valsI.append(invoice.invoice_date)#Fecha
                        _valsI.append(invoice.partner_id.name)#Cliente/Proveedor
                        _valsI.append(invoice.partner_id.vat)#CUIT
                        _valsI.append(invoice.partner_id.state_id.name)#Provincia
                        if invoice.currency_id.name != 'ARS': #Multimoneda
                            _valsI.append(tax['tax_group_amount'] * invoice.l10n_ar_currency_rate)#Total
                            _valsI.append(tax['tax_group_base_amount'] * invoice.l10n_ar_currency_rate)#Monto imponible
                        else:
                            _valsI.append(tax['tax_group_amount'])#Total
                            _valsI.append(tax['tax_group_base_amount'])#Monto imponible
                        _valsI.append(invoice.partner_id.iibb_number)#Ingresos Brutos       
#
                        invoices_whit_perceptions.append(_valsI)
            
            #Retenciones en pagos
            for payment in payments_ids:
                for pline in payment.payment_ids:
                    if pline.print_withholding:
                        if pline.tax_withholding_id.withholding_type == 'tabla_ganancias':
                            _valsPG = []                       
                            _valsPG.append(pline.tax_withholding_id.name)#Tipo
                            _valsPG.append(pline.withholding_number)#Numero
                            _valsPG.append(pline.date)#Fecha
                            _valsPG.append(payment.partner_id.name)#Cliente/Proveedor
                            _valsPG.append(payment.partner_id.vat)#CUIT
                            _valsPG.append(payment.partner_id.state_id.name)#Provincia
                            _valsPG.append(pline.signed_amount)#Total
                            _valsPG.append(payment.display_name)#Num de pago
                            _tpww = 0
                            for mm in payment.matched_move_line_ids:
                                _tpww += mm.move_id.amount_untaxed
                            _valsPG.append(_tpww)#Monto imponible
                            _valsPG.append(payment.partner_id.iibb_number)#Ingresos Brutos
                            
                            payments_whit_profit_withholdings.append(_valsPG)
                            
                        else:
                            _valsP = []                       
                            _valsP.append(pline.tax_withholding_id.name)#Tipo
                            _valsP.append(pline.withholding_number)#Numero
                            _valsP.append(pline.date)#Fecha
                            _valsP.append(payment.partner_id.name)#Cliente/Proveedor
                            _valsP.append(payment.partner_id.vat)#CUIT
                            _valsP.append(payment.partner_id.state_id.name)#Provincia
                            _valsP.append(pline.signed_amount)#Total
                            _valsP.append(payment.display_name)#Num de pago
                            _tww = 0
                            for m in payment.matched_move_line_ids:
                                _tww += m.move_id.amount_untaxed
                            _valsP.append(_tww)#Monto imponible
                            _valsP.append(payment.partner_id.iibb_number)#Ingresos Brutos

                            payments_whit_withholdings.append(_valsP)

            data = {
                'from_data' : self.read()[0],
                'percepciones_ids' : invoices_whit_perceptions,
                'retenciones_ids' : payments_whit_withholdings,
                'retenciones_gan_ids' : payments_whit_profit_withholdings
            }
            return self.env.ref('l10n_ar_withholding.action_withholdings_report_general').sudo().with_context(landscape=True).report_action(self, data=data)
