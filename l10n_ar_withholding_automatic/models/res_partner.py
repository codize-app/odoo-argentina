# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from odoo.exceptions import UserError
try:
    from pysimplesoap.client import SoapFault
except ImportError:
    SoapFault = None
import logging
_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = "res.partner"

    #arba_alicuot_ids = fields.One2many(
    #    'res.partner.tax',
    #    'partner_id',
    #    'Alícuotas PERC-RET',
    #)
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
    afip_responsability_type_id = fields.Many2one(
        'l10n_ar.afip.responsability.type',
        'AFIP Responsability Type',
        auto_join=True,
        index=True,
    )

    # From
    # http://www.sistemasagiles.com.ar/trac/wiki/PadronContribuyentesAFIP
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
    #actividades_padron = fields.Many2many(
    #    'afip.activity',
    #    'res_partner_afip_activity_rel',
    #    'partner_id', 'afip_activity_id',
    #    string='Actividades',
    #)
    #impuestos_padron = fields.Many2many(
    #    'afip.tax',
    #    'res_partner_afip_tax_rel',
    #    'partner_id', 'afip_tax_id',
    #    string='Impuestos',
    #)
    #last_update_padron = fields.Date(
    #    'Última Actualización del Padrón',
    #)

    #def get_arba_alicuota_percepcion(self):
    #    company = self._context.get('invoice_company')
    #    date_invoice = self._context.get('date_invoice')
    #    if date_invoice and company:
    #        date = fields.Date.from_string(date_invoice)
    #        arba = self.get_arba_data(company, date)
    #        return arba.alicuota_percepcion / 100.0
    #    return 0
#
    #def get_arba_alicuota_retencion(self, company, date):
    #    arba = self.get_arba_data(company, date)
    #    return arba.alicuota_retencion / 100.0
#
    #def get_arba_data(self, company, date):
    #    self.ensure_one()
    #    from_date = (date + relativedelta(day=1)).strftime('%Y%m%d')
    #    to_date = (date + relativedelta(
    #        day=1, days=-1, months=+1)).strftime('%Y%m%d')
    #    commercial_partner = self.commercial_partner_id
    #    arba = self.arba_alicuot_ids.search([
    #        ('from_date', '=', from_date),
    #        ('to_date', '=', to_date),
    #        ('company_id', '=', company.id),
    #        ('partner_id', '=', commercial_partner.id)], limit=1)
    #    if not arba:
    #        arba_data = company.get_arba_data(
    #            commercial_partner,
    #            from_date, to_date,
    #        )
    #        arba_data['partner_id'] = commercial_partner.id
    #        arba_data['company_id'] = company.id
    #        arba = self.arba_alicuot_ids.sudo().create(arba_data)
    #    return arba
#
    #def update_constancia_from_padron_afip(self):
    #    self.ensure_one()
    #    return True
#
    def get_data_from_padron_afip(self):
        self.ensure_one()
        cuit = self.cuit_required()

        company = self.env.user.company_id
        env_type = company._get_environment_type()
        try:
            certificate = company.get_key_and_certificate(
                company._get_environment_type())
        except Exception:
            certificate = self.env['afipws.certificate'].search([
                ('alias_id.type', '=', env_type),
                ('state', '=', 'confirmed'),
            ], limit=1)
            if not certificate:
                raise UserError(_(
                    'Not confirmed certificate found on database'))
            company = certificate.alias_id.company_id

        padron = company.get_connection('ws_sr_padron_a5').connect()
        error_msg = _(
            'No pudimos actualizar desde padron afip al partner %s (%s).\n'
            'Recomendamos verificar manualmente en la página de AFIP.\n'
            'Obtuvimos este error: %s')
        try:
            padron.Consultar(cuit)
        except SoapFault as e:
            raise UserError(error_msg % (self.name, cuit, e.faultstring))
        except Exception as e:
            raise UserError(error_msg % (self.name, cuit, e))

        if not padron.denominacion or padron.denominacion == ', ':
            raise UserError(error_msg % (
                self.name, cuit, 'AFIP no devolvió nombre'))

        imp_iva = padron.imp_iva
        if imp_iva == 'S':
            imp_iva = 'AC'
        elif imp_iva == 'N':
            imp_iva = 'NI'

        vals = {
            'name': padron.denominacion,
            # 'name': padron.tipo_persona,
            # 'name': padron.tipo_doc,
            # 'name': padron.dni,
            'estado_padron': padron.estado,
            'street': padron.direccion,
            'city': padron.localidad,
            'zip': padron.cod_postal,
            'actividades_padron': self.actividades_padron.search(
                [('code', 'in', padron.actividades)]).ids,
            'impuestos_padron': self.impuestos_padron.search(
                [('code', 'in', padron.impuestos)]).ids,
            'imp_iva_padron': imp_iva,
            # TODAVIA no esta funcionando
            # 'imp_ganancias_padron': padron.imp_ganancias,
            'monotributo_padron': padron.monotributo,
            'actividad_monotributo_padron': padron.actividad_monotributo,
            'empleador_padron': padron.empleador == 'S' and True,
            'integrante_soc_padron': padron.integrante_soc,
            #'last_update_padron': fields.Date.today(),
        }
        ganancias_inscripto = [10, 11]
        ganancias_exento = [12]
        if set(ganancias_inscripto) & set(padron.impuestos):
            vals['imp_ganancias_padron'] = 'AC'
        elif set(ganancias_exento) & set(padron.impuestos):
            vals['imp_ganancias_padron'] = 'EX'
        elif padron.monotributo == 'S':
            vals['imp_ganancias_padron'] = 'NC'
        else:
            _logger.info(
                "We couldn't get impuesto a las ganancias from padron, you"
                "must set it manually")

        if padron.provincia:
            # depending on the database, caba can have one of this codes
            caba_codes = ['C', 'CABA', 'ABA']
            # if not localidad then it should be CABA.
            if not padron.localidad:
                state = self.env['res.country.state'].search([
                    ('code', 'in', caba_codes),
                    ('country_id.code', '=', 'AR')], limit=1)
            # If localidad cant be caba
            else:
                state = self.env['res.country.state'].search([
                    ('name', 'ilike', padron.provincia),
                    ('code', 'not in', caba_codes),
                    ('country_id.code', '=', 'AR')], limit=1)
            if state:
                vals['state_id'] = state.id

        if imp_iva == 'NI' and padron.monotributo == 'S':
            vals['afip_responsability_type_id'] = self.env.ref(
                'l10n_ar.res_RM').id
        elif imp_iva == 'AC':
            vals['afip_responsability_type_id'] = self.env.ref(
                'l10n_ar.res_IVARI').id
        elif imp_iva == 'EX':
            vals['afip_responsability_type_id'] = self.env.ref(
                'l10n_ar.res_IVAE').id
        else:
            _logger.info(
                "We couldn't infer the AFIP responsability from padron, you"
                "must set it manually.")

        return vals

    @api.constrains('gross_income_jurisdiction_ids', 'state_id')
    def check_gross_income_jurisdictions(self):
        for rec in self:
            if rec.state_id and \
                    rec.state_id in rec.gross_income_jurisdiction_ids:
                raise UserError(_(
                    'Jurisdiction %s is considered the main jurisdiction '
                    'because it is the state of the company, please remove it'
                    'from the jurisdiction list') % rec.state_id.name)


#class ResPartnerArbaAlicuot(models.Model):
    #_name = "res.partner.tax"
    #_order = "to_date desc, from_date desc, tag_id, company_id"
#
    #partner_id = fields.Many2one(
    #    'res.partner',
    #    required=True,
    #    ondelete='cascade',
    #)
    #tax_id = fields.Many2one(
    #    'account.tax',
    #    'Impuesto',
    #    domain=[('type_tax_use', '=', 'supplier')],
    #)
    #percent = fields.Float('Porcentaje',digits=(6,4))
    #tag_id = fields.Many2one(
    #    'account.account.tag',
    #    domain=[('applicability', '=', 'taxes')],
    #    change_default=True,
    #)
    #company_id = fields.Many2one(
    #    'res.company',
    #    required=True,
    #    ondelete='cascade',
    #    default=lambda self: self.env.user.company_id,
    #)
    #from_date = fields.Date(
    #)
    #to_date = fields.Date(
    #)
    #numero_comprobante = fields.Char(
    #)
    #codigo_hash = fields.Char(
    #)
    #alicuota_percepcion = fields.Float(
    #)
    #alicuota_retencion = fields.Float(
    #)
    #grupo_percepcion = fields.Char(
    #)
    #grupo_retencion = fields.Char(
    #)
    #withholding_amount_type = fields.Selection([
    #    ('untaxed_amount', 'Untaxed Amount'),
    #    ('total_amount', 'Total Amount'),
    #],
    #    'Base para retenciones',
    #    help='Base amount used to get withholding amount',
    #)
    #regimen_percepcion = fields.Char(
    #    size=3,
    #    help="Utilizado para la generación del TXT para SIRCAR.\n"
    #    "Tipo de Régimen de Percepción (código correspondiente según "
    #    "tabla definida por la jurisdicción)"
    #)
    #regimen_retencion = fields.Char(
    #    size=3,
    #    help="Utilizado para la generación del TXT para SIRCAR.\n"
    #    "Tipo de Régimen de Retención (código correspondiente según "
    #    "tabla definida por la jurisdicción)"
    #)
    #api_codigo_articulo_retencion = fields.Selection([
    #    ('001', '001: Art.1 - inciso A - (Res. Gral. 15/97 y Modif.)'),
    #    ('002', '002: Art.1 - inciso B - (Res. Gral. 15/97 y Modif.)'),
    #    ('003', '003: Art.1 - inciso C - (Res. Gral. 15/97 y Modif.)'),
    #    ('004', '004: Art.1 - inciso D pto.1 - (Res. Gral. 15/97 y Modif.)'),
    #    ('005', '005: Art.1 - inciso D pto.2 - (Res. Gral. 15/97 y Modif.)'),
    #    ('006', '006: Art.1 - inciso D pto.3 - (Res. Gral. 15/97 y Modif.)'),
    #    ('007', '007: Art.1 - inciso E - (Res. Gral. 15/97 y Modif.)'),
    #    ('008', '008: Art.1 - inciso F - (Res. Gral. 15/97 y Modif.)'),
    #    ('009', '009: Art.1 - inciso H - (Res. Gral. 15/97 y Modif.)'),
    #    ('010', '010: Art.1 - inciso I - (Res. Gral. 15/97 y Modif.)'),
    #    ('011', '011: Art.1 - inciso J - (Res. Gral. 15/97 y Modif.)'),
    #    ('012', '012: Art.1 - inciso K - (Res. Gral. 15/97 y Modif.)'),
    #    ('013', '013: Art.1 - inciso L - (Res. Gral. 15/97 y Modif.)'),
    #    ('014', '014: Art.1 - inciso LL pto.1 - (Res. Gral. 15/97 y Modif.)'),
    #    ('015', '015: Art.1 - inciso LL pto.2 - (Res. Gral. 15/97 y Modif.)'),
    #    ('016', '016: Art.1 - inciso LL pto.3 - (Res. Gral. 15/97 y Modif.)'),
    #    ('017', '017: Art.1 - inciso LL pto.4 - (Res. Gral. 15/97 y Modif.)'),
    #    ('018', '018: Art.1 - inciso LL pto.5 - (Res. Gral. 15/97 y Modif.)'),
    #    ('019', '019: Art.1 - inciso M - (Res. Gral. 15/97 y Modif.)'),
    #    ('020', '020: Art.2 - (Res. Gral. 15/97 y Modif.)'),
    #],
    #    string='Código de Artículo/Inciso por el que retiene',
    #)
    #api_codigo_articulo_percepcion = fields.Selection([
    #    ('021', '021: Art.10 - inciso A - (Res. Gral. 15/97 y Modif.)'),
    #    ('022', '022: Art.10 - inciso B - (Res. Gral. 15/97 y Modif.)'),
    #    ('023', '023: Art.10 - inciso D - (Res. Gral. 15/97 y Modif.)'),
    #    ('024', '024: Art.10 - inciso E - (Res. Gral. 15/97 y Modif.)'),
    #    ('025', '025: Art.10 - inciso F - (Res. Gral. 15/97 y Modif.)'),
    #    ('026', '026: Art.10 - inciso G - (Res. Gral. 15/97 y Modif.)'),
    #    ('027', '027: Art.10 - inciso H - (Res. Gral. 15/97 y Modif.)'),
    #    ('028', '028: Art.10 - inciso I - (Res. Gral. 15/97 y Modif.)'),
    #    ('029', '029: Art.10 - inciso J - (Res. Gral. 15/97 y Modif.)'),
    #    ('030', '030: Art.11 - (Res. Gral. 15/97 y Modif.)'),
    #],
    #    string='Código de artículo Inciso por el que percibe',
    #)
    #api_articulo_inciso_calculo_selection = [
    #    ('001', '001: Art. 5º 1er. párrafo (Res. Gral. 15/97 y Modif.)'),
    #    ('002', '002: Art. 5º inciso 1)(Res. Gral. 15/97 y Modif.)'),
    #    ('003', '003: Art. 5° inciso 2)(Res. Gral. 15/97 y Modif.)'),
    #    ('004', '004: Art. 5º inciso 4)(Res. Gral. 15/97 y Modif.)'),
    #    ('005', '005: Art. 5° inciso 5)(Res. Gral. 15/97 y Modif.)'),
    #    ('006', '006: Art. 6º inciso a)(Res. Gral. 15/97 y Modif.)'),
    #    ('007', '007: Art. 6º inciso b)(Res. Gral. 15/97 y Modif.)'),
    #    ('008', '008: Art. 6º inciso c)(Res. Gral. 15/97 y Modif.)'),
    #    ('009', '009: Art. 12º)(Res. Gral. 15/97 y Modif.)'),
    #    ('010', '010: Art. 6º inciso d)(Res. Gral. 15/97 y Modif.)'),
    #    ('011', '011: Art. 5° inciso 6)(Res. Gral. 15/97 y Modif.)'),
    #    ('012', '012: Art. 5° inciso 3)(Res. Gral. 15/97 y Modif.)'),
    #    ('013', '013: Art. 5° inciso 7)(Res. Gral. 15/97 y Modif.)'),
    #    ('014', '014: Art. 5° inciso 8)(Res. Gral. 15/97 y Modif.)'),
    #]
    #api_articulo_inciso_calculo_percepcion = fields.Selection(
    #    api_articulo_inciso_calculo_selection,
    #    string='Artículo/Inciso para el cálculo percepción',
    #)
    #api_articulo_inciso_calculo_retencion = fields.Selection(
    #    api_articulo_inciso_calculo_selection,
    #    string='Artículo/Inciso para el cálculo retención',
    #)

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

