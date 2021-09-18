# Modulo Base para los Web Services de AFIP

## Homologation / Production:

First it search for a paramter "afip.ws.env.type" if exists and:

* is production --> production
* is homologation --> homologation

Else

Search for 'server_mode' parameter on conf file. If that parameter:

* has a value then we use "homologation",
* if no parameter, then "production"

## Incluye:

* Wizard for install keys for Web Services.
* API for Ato make request on the Web Services from Odoo.

The l10n_ar_afipws module allows OpenERP to access AFIP services at through Web Services. This module is a service for administrators and programmers, where they could configure the server, authentication and they will also have access to a generic API in Python to use the AFIP services.

Keep in mind that these keys are personal and may cause conflict publish them in the public repositories. 

## Contributors

* AdHoc SA
* Moldeo Interactive
* Exemax
* Codize

## Maintainer

This module is maintained by the Exemax-Codize. Original develop by AdHoc SA
