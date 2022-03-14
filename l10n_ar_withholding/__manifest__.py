{
    'name': 'Retenciones en Pagos de Argentina',
    'license': 'AGPL-3',
    'author': 'ADHOC SA, Moldeo Interactive, Exemax, Codize',
    'category': 'Accounting & Finance',
    'data': [
        'views/account_tax_view.xml',
        'views/account_payment_view.xml',
        'views/account_payment_group_view.xml',
        'data/account_payment_method_data.xml',
        'security/ir.model.access.csv',
    ],
    'depends': [
        'account',
        'l10n_ar',
        'account_payment_group',
    ],
    'installable': True,
    'version': '14.0.1.0.0',
}
