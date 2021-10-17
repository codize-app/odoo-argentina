# -*- coding: utf-8 -*-

from odoo import models, fields, api
import logging
_logger = logging.getLogger(__name__)

class ResPartner(models.Model):
    _inherit = 'res.partner'

    internal_reference = fields.Char('Nombre de Fantasía')

    def name_get(self):
        result = []
        for record in self:
            if record.internal_reference:
                result.append((record.id, record.internal_reference + ' - [' + record.name + ']'))
            else:
                result.append((record.id, record.name))
        return result

    def update_from_padron(self):
        company_id = self.env.company
        ws_sr_padron_a5 = company_id.get_connection('ws_sr_padron_a5').connect()
        #connect = ws_sr_padron_a5.Consultar('20000000516') # Testing
        connect = ws_sr_padron_a5.Consultar(self.vat)
        #_logger.info(ws_sr_padron_a5)
        self.name = ws_sr_padron_a5.denominacion
        self.street = ws_sr_padron_a5.direccion
        self.city = ws_sr_padron_a5.localidad
        self.zip = ws_sr_padron_a5.cod_postal
        if ws_sr_padron_a5.tipo_persona == 'FISICA':
            self.company_type = 'person'
        else:
            self.company_type = 'company'

        iva = ws_sr_padron_a5.imp_iva
        l10n_ar_type = ''

        if iva == 'N' or iva == 'NI':
            l10n_ar_type = 'Consumidor Final'
        elif iva == 'AC' or iva == 'S':
            l10n_ar_type = 'IVA Responsable Inscripto'
        elif iva == 'XN' or iva == 'AN' or iva == 'NA':
            l10n_ar_type = 'IVA No Alcanzado'
        elif iva == 'EX':
            l10n_ar_type = 'IVA Sujeto Exento'
        else:
            l10n_ar_type = 'Consumidor Final'

        if l10n_ar_type != '':
            iva_afip = self.env['l10n_ar.afip.responsibility.type'].search([('name', '=', l10n_ar_type)])
            self.l10n_ar_afip_responsibility_type_id = iva_afip.id
