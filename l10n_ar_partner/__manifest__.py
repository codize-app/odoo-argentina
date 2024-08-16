{
    'name': 'Datos Extras para Contacto de Argentina',
    'icon': '/account/static/description/l10n.png',
    'countries': ['ar'],
    'version': '17.0.0.1.0',
    'category': 'Partner',
    'license': 'AGPL-3',
    'summary': "Datos Extras para Contacto de Argentina",
    'description': """
Datos Extras para Contacto de Argentina

* Agrega nombre de Fantasía
* Agrega Localidades y Departamentos
* Agrega Actualizar con Datos de AFIP (Contribuyente)
    """,
    'author': 'Codize, Exemax',
    'website': 'http://www.codize.ar',
    'depends': ['base'],
    'data': [
        'data/depart_data.xml', 
        'data/localidad_data.xml',
        'views/partner_view.xml',
        'security/ir.model.access.csv',
    ],
    'installable': True,
}
