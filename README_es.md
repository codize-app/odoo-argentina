[English](https://github.com/codize-app/odoo-argentina/blob/15.0/README.md) | **Spanish**

# Odoo Argentina
Localización Argentina para Odoo 15 Community. Basada en la Localización de Moldeo Interactive [y a su vez basada en la Localización de AdHoc]

## Instalación
### Instalar módulo base l10n_ar

Primero, instalr el módulo de Odoo Community l10n_ar

Clonar este repositorio con la branch 15.0:

```
git clone https://github.com/codize-app/odoo-argentina -b 15.0
```

Dentro del directorio, instalar las dependencias:

```
sudo pip3 install -r requirements.txt
sudo apt-get install python3-m2crypto
```

### Preparar el Servidor

#### Ubuntu 20.04
Ingresar al archivo:

```
sudo nano /etc/ssl/openssl.cnf
```

Agregar esta línea al principio del archivo:

```
openssl_conf = default_conf
```

Agregar este bloque al final del archivo:

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
Ingresr al archivo:

```
sudo nano /etc/ssl/openssl.cnf
```

Buscar la siguiente línea: `CipherString = DEFAULT@SECLEVEL=2` y reemplazarla por `CipherString = DEFAULT@SECLEVEL=1`

### Instalar Factura Electrónica

Instalar PyAfipWS:

```
git clone https://github.com/pyar/pyafipws.git -b py3k
cd pyafipws
sudo pip3 install -r requirements.txt
sudo python setup.py install
```

Si se presentan errores:

```
sudo python3 setup.py install
```

Ir al directorio de instalación de PyAFIPWS:

```
cd /usr/local/lib/python3/dist-packages/pyafipws
```

Nota: Reemplazar `python3` por la versión de python instalada en el sistema (como `python3.9`)

Crear una carpeta con el nombre cache:

```
sudo mkdir cache
```

Cambiar permisos de carpeta:

```
sudo chmod -R 777 cache
```

Agregar la ruta odoo-argentina a la ruta de addons en `odoo.conf`. Reiniciar el Servidor de odoo, Actualizar la Lista de Aplicaciones e instalar los módulos `l10n_ar_afipws` y `l10n_ar_afipws_fe`
Para acceso a los reportes en PDF instalar `l10n_ar_report_fe`

## l10n_ar extras

* `l10n_ar_ledger`: Libro IVA para Ventas y Compras
* `l10n_ar_withholding`: Percepciones/Retenciones en Pagos y Facturas. El paquete premium (`odoo-argentina-withholding`) soporta la exportación para ARBA, AGIP, SIRCAR Neuquén y SIRCAR Río Negro
* `l10n_ar_report_picking`: Soporte para Remito PreImpreso (Autoimpresor)
* `l10n_ar_bank`: Instala la Lista de Bancos Argentinos
* `l10n_ar_debit_automatic`: Agrega la opción de carga y reporte de débito automático en los pagos
* `l10n_ar_partner`: Agrega nuevas características a los contactos (como el nombre de fantasía, actualización desde Padrón)
* `l10n_ar_sale`: Agrega nuevas características a ventas (como permitir pedidos de venta en USD pero facturarlos en ARS)
* `l10n_ar_purchase`: Agrega nuevas características a compras (como permitir pedidos de compra en USD pero facturarlos en ARS)
* `l10n_ar_taxes`: Agrega otro tipo de facilidades en la carga de impuestos (como Impuestos Internos)

## Extras

* `account_debt_managment`: Obtiene Deuda de Cliente / Proveedor
* `account_check`: Gestion para Cheques (rechazados, diferidos, de terceros)

## Preguntas y Bugs

Para preguntas, o reporte de bugs por favor utilizar los siguientes recursos:

* [OdooAR - Wiki](https://github.com/OdooAR/odoo-argentina-doc/wiki)
* [OdooAR - Forum](https://github.com/OdooAR/odoo-argentina-doc/discussions)

---
Desarrollado por Exemax SAS & Codize

Contacto Funcional: contacto@exemax.com.ar

Contacto de Desarrollo: info@codize.ar
