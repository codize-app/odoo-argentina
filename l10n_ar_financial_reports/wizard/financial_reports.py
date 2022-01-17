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
            invoices_ids = self.env['account.move'].search_read([('move_type','in',['out_invoice','out_refund']),('invoice_date','>=',self.date_from),('invoice_date','<=',self.date_to)])
            data = {
                'from_data' : self.read()[0],
                'invoices_ids' : invoices_ids
            }
            return self.env.ref('l10n_ar_financial_reports.action_report_iva_sale').sudo().with_context(landscape=True).report_action(self, data=data)
        elif self.type_report == 'ivapurchase':
            invoices_ids = self.env['account.move'].search_read([('move_type','in',['in_invoice','in_refund']),('date','>=',self.date_from),('date','<=',self.date_to)])
            data = {
                'from_data' : self.read()[0],
                'invoices_ids' : invoices_ids
            }
            return self.env.ref('l10n_ar_financial_reports.action_report_iva_purchase').sudo().with_context(landscape=True).report_action(self, data=data)
