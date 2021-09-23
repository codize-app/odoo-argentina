# Odoo Argentina
Argentine Location for Odoo 14 Community. Original based on Location by Moldeo Interactive [and original based on Location by AdHoc]

## Installation
### Install l10n_ar base

Clone this repository with branch 14.0

```
git clone https://github.com/codize-app/odoo-argentina -b 14.0
```

Inside directory, install dependencies:

```
sudo pip3 install -r requirements.txt
sudo apt-get install python-m2crypto
```

Remember install OCA Dependencies (inside `oca_dependencies.txt` file)

### Install Electronic Invoice

Install PyAfipWS:

```
git clone https://github.com/pyar/pyafipws.git -b py3k
cd pyafipws
sudo pip3 install -r requirements.txt
sudo python setup.py install
```

If errors:

```
sudo python3 setup.py install
```

Add path odoo-argentina to addons path in `odoo.conf`. Restart Odoo Server, Update Apps List and install modules `l10n_ar_afipws` and `l10n_ar_afipws_fe`. For reports install `l10n_ar_report_fe`.

## l10n_ar extras

* `l10n_ar_ledger`: VAT Ledger for Sales and Purchases
* `l10n_ar_exchange_rate`: Get Exchange Rate from AFIP
* `l10n_ar_bank`: Install Argentina Bank's List
* `l10n_ar_partner`: Add features to contacts (like fantasy name)
* `l10n_ar_taxes`: Add other taxes (like Internal Taxes)

## Extras

* `account_debt_managment`: Get Debt of Customer / Supplier
* `account_check`: Manager for Checks (rejected, deferred, holding)

## Questions & Bugs

For questions, or report bugs please use the following resources:

* [OdooAR - Wiki](https://github.com/OdooAR/odoo-argentina-doc/wiki)
* [OdooAR - Forum](https://github.com/OdooAR/odoo-argentina-doc/discussions)

---
Develop by Exemax SAS & Codize

Funtional Contact: info@examax.com.ar

Dev Contact: info@codize.ar
