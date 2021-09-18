# Account Payment Groups

This module extends the functionality of payments to suport paying with multiple payment methods at once.

By default payments are managed on one step, if you want, you can use two steps to confirm payments on supplier payments. This option is available per company.

A new security group "See Payments Menu" is created and native odoo payments menus are assigned to that group.

We also add a pay now functionality on invoices so that payment can be automatically created if you choose a journal on the invoice. You need to enable this on accounting configuration.

Account Payment groups are created from:

* sale order payments
* reconciliation wizard (statements)
* website payments
* after expense validation when posting journal items.

## Contributors

* AdHoc SA
* Moldeo Interactive
* Exemax
* Codize

## Maintainer

This module is maintained by the Exemax-Codize. Original develop by AdHoc SA
