# Account Debt Management

It adds new ways to see partner debt:

* Two new tabs (customer debt / supplier debt) on partner form showing the detail of all unreconciled lines with amount on currencies, financial amount and cumulative amounts
* New button from partner to display all the history for a partner
* Add partner balance
* You can send email to one or multiple partners with they debt report

By default all lines of same document are grouped and minimun maturity date of the move line is shown, you can change this behaviur by:

* Create / modify parameter "account_debt_management.date_maturity_type" with one of the following values:
   * detail: lines will be splitted by maturity date
   * max: one line per document, max maturity date shown
   * min (default value if no parameter or no matching): one line per document, min maturity date shown.

IMPORTANT: this modules isn't compatible with account_journal_security or account_multi_store module. This mudule allows user to see all debt lines no matter journals restrictions

## Contributors

* AdHoc SA
* Moldeo Interactive
* Exemax
* Codize

## Maintainer

This module is maintained by the Exemax-Codize. Original develop by AdHoc SA
