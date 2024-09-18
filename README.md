**English** | [Spanish](https://github.com/codize-app/odoo-argentina/blob/15.0/README_es.md)

# Odoo Argentina
Argentine Location for Odoo 17 Community. Original based on Location by Moldeo Interactive [and original based on Location by AdHoc]

## Installation
### Install l10n_ar base

First, install Odoo Community module l10n_ar

Clone this repository with branch 17.0

```
git clone https://github.com/codize-app/odoo-argentina -b 17.0
```

Verify dependencies:

```
sudo apt-get install libpq-dev python-dev libxml2-dev libxslt1-dev libldap2-dev libsasl2-dev libffi-dev libssl-dev
```

Inside directory, install dependencies:

```
sudo pip3 install -r requirements.txt
sudo apt-get install python3-m2crypto
```

### Prepare Server

#### Ubuntu 20.04
Enter the file:

```
sudo nano /etc/ssl/openssl.cnf
```

Add this to the beginning of the file:

```
openssl_conf = default_conf
```

Add this to the end of the file:

```
[ default_conf ]
ssl_conf = ssl_sect
[ssl_sect]
system_default = system_default_sect
[system_default_sect]
MinProtocol = TLSv1.2
CipherString = DEFAULT:@SECLEVEL=1
```

#### Debian 10 / Debian 11
Enter the file:

```
sudo nano /etc/ssl/openssl.cnf
```

Search the following line: `CipherString = DEFAULT@SECLEVEL=2` and replace by `CipherString = DEFAULT@SECLEVEL=1`

### Install Electronic Invoice

Install PyAfipWS:

```
git clone https://github.com/pyar/pyafipws.git
cd pyafipws
sudo pip3 install -r requirements.txt
sudo python setup.py install
```

If errors:

```
sudo python3 setup.py install
```

Go to installation directory of PyAFIPWS:

```
cd /usr/local/lib/python3/dist-packages/pyafipws
```

Note: Replace `python3` by the python version in the system (like `python3.9`)

Create a folder with the name cache:

```
sudo mkdir cache
```

Change permission of folder:

```
sudo chmod -R 777 cache
```

Add path odoo-argentina to addons path in `odoo.conf`. Restart Odoo Server, Update Apps List and install modules `l10n_ar_afipws` and `l10n_ar_afipws_fe`
For reports install `l10n_ar_report_fe`

## l10n_ar extras

* `l10n_ar_ledger`: VAT Ledger for Sales and Purchases
* `l10n_ar_withholding_automatic`: Automatic Withholding on Invoices and Payments. Premium package (`odoo-argentina-withholding`) support on exports for ARBA, AGIP and SIRCAR
* `l10n_ar_bank`: Install Argentina Bank's List
* `l10n_ar_partner`: Improve partners for Argentina PyMEs
* `l10n_ar_sale`: Localized sales, like multi-currency management
* `l10n_ar_purchase`: Localized purchases, like multi-currency management
* `l10n_ar_exchange_rate`: Automatic Exchange Rate and Manual Rate for Purchases Invoices

## Extras

* `account_payment_group`: Payments Group
* `account_bimonetary`: Account Bimonetary Reports

## Questions & Bugs

For questions, or report bugs please use the following resources:

* [OdooAR - Wiki](https://github.com/OdooAR/odoo-argentina-doc/wiki)
* [OdooAR - Forum](https://github.com/OdooAR/odoo-argentina-doc/discussions)

---
Develop by Exemax SAS & Codize

Funtional Contact: contacto@exemax.com.ar

Dev Contact: info@codize.ar
