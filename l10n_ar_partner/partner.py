# -*- coding: utf-8 -*-

from odoo import models, fields, api
import logging
_logger = logging.getLogger(__name__)

class ResPartner(models.Model):
    _inherit = 'res.partner'

    internal_reference = fields.Char('Nombre de Fantasía')

    def write(self, values):
        res = super(ResPartner, self).write(values)

        if self.l10n_latam_identification_type_id.name == 'CUIT' or self.l10n_latam_identification_type_id.name == 'CUIL' or self.l10n_latam_identification_type_id.name == 'DNI':
            for rec in self:
                if rec.vat:
                    if '-' in rec.vat:
                        vat = rec.vat.replace('-', '')
                        rec.vat = vat
                    if '.' in rec.vat:
                        vat = rec.vat.replace('.', '')
                        rec.vat = vat

        return res

    def name_get(self):
        result = []
        for record in self:
            if record.internal_reference:
                if record.parent_id:
                    result.append((record.id, str(record.parent_id.name) + ', ' + str(record.internal_reference) + ' - [' + str(record.name) + ']'))
                else:
                    result.append((record.id, str(record.internal_reference) + ' - [' + str(record.name) + ']'))
            else:
                if record.parent_id:
                    result.append((record.id, str(record.parent_id.name) + ', ' + str(record.name)))
                else:
                    result.append((record.id, str(record.name)))
        return result

    def update_from_padron(self):
        company_id = self.env.company
        if self.l10n_latam_identification_type_id.name == 'CUIT':
            ws_sr_padron_a5 = company_id.get_connection('ws_sr_padron_a5').connect()
            #connect = ws_sr_padron_a5.Consultar('20000000516') # Testing
            connect = ws_sr_padron_a5.Consultar(self.vat)
            #_logger.info(ws_sr_padron_a5)
            self.name = ws_sr_padron_a5.denominacion
            self.street = ws_sr_padron_a5.direccion.capitalize()
            self.city = ws_sr_padron_a5.localidad.capitalize()
            self.zip = ws_sr_padron_a5.cod_postal
            if ws_sr_padron_a5.tipo_persona == 'FISICA':
                self.company_type = 'person'
            else:
                self.company_type = 'company'

            iva = ws_sr_padron_a5.imp_iva
            l10n_ar_type = ''

            if iva == 'N' or iva == 'NI':
                l10n_ar_type = 'Responsable Monotributo'
            elif iva == 'AC' or iva == 'S':
                l10n_ar_type = 'IVA Responsable Inscripto'
            elif iva == 'XN' or iva == 'AN' or iva == 'NA':
                l10n_ar_type = 'IVA No Alcanzado'
            elif iva == 'EX':
                l10n_ar_type = 'IVA Sujeto Exento'
            else:
                l10n_ar_type = 'Consumidor Final'

            if l10n_ar_type != '':
                iva_afip = self.env['l10n_ar.afip.responsibility.type'].search([('name', '=', l10n_ar_type)], limit=1)
                self.l10n_ar_afip_responsibility_type_id = iva_afip.id

            if ws_sr_padron_a5.provincia:
                country_id = self.env['res.country'].search([('name', '=', 'Argentina')], limit=1)
                if country_id:
                    self.country_id = country_id.id

                provincia = ''

                if ws_sr_padron_a5.provincia == 'NEUQUEN':
                    provincia = 'Neuquén'
                elif ws_sr_padron_a5.provincia == 'CORDOBA':
                    provincia = 'Córdoba'
                else:
                    provincia = ws_sr_padron_a5.provincia

                state_id = self.env['res.country.state'].search([('name', 'like', provincia), ('country_id', '=', country_id.id)], limit=1)
                if state_id:
                    self.state_id = state_id.id
        else:
            iva_afip = self.env['l10n_ar.afip.responsibility.type'].search([('name', '=', 'Consumidor Final')], limit=1)
            self.l10n_ar_afip_responsibility_type_id = iva_afip.id

