# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
import logging
_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = 'res.partner'

    alicuot_ret_sircar_neuquen_ids = fields.One2many(
        'partner.padron.sircar.neuquen.ret',
        'partner_id',
        'Alicuotas Retencion',
    )
    alicuot_per_sircar_neuquen_ids = fields.One2many(
        'partner.padron.sircar.neuquen.per',
        'partner_id',
        'Alicuotas Percepcion',
    )

class ResPartnerAlicuotRet(models.Model):
    _name = 'partner.padron.sircar.neuquen.ret'
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

    @api.model
    def create(self, vals):
        parent = self.env['res.partner'].search([('id','=',int(vals['partner_id'])),('parent_id','=',False)],limit=1)
        for alicuota in parent.alicuot_ret_sircar_neuquen_ids:
            if alicuota.padron_activo == True:
                alicuota.padron_activo = False
        
        vals['padron_activo'] = True
        rec = super(ResPartnerAlicuotRet, self).create(vals)
        return rec

class ResPartnerAlicuotPer(models.Model):
    _name = 'partner.padron.sircar.neuquen.per'
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

    @api.model
    def create(self, vals):
        parent = self.env['res.partner'].search([('id','=',int(vals['partner_id'])),('parent_id','=',False)],limit=1)
        for alicuota in parent.alicuot_per_sircar_neuquen_ids:
            if alicuota.padron_activo == True:
                alicuota.padron_activo = False
        
        vals['padron_activo'] = True
        rec = super(ResPartnerAlicuotPer, self).create(vals)
        return rec