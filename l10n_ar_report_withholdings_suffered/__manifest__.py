# -*- coding: utf-8 -*-
{
    "name": "Reportes de Ret/Per Sufridas",
    'version': '19.0.0.1.0',
    'category': 'Accounting/Localizations',
    'sequence': 14,
    'author': 'Ivan Arriola, Exemax, Codize',
    'license': 'AGPL-3',
    'summary': '',
    "depends": [
	"base",
        "l10n_ar"
    ],
    'external_dependencies': {},
    "data": [
        'security/ir.model.access.csv',
        'views/account_journal_view.xml',
        'views/account_tax_view.xml',
        'views/report_withholdings_suffered_views.xml',
    ],
    'demo': [],
    'installable': True,
    'auto_install': False,
    'application': False,
}
