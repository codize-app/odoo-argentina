# -*- coding: utf-8 -*-
import logging
from odoo import http
from odoo.http import content_disposition, request
from datetime import datetime
from odoo.exceptions import ValidationError
import io
import xlsxwriter
import json
 
_logger = logging.getLogger(__name__)
class WithholdingsReportsController(http.Controller):
    @http.route([
        '/withholding/report/<model("ar.withholdings.reports"):wizard>',
    ], type='http', auth="user", csrf=False)
    def get_withholding_excel_report(self,wizard=None,**args):
         
        response = request.make_response(
                    None,
                    headers=[
                        ('Content-Type', 'application/vnd.ms-excel'),
                        ('Content-Disposition', content_disposition('Reporte de Ret/Per' + '.xlsx'))
                    ]
                )
 
        # Crea workbook
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
 
        # Estilos de celdas
        title_style = workbook.add_format({'font_name': 'Times', 'font_size': 14, 'bold': True, 'align': 'center','bg_color': 'yellow', 'left': 1, 'bottom':1, 'right':1, 'top':1})
        header_style = workbook.add_format({'font_name': 'Times', 'bold': True, 'left': 1, 'bottom':1, 'right':1, 'top':1, 'align': 'center'})
        text_style = workbook.add_format({'font_name': 'Times', 'left': 1, 'bottom':1, 'right':1, 'top':1, 'align': 'left'})
        number_style = workbook.add_format({'font_name': 'Times', 'left': 1, 'bottom':1, 'right':1, 'top':1, 'align': 'right'})
        date_style = workbook.add_format({'num_format': 'dd/mm/yy','font_name': 'Times', 'left': 1, 'bottom':1, 'right':1, 'top':1, 'align': 'right'})
        currency_style = workbook.add_format({'num_format':'$#,##0.00','font_name': 'Times', 'left': 1, 'bottom':1, 'right':1, 'top':1, 'align': 'right'})
 

        ### RETENCIONES ###
        # Crea worksheet
        sheet = workbook.add_worksheet("Retenciones")
        # Orientacion landscape
        sheet.set_landscape()
        # Tamaño de papel A4
        sheet.set_paper(9)
        # Margenes
        sheet.set_margins(0.5,0.5,0.5,0.5)

        # Configuracion de ancho de columnas
        sheet.set_column('A:A', 10)
        sheet.set_column('B:B', 30)
        sheet.set_column('C:C', 20)
        sheet.set_column('D:D', 20)
        sheet.set_column('E:E', 20)
        sheet.set_column('F:F', 20)
        sheet.set_column('G:G', 20)
        sheet.set_column('H:H', 20)
        sheet.set_column('I:I', 20)
        sheet.set_column('J:J', 20)

        # Titulos de reporte
        sheet.merge_range('A1:F1', 'Retenciones', title_style)
         
        # Títulos de columnas
        sheet.write(1, 0, 'Fecha', header_style)
        sheet.write(1, 1, 'Cliente', header_style)
        sheet.write(1, 2, 'Impuesto', header_style)
        sheet.write(1, 3, 'N Ret', header_style)
        sheet.write(1, 4, 'Base', header_style)
        sheet.write(1, 5, 'Monto Ret', header_style)

        row = 2

        #Buscamos los pagos que su diario sea de tipo deretencion
        company_id = request._context.get('company_id', request.env.user.company_id.id)
        payments_ids = request.env['account.payment'].search([('company_id', '=', company_id),('tax_withholding_id','!=',False),('date','>=',wizard.date_from),('date','<=',wizard.date_to)])
        #Variables temporales  
        _withholdings = []
        _withholding = []
        _withholding_categories = []

        for payment in payments_ids:

            _withholdings.append({'impuesto': payment.tax_withholding_id.name,
                                    'Fecha': payment.date,
                                    'Cliente': payment.partner_id.name,
                                    'NRet': payment.withholding_number,
                                    'Base': payment.withholding_base_amount,
                                    'MontoRet': payment.amount})
            if not payment.tax_withholding_id.name in _withholding_categories:
                _vals={'impuesto' : payment.tax_withholding_id.name,
                        'Base': payment.withholding_base_amount,
                        'MontoRet': payment.amount}
                _withholding.append(_vals)
                _withholding_categories.append(payment.tax_withholding_id.name)
            # En el caso de que ya se haya cargado la categoria se suman los totales del producto de dicha categoria
            else:
                for ret in _withholding:
                    if ret['impuesto'] == payment.tax_withholding_id.name:
                        ret['Base'] = ret['Base'] + payment.withholding_base_amount
                        ret['MontoRet'] = ret['MontoRet'] + payment.amount

        #Ordenamos Retenciones por nombre de impuesto
        ordenado = sorted(_withholdings, key=lambda nom : nom['Fecha'])
        _BaseTotal = 0
        _MontoRetTotal = 0

        for o in ordenado:
            # Documento de categorias
            sheet.write(row, 0, o['Fecha'], date_style) 
            sheet.write(row, 1, o['Cliente'], text_style) 
            sheet.write(row, 2, o['impuesto'], text_style) 
            sheet.write(row, 3, o['NRet'], currency_style)
            sheet.write(row, 4, o['Base'], currency_style)
            sheet.write(row, 5, o['MontoRet'], currency_style)

            _BaseTotal += float(o['Base'])
            _MontoRetTotal += float(o['MontoRet'])

            row += 1

        # Imprimiendo totales
        sheet.write(row, 4, _BaseTotal, currency_style)
        sheet.write(row, 5, _MontoRetTotal, currency_style)

        sheet.merge_range('H1:J1', 'Totales por Impuesto', title_style)
        row = 1
        # Títulos de columnas
        sheet.write(row, 7, 'Impuesto', header_style)
        sheet.write(row, 8, 'Base', header_style)
        sheet.write(row, 9, 'Monto Ret', header_style)
        for w in _withholding:
            row += 1
            # Documento de categorias
            sheet.write(row, 7, w['impuesto'], text_style) 
            sheet.write(row, 8, w['Base'], currency_style)
            sheet.write(row, 9, w['MontoRet'], currency_style)

        ### PERCEPCIONES ###
        # Crea worksheet
        sheet = workbook.add_worksheet("Percepciones")
        # Orientacion landscape
        sheet.set_landscape()
        # Tamaño de papel A4
        sheet.set_paper(9)
        # Margenes
        sheet.set_margins(0.5,0.5,0.5,0.5)

        # Configuracion de ancho de columnas
        sheet.set_column('A:A', 10)
        sheet.set_column('B:B', 30)
        sheet.set_column('C:C', 25)
        sheet.set_column('D:D', 20)
        sheet.set_column('E:E', 20)
        sheet.set_column('F:F', 20)
        sheet.set_column('G:G', 10)
        sheet.set_column('H:H', 20)
        sheet.set_column('I:I', 20)
        sheet.set_column('J:J', 20)

        # Titulos de reporte
        sheet.merge_range('A1:F1', 'Percepciones', title_style)
        sheet.merge_range('H1:J1', 'Percepciones por Impuesto', title_style)
         
        # Títulos de columnas
        sheet.write(1, 0, 'Fecha', header_style)
        sheet.write(1, 1, 'Cliente', header_style)
        sheet.write(1, 2, 'Factura', header_style)
        sheet.write(1, 3, 'Impuesto', header_style)
        sheet.write(1, 4, 'Base', header_style)
        sheet.write(1, 5, 'Monto Ret', header_style)

        sheet.write(1, 7, 'Impuesto', header_style)
        sheet.write(1, 8, 'Base', header_style)
        sheet.write(1, 9, 'Monto Ret', header_style)
        row = 1


        _precepcion = []
        _precepcion_categories = []
        _precepciones = []
        _baseTotal = 0
        _montoPerTotal = 0

        invoices = request.env['account.move'].search([('company_id', '=', company_id),('move_type','in',['out_invoice','out_refund']),('state','=','posted'),('invoice_date','<=',wizard.date_to),('invoice_date','>=',wizard.date_from)],order='invoice_date asc')
        for invoice in invoices:
            taxes = json.loads(invoice.tax_totals_json)['groups_by_subtotal']['Importe libre de impuestos']
            for tax in taxes:
                if 'Perc' in tax['tax_group_name']:
                    if invoice.move_type == 'out_invoice':
                        _base = tax['tax_group_base_amount'] if invoice.currency_id.name == 'ARS' else float(tax['tax_group_base_amount']) * invoice.l10n_ar_currency_rate #Multimoneda
                        _moto_per = tax['tax_group_amount'] if invoice.currency_id.name == 'ARS' else float(tax['tax_group_amount']) * invoice.l10n_ar_currency_rate #Multimoneda
                    else:
                        _base = (float(tax['tax_group_base_amount']) * -1) if invoice.currency_id.name == 'ARS' else ((float(tax['tax_group_base_amount']) * invoice.l10n_ar_currency_rate) * -1) #Multimoneda
                        _moto_per = (float(tax['tax_group_amount']) * -1) if invoice.currency_id.name == 'ARS' else ((float(tax['tax_group_amount']) * invoice.l10n_ar_currency_rate) * -1) #Multimoneda

                    _precepciones.append({'Fecha': invoice.invoice_date,
                                            'Cliente': invoice.partner_id.name,
                                            'Factura': invoice.name,
                                            'Impuesto': tax['tax_group_name'],
                                            'Base':_base,
                                            'Monto Perc': _moto_per})

                    _baseTotal += _base
                    _montoPerTotal += _moto_per

                    if not tax['tax_group_name'] in _precepcion_categories:
                        _vals={'impuesto' : tax['tax_group_name'],
                                'Base': _base,
                                'MontoPer': _moto_per}
                        _precepcion.append(_vals)
                        _precepcion_categories.append(tax['tax_group_name'])
                    # En el caso de que ya se haya cargado la categoria se suman los totales del producto de dicha categoria
                    else:
                        for per in _precepcion:
                            if per['impuesto'] == tax['tax_group_name']:
                                per['Base'] = per['Base'] + _base
                                per['MontoPer'] = per['MontoPer'] + _moto_per

        _precepciones = sorted(_precepciones, key=lambda nom : nom['Fecha'])
        for p in _precepciones:
            row += 1
            sheet.write(row, 0, p['Fecha'], date_style) 
            sheet.write(row, 1, p['Cliente'], text_style)
            sheet.write(row, 2, p['Factura'], text_style)
            sheet.write(row, 3, p['Impuesto'], text_style)
            sheet.write(row, 4, p['Base'], currency_style)
            sheet.write(row, 5, p['Monto Perc'], currency_style)
        
        #TOTALES
        row += 1
        sheet.write(row, 4, _baseTotal, currency_style)
        sheet.write(row, 5, _montoPerTotal, currency_style)
        
        row = 1

        for pc in _precepcion:
            row += 1
            sheet.write(row, 7, pc['impuesto'], text_style)
            sheet.write(row, 8, pc['Base'], currency_style)
            sheet.write(row, 9, pc['MontoPer'], currency_style)


        # Devuelve el archivo de Excel como respuesta, para que el navegador pueda descargarlo 
        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()
 
        return response