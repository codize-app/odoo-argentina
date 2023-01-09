# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
from odoo import models, fields, api, _
from odoo.exceptions import Warning, ValidationError
import json

class AccountVatLedgerXlsx(models.AbstractModel):
    _name = 'report.l10n_ar_ledger.account_vat_ledger_xlsx'
    _inherit = 'report.report_xlsx.abstract'
    _description = 'Report VAT Ledger XLSX'

    def generate_xlsx_report(self, workbook, data, vat_ledger):
        if vat_ledger.invoice_ids:
            report_name = 'IVA Ventas'
            if vat_ledger.type == 'purchase':
                report_name = 'IVA Compras'

            sheet = workbook.add_worksheet(report_name[:31])
            h = "#"
            money_format = workbook.add_format({'num_format': "$ 0" + h + h + '.' + h + h + ',' + h + h})
            bold = workbook.add_format({'bold': True})
            sheet.write(1, 0, vat_ledger.display_name, bold)

            titles = ['Fecha','Razón Social','CUIT','Responsabilidad AFIP','Tipo de Comprobante','Nro Comprobante','Neto gravado','Neto no gravado','Neto exento','IVA 27%','IVA 21%','IVA 10.5%','Percepción de IVA','Perc IIBB CABA','Perc IIBB ARBA','Perc IIBB Santa Fe','Perc IIBB Cordoba','Perc IIBB Mendoza','Perc IIBB La Pampa','Perc IIBB Jujuy','Perc IIBB Salta','Perc IIBB Formosa','Perc IIBB Misiones','Perc IIBB Corrientes','Perc IIBB Entre Rios','Perc IIBB San Luis','Perc IIBB Catamarca','Perc IIBB Neuquen','Perc IIBB Chubut','Perc IIBB Rio Negro','Perc IIBB Santa Cruz','Perc IIBB Tierra del Fuego','Perc IIBB Tucuman','Impuestos Internos','Otros','Total gravado','Total']
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
                
                taxes = json.loads(obj.tax_totals_json)['groups_by_subtotal']['Importe libre de impuestos']

                # Neto gravado
                netoG = 0
                for tax in taxes:
                    if tax['tax_group_name'] == 'IVA 21%' or tax['tax_group_name'] == 'IVA 10.5%' or tax['tax_group_name'] == 'IVA 27%':
                        netoG = netoG + tax['tax_group_base_amount']
                if obj.l10n_latam_document_type_id.internal_type == 'credit_note':
                    netoG = netoG * -1
                sheet.write(row + index, 6, netoG, money_format) # Neto gravado

                # Neto no gravado
                netoN = 0
                for tax in taxes:
                    if tax['tax_group_name'] == 'IVA No Gravado' or tax['tax_group_name'] == 'IVA 0%':
                        netoN = netoN + tax['tax_group_base_amount']
                if obj.l10n_latam_document_type_id.internal_type == 'credit_note':
                    netoN = netoN * -1
                sheet.write(row + index, 7, netoN, money_format) # Neto no gravado

                # Neto exento
                netoE = 0
                for tax in taxes:
                    if tax['tax_group_name'] == 'IVA Exento':
                        netoE = netoE + tax['tax_group_base_amount']
                if obj.l10n_latam_document_type_id.internal_type == 'credit_note':
                    netoE = netoE * -1
                sheet.write(row + index, 8, netoE, money_format) # Neto exento

                # IVA 27
                iva27 = 0
                for tax in taxes:
                    if tax['tax_group_name'] == 'IVA 27%':
                        iva27 = iva27 + tax['tax_group_amount']
                if obj.l10n_latam_document_type_id.internal_type == 'credit_note':
                    iva27 = iva27 * -1
                sheet.write(row + index, 9, iva27, money_format) # IVA 27

                # IVA 21
                iva21 = 0
                for tax in taxes:
                    if tax['tax_group_name'] == 'IVA 21%':
                        iva21 = iva21 + tax['tax_group_amount']
                if obj.l10n_latam_document_type_id.internal_type == 'credit_note':
                    iva21 = iva21 * -1
                sheet.write(row + index, 10, iva21, money_format) # IVA 21

                # IVA 10.5
                iva105 = 0
                for tax in taxes:
                    if tax['tax_group_name'] == 'IVA 10.5%':
                        iva105 = iva105 + tax['tax_group_amount']
                if obj.l10n_latam_document_type_id.internal_type == 'credit_note':
                    iva105 = iva105 * -1
                sheet.write(row + index, 11, iva105, money_format) # IVA 10.5

                # Precepciones IVA
                periva = 0
                for tax in taxes:
                    if tax['tax_group_name'] == 'Percepción de IVA':
                        periva = periva + tax['tax_group_amount']
                if obj.l10n_latam_document_type_id.internal_type == 'credit_note':
                    periva = periva * -1
                sheet.write(row + index, 12, periva, money_format) # Precepciones IVA
                
                # Percepciones IIBB CABA
                percaba = 0
                for tax in taxes:
                    if tax['tax_group_name'] == 'Perc IIBB CABA':
                        percaba = percaba + tax['tax_group_amount']
                if obj.l10n_latam_document_type_id.internal_type == 'credit_note':
                    percaba = percaba * -1
                sheet.write(row + index, 13, percaba, money_format) # Percepciones IIBB CABA
                
                # Percepciones IIBB Buenos Aires
                perarba = 0
                for tax in taxes:
                    if tax['tax_group_name'] == 'Perc IIBB ARBA':
                        perarba = perarba + tax['tax_group_amount']
                if obj.l10n_latam_document_type_id.internal_type == 'credit_note':
                    perarba = perarba * -1
                sheet.write(row + index, 14, perarba, money_format) # Percepciones IIBB Buenos Aires

                #  Percepciones IIBB Santa Fe
                perstafe = 0
                for tax in taxes:
                    if tax['tax_group_name'] == 'Perc IIBB Santa Fe':
                        perstafe = perstafe + tax['tax_group_amount']
                if obj.l10n_latam_document_type_id.internal_type == 'credit_note':
                    perstafe = perstafe * -1
                sheet.write(row + index, 15, perstafe, money_format) # Percepciones IIBB Santa Fe
                
                #  Percepciones IIBB Córdoba
                percordoba = 0
                for tax in taxes:
                    if tax['tax_group_name'] == 'Perc IIBB Córdoba':
                        percordoba = percordoba + tax['tax_group_amount']
                if obj.l10n_latam_document_type_id.internal_type == 'credit_note':
                    percordoba = percordoba * -1
                sheet.write(row + index, 16, percordoba, money_format) # Percepciones IIBB Córdoba

                #  Percepciones IIBB Mendoza
                permend = 0
                for tax in taxes:
                    if tax['tax_group_name'] == 'Perc IIBB Mendoza':
                        permend = permend + tax['tax_group_amount']
                if obj.l10n_latam_document_type_id.internal_type == 'credit_note':
                    permend = permend * -1
                sheet.write(row + index, 17, permend, money_format) # Percepciones IIBB Mendoza

                #  Percepciones IIBB La Pampa
                perpampa = 0
                for tax in taxes:
                    if tax['tax_group_name'] == 'Perc IIBB La Pampa':
                        perpampa = perpampa + tax['tax_group_amount']
                if obj.l10n_latam_document_type_id.internal_type == 'credit_note':
                    perpampa = perpampa * -1
                sheet.write(row + index, 18, perpampa, money_format) # Percepciones IIBB La Pampa
               
                #  Percepciones IIBB La Pampa
                perju = 0
                for tax in taxes:
                    if tax['tax_group_name'] == 'Perc IIBB Jujuy':
                        perju = perju + tax['tax_group_amount']
                if obj.l10n_latam_document_type_id.internal_type == 'credit_note':
                    perju = perju * -1
                sheet.write(row + index, 19, perju, money_format) # Percepciones IIBB Jujuy
                
                #  Percepciones IIBB Salta
                persalta = 0
                for tax in taxes:
                    if tax['tax_group_name'] == 'Perc IIBB Salta':
                        persalta = persalta + tax['tax_group_amount']
                if obj.l10n_latam_document_type_id.internal_type == 'credit_note':
                    persalta = persalta * -1
                sheet.write(row + index, 20, persalta, money_format) # Percepciones IIBB Salta
                
                #  Percepciones IIBB Formosa
                performosa = 0
                for tax in taxes:
                    if tax['tax_group_name'] == 'Perc IIBB Formosa':
                        performosa = performosa + tax['tax_group_amount']
                if obj.l10n_latam_document_type_id.internal_type == 'credit_note':
                    performosa = performosa * -1
                sheet.write(row + index, 21, performosa, money_format) # Percepciones IIBB Formosa

                #  Percepciones IIBB Misiones
                permis = 0
                for tax in taxes:
                    if tax['tax_group_name'] == 'Perc IIBB Misiones':
                        permis = permis + tax['tax_group_amount']
                if obj.l10n_latam_document_type_id.internal_type == 'credit_note':
                    permis = permis * -1
                sheet.write(row + index, 22, permis, money_format) # Percepciones IIBB Misiones

                #  Percepciones IIBB Corrientes
                percorr = 0
                for tax in taxes:
                    if tax['tax_group_name'] == 'Perc IIBB Corrientes':
                        percorr = percorr + tax['tax_group_amount']
                if obj.l10n_latam_document_type_id.internal_type == 'credit_note':
                    percorr = percorr * -1
                sheet.write(row + index, 23, percorr, money_format) # Percepciones IIBB Corrientes

                #  Percepciones IIBB Entre Rios
                perent = 0
                for tax in taxes:
                    if tax['tax_group_name'] == 'Perc IIBB Entre Rios':
                        perent = perent + tax['tax_group_amount']
                if obj.l10n_latam_document_type_id.internal_type == 'credit_note':
                    perent = perent * -1
                sheet.write(row + index, 24, perent, money_format) # Percepciones IIBB Entre Rios

                #  Percepciones IIBB San Luis
                persanl = 0
                for tax in taxes:
                    if tax['tax_group_name'] == 'Perc IIBB San Luis':
                        persanl = persanl + tax['tax_group_amount']
                if obj.l10n_latam_document_type_id.internal_type == 'credit_note':
                    persanl = persanl * -1
                sheet.write(row + index, 25, persanl, money_format) # Percepciones IIBB San Luis
                
                #  Percepciones IIBB Catamarca
                percat = 0
                for tax in taxes:
                    if tax['tax_group_name'] == 'Perc IIBB Catamarca':
                        percat = percat + tax['tax_group_amount']
                if obj.l10n_latam_document_type_id.internal_type == 'credit_note':
                    percat = percat * -1
                sheet.write(row + index, 26, percat, money_format) # Percepciones IIBB Catamarca
                
                #  Percepciones IIBB Neuquen
                perneu = 0
                for tax in taxes:
                    if tax['tax_group_name'] == 'Perc IIBB Neuquen':
                        perneu = perneu + tax['tax_group_amount']
                if obj.l10n_latam_document_type_id.internal_type == 'credit_note':
                    perneu = perneu * -1
                sheet.write(row + index, 27, perneu, money_format) # Percepciones IIBB Neuquen
                
                #  Percepciones IIBB Chubut
                perchu = 0
                for tax in taxes:
                    if tax['tax_group_name'] == 'Perc IIBB Chubut':
                        perchu = perchu + tax['tax_group_amount']
                if obj.l10n_latam_document_type_id.internal_type == 'credit_note':
                    perchu = perchu * -1
                sheet.write(row + index, 28, perchu, money_format) # Percepciones IIBB Chubut
                
                #  Percepciones IIBB Rio Negro
                perrine = 0
                for tax in taxes:
                    if tax['tax_group_name'] == 'Perc IIBB Rio Negro':
                        perrine = perrine + tax['tax_group_amount']
                if obj.l10n_latam_document_type_id.internal_type == 'credit_note':
                    perrine = perrine * -1
                sheet.write(row + index, 29, perrine, money_format) # Percepciones IIBB Rio Negro
                
                #  Percepciones IIBB Santa Cruz
                perstacr = 0
                for tax in taxes:
                    if tax['tax_group_name'] == 'Perc IIBB Santa Cruz':
                        perstacr = perstacr + tax['tax_group_amount']
                if obj.l10n_latam_document_type_id.internal_type == 'credit_note':
                    perstacr = perstacr * -1
                sheet.write(row + index, 30, perstacr, money_format) # Percepciones IIBB Santa Cruz
                
                #  Percepciones IIBB Tierra del Fuego
                pertie = 0
                for tax in taxes:
                    if tax['tax_group_name'] == 'Perc IIBB Tierra del Fuego':
                        pertie = pertie + tax['tax_group_amount']
                if obj.l10n_latam_document_type_id.internal_type == 'credit_note':
                    pertie = pertie * -1
                sheet.write(row + index, 31, pertie, money_format) # Percepciones IIBB Tierra del Fuego
                
                #  Percepciones IIBB Tucuman
                pertuc = 0
                for tax in taxes:
                    if tax['tax_group_name'] == 'Perc IIBB Tucuman':
                        pertuc = pertuc + tax['tax_group_amount']
                if obj.l10n_latam_document_type_id.internal_type == 'credit_note':
                    pertuc = pertuc * -1
                sheet.write(row + index, 32, pertuc, money_format) # Percepciones IIBB Tucuman
                
                #  Impuestos Internos
                impinter = 0
                for tax in taxes:
                    if tax['tax_group_name'] == 'Impuestos Internos':
                        impinter = impinter + tax['tax_group_amount']
                if obj.l10n_latam_document_type_id.internal_type == 'credit_note':
                    impinter = impinter * -1
                sheet.write(row + index, 33, impinter, money_format) # Impuestos Internos
                
                # Otros
                otros = 0
                for tax in taxes:
                    if tax['tax_group_name'] not in titles:
                        otros = otros + tax['tax_group_amount']
                if obj.l10n_latam_document_type_id.internal_type == 'credit_note':
                    otros = otros * -1
                sheet.write(row + index, 34, otros, money_format) # Otros

                sheet.write(row + index, 35, netoG + iva27 + iva21 + iva105 + otros, money_format) # Total gravado
                sheet.write(row + index, 36, obj.amount_total, money_format) # Total

                index += 1

