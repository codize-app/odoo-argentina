{
    'name': 'Export TXT RET/PER Agip',
    'license': 'AGPL-3',
    'author': 'ADHOC SA, Moldeo Interactive, Exemax, Codize',
    'category': 'Accounting & Finance',
    'data': [
        'views/account_export_agip_view.xml',
        'security/ir.model.access.csv',
    ],
    'depends': [
        'base',
        'account',
        'l10n_ar',
        'l10n_ar_withholding',
    ],
    'installable': True,
    'version': '14.0.1.0.0',
}
