from odoo import models, fields, api
import logging
_logger = logging.getLogger(__name__)


class ProductTemplate(models.AbstractModel):
    _name = 'report.l10n_ar_debit_automatic.debit_automatic_payments_xlsx'
    _inherit = 'report.report_xlsx.abstract'


    def generate_xlsx_report(self, workbook, data, debits_automatic):
        _logger.info(debits_automatic)
        for debit in debits_automatic:
            datos = self.env['account.payment.group'].search([('account_debit_automatic_id','=',debit.id)])
            sheet = workbook.add_worksheet(str(debit.name))
            row=0
            bold = workbook.add_format({'bold': True,'valign':'vcenter','align':'center'})
            date_format = workbook.add_format({'num_format': 'dd/mm/yy'})
            currency_format = workbook.add_format({'num_format': '$#,##0.00'})

            sheet.write(row, 0, 'Contacto', bold)
            sheet.set_column(0,len('Contacto'), 20)
            sheet.write(row, 1, 'Fecha de cobro', bold)
            sheet.set_column(1,len('Fecha de cobro'), 20)
            sheet.write(row, 2, 'Monto', bold)
            sheet.set_column(2,len('Monto'), 20)

            for account_payment_group in datos:
                for payment in account_payment_group.payment_ids:
                    row=row+1
                    sheet.write(row, 0, account_payment_group.partner_id.name)
                    sheet.write(row, 1, payment.date,date_format)
                    sheet.write(row, 2, payment.amount,currency_format)

