**English** | [Spanish](https://github.com/codize-app/odoo-argentina/blob/14.0/README_es.md)

# Odoo Argentina
Argentine Location for Odoo 14 Community. Original based on Location by Moldeo Interactive [and original based on Location by AdHoc]

## Installation
### Install l10n_ar base

First, install Odoo Community module l10n_ar

Clone this repository with branch 14.0

```
git clone https://github.com/codize-app/odoo-argentina -b 14.0
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
git clone https://github.com/pyar/pyafipws.git -b py3k
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

Add path odoo-argentina to addons path in `odoo.conf`. Restart Odoo Server, Update Apps List and install modules `l10n_ar_afipws` and `l10n_ar_afipws_fe`. For reports install `l10n_ar_report_fe`.

## l10n_ar extras

* `l10n_ar_ledger`: VAT Ledger for Sales and Purchases
* `l10n_ar_report_picking`: Support for Electronic Picking
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

Funtional Contact: contacto@exemax.com.ar

Dev Contact: info@codize.ar
