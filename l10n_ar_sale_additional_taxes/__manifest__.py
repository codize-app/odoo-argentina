# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
{
    'name': 'Impuestos Adicionales para Ventas - Argentina',
    'version': '11.0.1.0.0',
    'category': 'Accounting',
    'summary': "Impuestos Adicionales para Ventas - Argentina",
    'depends': ['base','account','l10n_ar','account_move_tax','account_check'],
    "data": [
	"account_view.xml",
        "security/ir.model.access.csv"
    ],
    'license': 'AGPL-3',
    'installable': True,
    'application': False,
}

