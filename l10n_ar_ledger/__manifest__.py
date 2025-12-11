# For copyright and license notices, see __manifest__.py file in module root
# directory or check the readme files

{
    "name": "Libros de IVA para Argentina",
    'icon': '/account/static/description/l10n.png',
    'countries': ['ar'],
    "version": "18.0.0.0.2",
    "category": "Accounting",
    "license": "AGPL-3",
    "summary": "Libros de IVA (PDF y XLSX), Libro IVA Digital e IVA Simple (TXT, CSV) para Argentina",
    "author": "Odoo Community Association (OCA), Codize, Exemax, ADHOC SA, Moldeo Interactive",
    "website": "https://github.com/OCA/l10n-argentina",
    "depends": ["base", "l10n_ar", "report_xlsx"],
    "external_dependencies": {},
    "data": [
        "security/ir.model.access.csv",
        "security/security.xml",
        "views/res_company.xml",
        "views/account_vat_ledger.xml",
        "report/account_vat_ledger.xml",
        "report/account_vat_ledger_xlsx.xml",
    ],
    "installable": True,
}
