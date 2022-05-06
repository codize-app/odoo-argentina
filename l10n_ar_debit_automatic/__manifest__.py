# -*- coding: utf-8 -*-
{
    'name': "Debit Automatic Payment",

    'summary': """
        Allows use Debit Automatic TXT file""",

    'description': """
        Allows load Debit Automatic TXT file and register like payments, and export TXT files from invoices
    """,

    'author': "Codize, Exemax",
    'website': "http://www.codize.ar",

    'category': 'Account',
    'version': '0.1',

    'depends': ['base', 'account', 'mail'],

    'data': [
        'security/ir.model.access.csv',
        'views/account_debit_automatic.xml',
        'views/partner_method.xml',
        'report/automatic_debit.xml'
    ],
    'demo': [],
}
