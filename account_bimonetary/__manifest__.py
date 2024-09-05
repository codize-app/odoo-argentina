# -*- coding: utf-8 -*-
{
    'name': "Account Bimonetary",

    'summary': """
        Account Bimonetary Reports for Odoo""",

    'description': """
        Account Bimonetary for Odoo
    """,

    "icon": '/account/static/description/icon.png',

    'author': "Exemax, Codize",
    'website': "https://www.exemax.com.ar",

    'category': 'Account',
    'version': '17.0.0.0.1',

    'depends': ['base', 'account'],

    'data': [
        'views/account_move_line.xml',
    ]
}
