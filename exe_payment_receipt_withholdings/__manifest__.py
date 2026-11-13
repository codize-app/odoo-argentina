{
    'name': 'EXE - Recibo de proveedores con certificados de retención',
    'version': '19.0.1.0.1',
    'category': 'Accounting/Accounting',
    'summary': 'Adjunta los certificados de retención al PDF de la orden de pago',
    'author': 'EXE',
    'license': 'AGPL-3',
    'depends': ['account_payment_group', 'l10n_ar_withholding_automatic'],
    'data': ['report/report_withholdings.xml'],
    'installable': True,
    'auto_install': True,
    'application': False,
}
