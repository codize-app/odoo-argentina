# -*- coding: utf-8 -*-
{
    'name': "Debit Automatic Payment",

    'summary': """
        Allows load Debit Automatic TXT file and register like payments""",

    'description': """
        Allows load Debit Automatic TXT file and register like payments
    """,

    'author': "Codize, Exemax",
    'website': "http://www.codize.ar",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Account',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'account', 'mail'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/partner_method.xml',
    ],
    # only loaded in demonstration mode
    'demo': [],
}
