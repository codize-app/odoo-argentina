# -*- coding: utf-8 -*-
{
    "name": "Argentinian VAT Ledger Management",
    'version': '9.0.1.4.0',
    'category': 'Localization/Argentina',
    'sequence': 14,
    'author': 'ADHOC SA,Moldeo Interactive,Odoo Community Association (OCA)',
    'license': 'AGPL-3',
    'summary': '',
    "depends": [
        # TODO we should try to get this report with another tool, not aeroo
	"base",
        "l10n_ar",
        "report_xlsx"
    ],
    'external_dependencies': {
    },
    "data": [
        'account_vat_report_view.xml',
        'account_report.xml',
        'security/ir.model.access.csv',
    ],
    'demo': [
    ],
    'test': [
    ],
    'images': [
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
