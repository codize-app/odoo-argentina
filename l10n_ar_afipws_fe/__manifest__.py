{
    "name": "Factura Electrónica Argentina",
    'version': '12.0.1.3.0',
    'category': 'Localization/Argentina',
    'sequence': 14,
    'author': 'ADHOC SA, Moldeo Interactive,Odoo Community Association (OCA)',
    'license': 'AGPL-3',
    'summary': '',
    'depends': [
        'l10n_ar_afipws',
        'base',
        'uom',
        'l10n_latam_invoice_document',
        'l10n_ar',
        'account_move_tax',
        'account_debit_note',
        'report_xlsx'
        #'l10n_ar_account',
    ],
    'external_dependencies': {
    },
    'data': [
        'wizard/afip_ws_consult_wizard_view.xml',
        #'wizard/afip_ws_currency_rate_wizard_view.xml',
        #'wizard/res_config_settings_view.xml',
        'views/move_view.xml',
        #'views/l10n_latam_document_type_view.xml',
        'views/account_journal_view.xml',
        'views/product_uom_view.xml',
        'views/res_currency_view.xml',
        'security/ir.model.access.csv',
        #views/report_invoice.xml',
        #'views/menuitem.xml',
    ],
    'demo': [
    ],
    'images': [
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
