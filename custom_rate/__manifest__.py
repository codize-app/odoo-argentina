# -*- coding: utf-8 -*-
{
    'name': "Custom rate",

    'summary': """
        take the custom rate for calculate amount other currency """,

    'description': """
        Long description of module's purpose
    """,

    'author': "Exemax, Gabriela Riquelme",
    'website': "http://www.Exemax.com.ar",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['l10n_latam_invoice_document',
        'l10n_latam_base','account'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/views.xml'
    ],
    # only loaded in demonstration mode
    'demo': [
        #'demo/demo.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
