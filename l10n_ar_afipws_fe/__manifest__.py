{
    "name": "Factura Electrónica Argentina",
    'version': '17.0.1.3.0',
    'icon': '/account/static/description/l10n.png',
    'countries': ['ar'],
    'category': 'Accounting/Localizations',
    'author': 'ADHOC SA, Moldeo Interactive, Exemax, Codize, Odoo Community Association (OCA)',
    'license': 'AGPL-3',
    'summary': '',
    'depends': [
        'base',
        'uom',
        'l10n_latam_invoice_document',
        'l10n_ar',
        'l10n_ar_afipws',
        'l10n_ar_bank',
        'account',
        'account_debit_note',
    ],
    'external_dependencies': {
    },
    'data': [
        'wizard/afip_ws_consult_wizard_view.xml',
        'views/move_view.xml',
        'views/account_journal_view.xml',
        'views/product_uom_view.xml',
        'views/res_currency_view.xml',
        'views/ir_sequence.xml',
        'security/ir.model.access.csv',
    ],
    'demo': [
    ],
    'images': [
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
