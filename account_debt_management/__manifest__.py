{
    'name': 'Account Debt Management',
    'version': '14.0.1.2.0',
    'category': 'Account',
    'author': 'ADHOC SA, Exemax, Codize',
    'license': 'AGPL-3',
    'depends': [
        'l10n_ar',
        'account_payment_fix'
    ],
    'data': [
        'security/ir.model.access.csv',
        'security/account_debt_management_security.xml',
        'report/account_debt_line_view.xml',
        'views/account_move_line_view.xml',
        'views/res_partner_view.xml',
    ],
    'demo': [],
    'installable': True,
}
