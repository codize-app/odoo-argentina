{
    'name': 'Datos Extras para Contacto de Argentina',
    'version': '16.0.0.1.0',
    'category': 'Partner',
    'license': 'AGPL-3',
    'summary': "Datos Extras para Contacto de Argentina",
    'description': """
Datos Extras para Contacto de Argentina
======================

* Agrega nombre de Fantasía
    """,
    'author': 'Codize, Exemax',
    'website': 'http://www.codize.ar',
    'depends': ['base'],
    'data': [
        'views/partner_view.xml',
        'security/ir.model.access.csv',
        'data/depart_data.xml', 
        'data/localidad_data.xml',
    ],
    'installable': True,
}
