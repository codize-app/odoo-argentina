# -*- coding: utf-8 -*-
{
    'name': "Ventas Localizadas para Argentina",

    'summary': """
        Ventas Localizadas para Argentina""",

    'description': """
    Ventas Localizadas para Argentina. Actualiza importes de facturas en ARS cuando el pedido está en USD 
    """,

    'author': 'Codize, Exemax',
    'website': 'http://www.codize.ar',

    'category': 'Sales',
    'version': '15.0.0.1.0',
    'license': 'AGPL-3',

    'depends': ['base', 'sale', 'sale_management'],

    'data': ['wizard/sale_make_invoice_advance_views.xml'],
    'demo': [],
}
