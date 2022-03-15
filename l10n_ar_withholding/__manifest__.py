{
    'name': 'Retenciones en Pagos de Argentina',
    'license': 'AGPL-3',
    'author': 'ADHOC SA, Moldeo Interactive, Exemax, Codize',
    'category': 'Accounting & Finance',
    'data': [
        'views/account_tax_view.xml',
        'views/account_payment_view.xml',
        'views/account_payment_group_view.xml',
        'views/res_partner_view.xml',
        'views/res_company_view.xml',
        'views/afip_activity_view.xml',
        'views/afip_tabla_ganancias_escala_view.xml',
        'views/afip_tabla_ganancias_alicuotasymontos_view.xml',
        'views/withholding_view.xml',
        'report/report_payment_withholding.xml',
        'security/ir.model.access.csv',
        'security/security.xml',
        'data/account_payment_method_data.xml',
        'data/tabla_ganancias_data.xml',
    ],
    'depends': [
        'account',
        'l10n_ar',
        'account_payment_group',
    ],
    'installable': True,
    'version': '14.0.1.0.0',
}
