{
    'name': 'Datos Extras para Contacto de Argentina',
    'icon': '/account/static/description/l10n.png',
    'countries': ['ar'],
    'version': '19.0.0.1.0',
    'category': 'Accounting',
    'license': 'AGPL-3',
    'summary': "Datos Extras para Contacto de Argentina",
    'description': """
Datos Extras para Contacto de Argentina

* Agrega nombre de Fantasía
* Agrega Localidades y Departamentos
* Agrega Actualizar con Datos desde ARCA (Contribuyente)
    """,
    'author': 'Codize, Exemax',
    'website': 'http://www.codize.ar',
    'depends': ['base', 'account', 'l10n_ar'],
    'data': [
        'data/depart_data.xml',
        'data/localidad_data.xml',
        'views/partner_view.xml',
        'security/ir.model.access.csv',
        'views/afip_activity_view.xml',
        'views/afip_tax_view.xml',
    ],
    'installable': True,
}
