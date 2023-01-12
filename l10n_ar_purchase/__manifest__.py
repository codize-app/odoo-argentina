# -*- coding: utf-8 -*-
{
    'name': "Compras Localizadas para Argentina",

    'summary': """
        Compras Localizadas para Argentina""",

    'description': """
    Compras Localizadas para Argentina. Actualiza importes de facturas en ARS cuando el pedido está en USD 
    """,

    'author': 'Codize, Exemax',
    'website': 'http://www.codize.ar',

    'category': 'Purchase',
    'version': '15.0.0.1.0',
    'license': 'AGPL-3',

    'depends': ['base', 'purchase', 'custom_rate'],

    'data': ['wizard/purchase_make_invoice_advance_views.xml',
             'views/purchase_views.xml',
             'security/ir.model.access.csv',
     ],
    'demo': [],
}
