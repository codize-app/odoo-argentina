# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
from odoo import models, fields, api, _
from odoo.exceptions import Warning, ValidationError

class AccountVatLedgerXlsx(models.AbstractModel):
    _name = 'report.l10n_ar_ledger.account_vat_ledger_xlsx'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, vat_ledger):
        if vat_ledger.invoice_ids:
            report_name = 'IVA Ventas'
            if vat_ledger.type == 'purchase':
                report_name = 'IVA Compras'

            sheet = workbook.add_worksheet(report_name[:31])
            h = "#"
            money_format = workbook.add_format({'num_format': "$ " + h + h + '.' + h + h + ',' + h + h})
            bold = workbook.add_format({'bold': True})
            sheet.write(1, 0, vat_ledger.display_name, bold)

            titles = ['Fecha','Razón Social','CUIT','Responsabilidad AFIP','Tipo de Comprobante','Nro Comprobante','Neto gravado','Neto no gravado','Neto exento','IVA 27','IVA 21','IVA 10.5','Otros','Total gravado','Total']
            for i,title in enumerate(titles):
                sheet.write(3, i, title, bold)

            row = 4
            index = 0
            sheet.set_column('A:F', 30)

            for i,obj in enumerate(vat_ledger.invoice_ids):
                sheet.write(row + index, 0, obj.invoice_date.strftime("%Y-%m-%d")) # Fecha
                sheet.write(row + index, 1, obj.partner_id.name) # Razón Social
                if obj.partner_id.vat: # CUIT
                    sheet.write(row + index, 2, obj.partner_id.vat)
                else:
                    sheet.write(row + index, 2, '-')
                sheet.write(row + index, 3, obj.partner_id.l10n_ar_afip_responsibility_type_id.name) # Responsabilidad AFIP
                sheet.write(row + index, 4, obj.l10n_latam_document_type_id.name) # Tipo de Comprobante
                sheet.write(row + index, 5, obj.name) # Nro Comprobante

                netoG = 0
                for tax in obj.amount_by_group:
                    if tax[0] == 'IVA 21%' or tax[0] == 'IVA 10.5%' or tax[0] == 'IVA 27%':
                        netoG = netoG + tax[2]
                if obj.l10n_latam_document_type_id.internal_type == 'credit_note':
                    netoG = netoG * -1
                sheet.write(row + index, 6, netoG, money_format) # Neto gravado



                index += 1
