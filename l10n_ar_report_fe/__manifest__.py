# -*- coding: utf-8 -*-
{
    "name": "Reporte de la Factura Electrónica Argentina",
    'version': '15.0.0.0.1.0',
    'author': "Moldeo Interactive, Exemax, Codize, ADHOC SA, Odoo Community Association (OCA)",
    'category': 'Accounting',
    'depends': [
        'l10n_ar_afipws_fe'
    ],
    'installable': True,
    'license': 'AGPL-3',
    'data': [
        'views/report_invoice_fe.xml',
        'views/afip_view.xml'
    ],
    'demo': []
}
