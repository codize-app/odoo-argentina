# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
import logging
_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = 'res.partner'

    alicuot_ret_arba_ids = fields.One2many(
        'partner.padron.arba.ret',
        'partner_id',
        'Alicuotas Retencion',
    )
    alicuot_per_arba_ids = fields.One2many(
        'partner.padron.arba.per',
        'partner_id',
        'Alicuotas Percepcion',
    )
    imp_per_arba_ids = fields.One2many(
        'res.partner.per.arba',
        'partner_id',
        'Impuestos Per ARBA'
    )

class ResPartnerPerArba(models.Model):
    _name = "res.partner.per.arba"
    _order = "company_id"

    partner_id = fields.Many2one(
        'res.partner',
        required=True,
        ondelete='cascade',
    )
    tax_id = fields.Many2one(
        'account.tax',
        'Impuesto',
        domain=[('type_tax_use', '=', 'sale'),('tax_group_id.l10n_ar_tribute_afip_code','=','07')],
    )
    company_id = fields.Many2one(
        'res.company',
        required=True,
        ondelete='cascade',
        default=lambda self: self.env.user.company_id,
    )

class ResPartnerAlicuotRet(models.Model):
    _name = 'partner.padron.arba.ret'
    _order = 'create_date desc'

    partner_id = fields.Many2one(
        'res.partner',
        required=True,
        ondelete='cascade',
    )
    publication_date = fields.Date('Fecha de publicacion')
    effective_date_from = fields.Date('Vigencia desde')
    effective_date_to = fields.Date('Vigencia hasta')
    type_contr_insc = fields.Selection([
        ('C', 'Convenio Multilatera'),
        ('D', 'Directo Pcia.Bs.As')
    ], 'Tipo')
    alta_baja = fields.Selection([
        ('S', 'Se incorpora al padron'),
        ('N', 'Baja')
    ], 'Alta/Baja')
    cambio = fields.Selection([
        ('S', 'Cambio al anterior'),
        ('N', 'Sin cambios')
    ], 'Cambio')
    a_ret = fields.Float('Alicuota-Retencion')
    nro_grupo_ret = fields.Char('Nro Grupo Retencion')
    padron_activo = fields.Boolean('Activo')

class ResPartnerAlicuotPer(models.Model):
    _name = 'partner.padron.arba.per'
    _order = 'create_date desc'

    partner_id = fields.Many2one(
        'res.partner',
        required=True,
        ondelete='cascade',
    )
    publication_date = fields.Date('Fecha de publicacion')
    effective_date_from = fields.Date('Vigencia desde')
    effective_date_to = fields.Date('Vigencia hasta')
    type_contr_insc = fields.Selection([
        ('C', 'Convenio Multilatera'),
        ('D', 'Directo Pcia.Bs.As')
    ], 'Tipo')
    alta_baja = fields.Selection([
        ('S', 'Se incorpora al padron'),
        ('N', 'Baja')
    ], 'Alta/Baja')
    cambio = fields.Selection([
        ('S', 'Cambio al anterior'),
        ('N', 'Sin cambios')
    ], 'Cambio')
    a_per = fields.Float('Alicuota-Percepcion')
    nro_grupo_per = fields.Char('Nro Grupo Percepcion')
    padron_activo = fields.Boolean('Activo')