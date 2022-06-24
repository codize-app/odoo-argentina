{
    'name': 'Export TXT RET/PER Arba',
    'license': 'AGPL-3',
    'author': 'ADHOC SA, Moldeo Interactive, Exemax, Codize',
    'category': 'Accounting & Finance',
    'data': [
        'views/account_export_arba_view.xml',
        'views/arba_padron.xml',
        'views/import_padron_arba_view.xml',
        'views/res_partner_view.xml',
        'views/res_config_settings_inherit_view.xml',
        'views/account_tax_inherit_view.xml',
        'security/ir.model.access.csv',
    ],
    'depends': [
        'base',
        'contacts',
        'account',
        'l10n_ar',
        'l10n_ar_withholding',
    ],
    'installable': True,
    'version': '14.0.1.0.0',
}
