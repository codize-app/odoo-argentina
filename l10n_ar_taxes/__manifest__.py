{
    'name': 'Impuestos Extras Argentina',
    'version': '14.0.0.0.0',
    'category': 'Partner',
    'license': 'AGPL-3',
    'summary': "Impuestos Extras Argentina",
    'description': """
Impuestos Extras Argentina
======================

* Impuestos Internos
    """,
    'author': 'Codize, Exemax',
    'website': 'http://www.codize.ar',
    'depends': ['base', 'product', 'account', 'sale','purchase'],
    'data': ['product_template.xml', 'sale_order.xml','purchase_order.xml', 'account_move.xml'],
    'installable': True,
}
