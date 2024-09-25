[English](https://github.com/codize-app/odoo-argentina/blob/15.0/README.md) | **Spanish**

# Odoo Argentina
Localización Argentina para Odoo 17 Community. Basada en la Localización de Moldeo Interactive [y a su vez basada en la Localización de AdHoc]

## Instalación
### Instalar módulo base l10n_ar

Primero, instalr el módulo de Odoo Community l10n_ar

Clonar este repositorio con la branch 17.0:

```
git clone https://github.com/codize-app/odoo-argentina -b 17.0
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
git clone https://github.com/pyar/pyafipws.git
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

* `l10n_ar_ledger`: Libros de IVA, Libros de IVA Digital y Reportes de IVA para Ventas y Compras
* `l10n_ar_withholding_automatic`: Percepciones/Retenciones Automáticas en Pagos y Facturas. El paquete premium (`odoo-argentina-withholding`) soporta la exportación para ARBA, AGIP y SIRCAR
* `l10n_ar_bank`: Instala la Lista de Bancos Argentinos
* `l10n_ar_partner`: Mejoras para datos de PyMEs Argentinas
* `l10n_ar_sale`: Ventas Localizadas, gestión multimonedas
* `l10n_ar_purchase`: Compras Localizadas, gestión multimonedas
* `l10n_ar_exchange_rate`: Tasa de Cambio Automática, y Tasa Manual para Facturas de Compra

## Extras

* `account_payment_group`: Recibos de Pago
* `account_bimonetary`: Reportes de Contabilidad Bimonetaria

## Preguntas y Bugs

Para preguntas, o reporte de bugs por favor utilizar los siguientes recursos:

* [OdooAR - Wiki](https://github.com/OdooAR/odoo-argentina-doc/wiki)
* [OdooAR - Forum](https://github.com/OdooAR/odoo-argentina-doc/discussions)

---
Desarrollado por Exemax SAS & Codize

Contacto Funcional: contacto@exemax.com.ar

Contacto de Desarrollo: info@codize.ar
