# -*- coding: utf-8 -*-

from odoo import models, fields, api
import requests
import json
import logging
_logger = logging.getLogger(__name__)

STATES = {
    0: "Ciudad Autónoma de Buenos Aires",
    1: "Buenos Aires",
    2: "Catamarca",
    3: "Córdoba",
    4: "Corrientes",
    5: "Entre Ríos",
    6: "Jujuy",
    7: "Mendoza",
    8: "La Rioja",
    9: "Salta",
    10: "San Juan",
    11: "San Luis",
    12: "Santa Fe",
    13: "Santiago del Estero",
    14: "Tucumán",
    16: "Chaco",
    17: "Chubut",
    18: "Formosa",
    19: "Misiones",
    20: "Neuquén",
    21: "La Pampa",
    22: "Río Negro",
    23: "Santa Cruz",
    24: "Tierra del Fuego"
}

class ResPartner(models.Model):
    _inherit = 'res.partner'

    internal_reference = fields.Char('Nombre de Fantasía')
    prov_id = fields.Many2one('res.country.state', string='Provincia (n)',domain="[('country_id.code', '=', 'AR')]")
    dept_id = fields.Many2one('res.departamento', string='Partido (n)', domain="[('provincia_id', '=', prov_id)]")
    loc_id = fields.Many2one('res.localidad', string='Localidad (n)', domain="[('partido_id', '=', dept_id)]")

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
        if self.l10n_latam_identification_type_id.name == 'CUIT':
            x = requests.get('https://www.tangofactura.com/Rest/GetContribuyente?cuit=' + self.vat)

            ws_sr_padron = json.loads(x.text)

            if ws_sr_padron['Contribuyente']['tipoPersona'] == "FISICA":
                self.company_type = "person"
            else:
                self.company_type = "company"

            self.name = ws_sr_padron['Contribuyente']['nombre']

            EsRI = ws_sr_padron['Contribuyente']['EsRI']
            EsMonotributo = ws_sr_padron['Contribuyente']['EsMonotributo']
            EsExento = ws_sr_padron['Contribuyente']['EsExento']
            l10n_ar_type = ""

            if EsRI == True:
                l10n_ar_type = "IVA Responsable Inscripto"
            elif EsMonotributo == True:
                l10n_ar_type = "Responsable Monotributo"
            elif EsExento == True:
                l10n_ar_type = "IVA Sujeto Exento"

            if l10n_ar_type != "":
                iva_afip = self.env["l10n_ar.afip.responsibility.type"].search([("name", "=", l10n_ar_type)], limit=1)
                self.l10n_ar_afip_responsibility_type_id = iva_afip.id

            if ws_sr_padron['Contribuyente']['domicilioFiscal']['direccion']:
                self.street = ws_sr_padron['Contribuyente']['domicilioFiscal']['direccion'].capitalize()
            if ws_sr_padron['Contribuyente']['domicilioFiscal']['localidad']:
                self.city = ws_sr_padron['Contribuyente']['domicilioFiscal']['localidad'].capitalize()
            if ws_sr_padron['Contribuyente']['domicilioFiscal']['codPostal']:
                self.zip = ws_sr_padron['Contribuyente']['domicilioFiscal']['codPostal']

            if ws_sr_padron['Contribuyente']['domicilioFiscal']['idProvincia']:
                country_id = self.env['res.country'].search([('name', '=', 'Argentina')], limit=1)
                if country_id:
                    self.country_id = country_id.id

                provincia = STATES.get(ws_sr_padron['Contribuyente']['domicilioFiscal']['idProvincia'])

                state_id = self.env['res.country.state'].search([('name', 'ilike', provincia), ('country_id', '=', country_id.id)], limit=1)
                if state_id:
                    self.state_id = state_id.id

class ResDepartament(models.Model):
    _name = "res.departamento"
    
    name = fields.Char(string="Nombre Departamento", required=True)
    provincia_id = fields.Many2one('res.country.state', string='Provincia', required=True)

class ResLocation(models.Model):
    _name = "res.localidad"
    
    name = fields.Char(string='Nombre Localidad', required=True)
    partido_id = fields.Many2one('res.departamento', string="Departamento", required=True)
