# -*- coding: utf-8 -*-
{
    "name": "Reportes de Impuestos Argentinos",
    'version': '14.0',
    'author': "Exemax, Codize, Autodidacta-TI",
    'category': 'Accounting/Localizations',
    'depends': [
        'l10n_ar'
    ],
    'installable': True,
    'license': 'AGPL-3',
    'data': [
		'security/ir.model.access.csv',
        'wizard/financial_reports.xml',
        'views/menu_reports.xml',
        'report/action_report.xml',
        'report/report_iva_sale.xml',
        'report/report_iva_purchase.xml'
    ],
    'demo': []
}
