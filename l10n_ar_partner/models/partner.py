# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import requests
import json
try:
    from pysimplesoap.client import SoapFault
except ImportError:
    SoapFault = None
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

    _super_send = requests.Session.send

    @classmethod
    def _request_handler(cls, s, r, **kwargs):
        """Don't block external requests."""
        return cls._super_send(s, r, **kwargs)

    internal_reference = fields.Char('Nombre de Fantasía')
    dept_id = fields.Many2one('res.departamento', string='Partido', ondelete='restrict', domain="[('provincia_id', '=', state_id)]")
    loc_id = fields.Many2one('res.localidad', string='Localidad', ondelete='restrict', domain="[('partido_id', '=', dept_id)]")
    
    iibb_number = fields.Char('Ingresos Burtos')
    #percepciones_ids = fields.One2many(
    #    'res.partner.per',
    #    'partner_id',
    #    'Percepciones de cliente'
    #)
    drei = fields.Selection([
        ('activo', 'Activo'),
        ('no_activo', 'No Activo'),
    ],
        string='DREI',
    )
    default_regimen_ganancias_id = fields.Many2one(
        'afip.tabla_ganancias.alicuotasymontos',
        'Regimen Ganancias por Defecto',
    )
    gross_income_number = fields.Char(
        'Número IIBB',
        size=64,
    )
    gross_income_type = fields.Selection([
        ('multilateral', 'Multilateral'),
        ('local', 'Local'),
        ('no_liquida', 'No Liquida'),
        ('reg_simplificado', 'Reg.Simplificado'),
    ],
        'Tipo IIBB',
    )
    gross_income_jurisdiction_ids = fields.Many2many(
        'res.country.state',
        string='Gross Income Jurisdictions',
        help='The state of the company is cosidered the main jurisdiction',
    )
    start_date = fields.Date(
        'Start-up Date',
    )
    estado_padron = fields.Char(string='Estado AFIP')
    imp_ganancias_padron = fields.Selection([
        ('NI', 'No Inscripto'),
        ('AC', 'Activo'),
        ('EX', 'Exento'),
        # ('NA', 'No alcanzado'),
        # ('XN', 'Exento no alcanzado'),
        # ('AN', 'Activo no alcanzado'),
        ('NC', 'No corresponde'),
    ],
        string='Ganancias',
    )
    imp_iva_padron = fields.Selection([
        ('NI', 'No Inscripto'),
        ('AC', 'Activo'),
        ('EX', 'Exento'),
        ('NA', 'No alcanzado'),
        ('XN', 'Exento no alcanzado'),
        ('AN', 'Activo no alcanzado'),
        # ('NC', 'No corresponde'),
    ],
        string='IVA',
    )
    integrante_soc_padron = fields.Selection(
        [('N', 'No'), ('S', 'Si')],
        'Integrante Sociedad',
    )
    monotributo_padron = fields.Selection(
        [('N', 'No'), ('S', 'Si')],
        'Monotributo',
    )
    actividad_monotributo_padron = fields.Char(string='Actividad Monotributo')
    empleador_padron = fields.Boolean(string="Padrón Empleador")
    actividades_padron = fields.Many2many(
       'afip.activity',
       'res_partner_afip_activity_rel',
       'partner_id', 'afip_activity_id',
       string='Actividades',
    )
    impuestos_padron = fields.Many2many(
       'afip.tax',
       'res_partner_afip_tax_rel',
       'partner_id', 'afip_tax_id',
       string='Impuestos',
    )

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

            if ws_sr_padron['Contribuyente']['ListaActividades']:
                self.write({'actividades_padron': [(5, 0, 0)]})
                for act in ws_sr_padron['Contribuyente']['ListaActividades']:
                    a = self.env['afip.activity'].search([('code', '=', str(act['idActividad']))], limit=1)
                    if a:
                        self.actividades_padron = [(4, a.id)]

            if ws_sr_padron['Contribuyente']['impuestos']:
                self.write({'impuestos_padron': [(5, 0, 0)]})
                for imp in ws_sr_padron['Contribuyente']['impuestos']:
                    i = self.env['afip.tax'].search([('code', '=', str(imp))], limit=1)
                    if i:
                        self.impuestos_padron = [(4, i.id)]

    @api.constrains('gross_income_jurisdiction_ids', 'state_id')
    def check_gross_income_jurisdictions(self):
        for rec in self:
            if rec.state_id and \
                    rec.state_id in rec.gross_income_jurisdiction_ids:
                raise UserError(_(
                    'La Juridicción %s es considerada la juridicción principal '
                    'porque es la provincia de la compañía, debe ser removida '
                    'de la lista de juridicciones.') % rec.state_id.name)

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

class ResDepartament(models.Model):
    _name = "res.departamento"
    _description = "Departamento-Partido"

    name = fields.Char(string="Nombre Partido", required=True)
    provincia_id = fields.Many2one('res.country.state', string='Provincia', required=True)

class ResLocation(models.Model):
    _name = "res.localidad"
    _description = "Localidad"

    name = fields.Char(string='Nombre Localidad', required=True)
    partido_id = fields.Many2one('res.departamento', string="Partido", required=True)

#class ResPartnerPer(models.Model):
#    _name = "res.partner.per"
#    _order = "company_id"
#
#    partner_id = fields.Many2one(
#        'res.partner',
#        required=True,
#        ondelete='cascade',
#    )
#    tax_id = fields.Many2one(
#        'account.tax',
#        'Impuesto',
#        domain=[('type_tax_use', '=', 'sale'),('tax_group_id.l10n_ar_tribute_afip_code','=','09')],
#    )
#    company_id = fields.Many2one(
#        'res.company',
#        required=True,
#        ondelete='cascade',
#        default=lambda self: self.env.user.company_id,
#    )

class AccountConcept(models.Model):
   _name = "afip.concept"

   code = fields.Char(
       'Código',
       required=True
   )
   name = fields.Char(
       'Nombre',
       required=True
   )
   active = fields.Boolean(
       default=True,
   )

class AccountActivity(models.Model):
   _name = "afip.activity"

   code = fields.Char(
       'Código',
       required=True
   )
   name = fields.Char(
       'Nombre',
       required=True
   )
   active = fields.Boolean(
       default=True,
   )


class AccountTax(models.Model):
   _name = "afip.tax"

   code = fields.Char(
       'Código',
       required=True
   )
   name = fields.Char(
       'Nombre',
       required=True
   )
   active = fields.Boolean(
       default=True,
   )

class ArcaTablagananciasEscala(models.Model):
    _name = 'afip.tabla_ganancias.escala'
    _rec_name = 'importe_desde'

    importe_desde = fields.Float(
        'Mas de $',
    )
    importe_hasta = fields.Float(
        'A $',
    )
    importe_fijo = fields.Float(
        '$',
    )
    porcentaje = fields.Float(
        'Más el %'
    )
    importe_excedente = fields.Float(
        'S/ Exced. de $'
    )
    cod_regimen = fields.Char('Código Régimen')


class ArcaTablagananciasAlicuotasymontos(models.Model):
    _name = 'afip.tabla_ganancias.alicuotasymontos'
    _rec_name = 'codigo_de_regimen'

    codigo_de_regimen = fields.Char(
        'Código de régimen',
        size=6,
        required=True,
        help='Código de régimen de inscripción en impuesto a las ganancias.'
    )
    anexo_referencia = fields.Char(
        'Anexo de referencia',
        required=True,
    )
    concepto_referencia = fields.Text(
        'Concepto de referencia',
        required=True,
    )
    porcentaje_inscripto = fields.Float(
        '% Inscripto',
        help='Elija -1 si se debe calcular s/escala'
    )
    porcentaje_no_inscripto = fields.Float(
        '% No Inscripto'
    )
    montos_no_sujetos_a_retencion = fields.Float(
        'Montos no sujetos a retención'
    )
