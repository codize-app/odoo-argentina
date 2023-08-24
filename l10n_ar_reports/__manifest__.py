# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Argentinian Accounting Reports',
    'version': '1.0',
    'author': 'ADHOC SA',
    'category': 'Accounting/Localizations/Reporting',
    'summary': 'Reporting for Argentinian Localization',
    'description': """
* Add VAT Book report which is a legal requirement in Argentina and that holds the VAT detail info of sales or purchases made in a period of time.
* Add a VAT summary report that is used to analyze invoicing
* Add Digital VAT Book functionality that let us generate TXT files to import in AFIP. The ones we implement are:

    * LIBRO_IVA_DIGITAL_VENTAS_CBTE
    * LIBRO_IVA_DIGITAL_VENTAS_ALICUOTAS
    * LIBRO_IVA_DIGITAL_COMPRAS_CBTE
    * LIBRO_IVA_DIGITAL_COMPRAS_ALICUOTAS
    * LIBRO_IVA_DIGITAL_IMPORTACION_BIENES_ALICUOTA

Official Documentation AFIP

* Digital VAT Book - record design https://www.afip.gob.ar/libro-iva-digital/documentos/libro-iva-digital-diseno-registros.pdf
* CITI - record design (same as the Digital VAT Book): https://www.afip.gob.ar/comprasyventas/documentos/RegimendeInformaciondeComprasyVentasDisenosdeRegistros1.xls
* CITI - specification (provides more information on how to format the numbers and the fillings of the numeric / alphanumeric fields): https://www.afip.gob.ar/comprasyventas/documentos/Regimen-Informacion-Compras-Ventas-Especificaciones.doc

""",
    'depends': [
        'l10n_ar',
 #       'account_reports',
    ],
    'data': [
#        'data/account_financial_report_data.xml',
        'report/account_ar_vat_line_views.xml',
        'security/ir.model.access.csv',
        'security/security.xml',
    ],
    'demo': [],
    'auto_install': True,
    'installable': True,
    'license': 'OEEL-1',
}
