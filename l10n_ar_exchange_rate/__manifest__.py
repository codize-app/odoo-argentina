# -*- coding: utf-8 -*-
{
    'name': "Tasa de Cambio Manual para Argentina",
    'icon': '/account/static/description/l10n.png',
    'countries': ['ar'],
    'summary': """
        Tasa de Cambio Manual para Argentina""",
    'description': """
        Tasa de Cambio Manual para Argentina
    """,

    'author': "Exemax, Codize",
    'website': "http://www.exemax.com.ar",

    'category': 'Account',
    'version': '17.0.0.0.1',

    'depends': ['base', 'l10n_ar', 'l10n_latam_invoice_document', 'l10n_latam_base'],

    'data': [
        'views/account_move.xml',
    ]
}
