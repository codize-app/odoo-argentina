# -*- coding: utf-8 -*-
{
    "name": "Libros IVA de Argentina",
    'version': '15.0.0.1.0',
    'category': 'Accounting/Localizations',
    'sequence': 14,
    'author': 'ADHOC SA, Moldeo Interactive, Odoo Community Association (OCA), Exemax, Codize',
    'license': 'AGPL-3',
    'summary': '',
    "depends": [
	"base",
        "l10n_ar",
        "report_xlsx"
    ],
    'external_dependencies': {},
    "data": [
        'account_vat_report_view.xml',
        'security/ir.model.access.csv',
        'report/l10n_ar_ledger_report.xml',
        'report/l10n_ar_ledger_report_xlsx.xml'
    ],
    'demo': [],
    'installable': True,
    'auto_install': False,
    'application': False,
}
