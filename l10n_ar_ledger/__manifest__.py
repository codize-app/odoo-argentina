# -*- coding: utf-8 -*-
{
    "name": "Libros IVA de Argentina",
    'version': '14.0.0.0.0',
    'category': 'Accounting/Localizations',
    'sequence': 14,
    'author': 'ADHOC SA, Moldeo Interactive, Odoo Community Association (OCA), Exemax, Codize',
    'license': 'AGPL-3',
    'summary': '',
    "depends": [
	"base",
        "l10n_ar",
    ],
    'external_dependencies': {
    },
    "data": [
        'account_vat_report_view.xml',
        'security/ir.model.access.csv',
        'report/l10n_ar_ledger_report.xml'
    ],
    'demo': [],
    'installable': True,
    'auto_install': False,
    'application': False,
}
