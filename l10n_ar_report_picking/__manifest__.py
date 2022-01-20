# -*- coding: utf-8 -*-
{
    "name": "Reporte del Remito Electrónico Argentino",
    'version': '14.0',
    'author': "Exemax, Codize",
    'category': 'Accounting/Localizations',
    'depends': [
        'stock',
        'l10n_ar',
	'l10n_ar_afipws_fe'
    ],
    'installable': True,
    'license': 'AGPL-3',
    'data': [
        'security/ir.model.access.csv',
        'report_stock_picking.xml',
        'afip_view.xml'
    ],
    'demo': []
}
