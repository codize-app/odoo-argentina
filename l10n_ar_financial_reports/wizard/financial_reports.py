from odoo import api, fields, models, _

class FinancialReports(models.TransientModel):
    _name="ar.financial.reports"
    _description="Financial Reports"

    type_report = fields.Selection([('ivasale', 'Iva Venta'),
                                    ('ivapurchase', 'Iva Compra')], string="Reporte", default='ivasale')
    date_from = fields.Date (string="Fecha Inicio")
    date_to = fields.Date (string="Fecha Fin")

    def print_report(self):
        if self.type_report == 'ivasale':
            #invoices_ids = self.env['account.move'].search_read([('move_type','in',['out_invoice','out_refund']),('invoice_date','>=',self.date_from),('invoice_date','<=',self.date_to)])
            #CAMBIOS POR MARITO - se agregaron los fields necesarios para el reporte
            invoices_ids = self.env['account.move'].search_read([('move_type','in',['out_invoice','out_refund']),('invoice_date','>=',self.date_from),('invoice_date','<=',self.date_to)],['id', 'name','l10n_ar_afip_responsibility_type_id','invoice_date','invoice_partner_display_name','document_partner','amount_total','amount_untaxed_signed','iva10','iva21','iva27','no_gravado','iva_exento','move_type'])
            data = {
                'from_data' : self.read()[0],
                'invoices_ids' : invoices_ids
            }
            return self.env.ref('l10n_ar_financial_reports.action_report_iva_sale').sudo().with_context(landscape=True).report_action(self, data=data)
        elif self.type_report == 'ivapurchase':
            #invoices_ids = self.env['account.move'].search_read([('move_type','in',['in_invoice','in_refund']),('date','>=',self.date_from),('date','<=',self.date_to)])
            #CAMBIOS POR MARITO - se agregaron los fields necesarios para el reporte
            invoices_ids = self.env['account.move'].search_read([('move_type','in',['in_invoice','in_refund']),('date','>=',self.date_from),('date','<=',self.date_to)],['id', 'name','l10n_ar_afip_responsibility_type_id','l10n_latam_amount_untaxed','invoice_date','invoice_partner_display_name','document_partner','amount_total','amount_untaxed_signed','iva10','iva21','iva27','no_gravado','iva_exento','iva_no_corresponde','move_type','amount_by_group'])
            data = {
                'from_data' : self.read()[0],
                'invoices_ids' : invoices_ids
            }
            return self.env.ref('l10n_ar_financial_reports.action_report_iva_purchase').sudo().with_context(landscape=True).report_action(self, data=data)
