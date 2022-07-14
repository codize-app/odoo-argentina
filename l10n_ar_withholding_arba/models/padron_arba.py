# -*- coding: utf-8 -*-
from odoo import models, fields, api
import logging
_logger = logging.getLogger(__name__)

class Padron(models.Model):
    _name = 'arba.padron'


    name = fields.Char('CUIT')
    publication_date = fields.Date('Fecha de publicacion')
    effective_date_from = fields.Date('Fecha de vigencia desde')
    effective_date_to = fields.Date('Fecha de vigencia hasta')
    type_alicuot = fields.Selection([
        ('P', 'Percepcion'),
        ('R', 'Retencion')
    ], 'Tipo', required = True)
    type_contr_insc = fields.Selection([
        ('C', 'Convenio Multilatera'),
        ('D', 'Directo Pcia.Bs.As')
    ], 'Tipo')
    alta_baja = fields.Selection([
        ('S', 'Se incorpora al padron'),
        ('N', 'No incorpora al padron'),
        ('B', 'Baja')
    ], 'Alta/Baja')
    cambio = fields.Selection([
        ('S', 'Cambio al anterior'),
        ('N', 'Sin cambios')
    ], 'Cambio')
    a_per = fields.Float('Alicuota-Percepcion')
    a_ret = fields.Float('Alicuota-Retencion')
    nro_grupo_perc = fields.Char('Nro Grupo Percepcion')
    nro_grupo_ret = fields.Char('Nro Grupo Retencion')

    @api.model
    def create(self, vals):
        padron = super(Padron, self).create(vals)
        partner = self.env['res.partner'].search([('vat','=',padron.name),('parent_id','=',False)],limit=1)
        if len(partner)>0:

            if padron.type_alicuot == 'R':
                for alicuota in partner.alicuot_ret_arba_ids:
                    if alicuota.padron_activo == True:
                        alicuota.padron_activo = False
                partner.sudo().update({'alicuot_ret_arba_ids' : [(0, 0, {
                    'partner_id': partner.id, 
                    'publication_date': padron.publication_date,
                    'effective_date_from': padron.effective_date_from,
                    'effective_date_to': padron.effective_date_to,
                    'type_contr_insc': padron.type_contr_insc,
                    'alta_baja': padron.alta_baja,
                    'cambio': padron.cambio,
                    'a_ret': padron.a_ret,
                    'nro_grupo_ret': padron.nro_grupo_ret,
                    'padron_activo': True
                })]})
            elif padron.type_alicuot == 'P':
                for alicuota in partner.alicuot_per_arba_ids:
                    if alicuota.padron_activo == True:
                        alicuota.padron_activo = False
                partner.sudo().update({'alicuot_per_arba_ids' : [(0, 0, {
                    'partner_id': partner.id, 
                    'publication_date': padron.publication_date,
                    'effective_date_from': padron.effective_date_from,
                    'effective_date_to': padron.effective_date_to,
                    'type_contr_insc': padron.type_contr_insc,
                    'alta_baja': padron.alta_baja,
                    'cambio': padron.cambio,
                    'a_per': padron.a_per,
                    'nro_grupo_per': padron.nro_grupo_perc,
                    'padron_activo': True
                })]})
        return padron
    
    def write(self, variables):
        if 'publication_date' in variables or 'effective_date_from' in variables or 'effective_date_to' in variables or 'alta_baja' in variables or 'a_per' in variables or 'a_ret' in variables:
            res = super(Padron, self).write(variables)
            partner = self.env['res.partner'].search([('vat','=',self.name),('parent_id','=',False)],limit=1)
            if len(partner)>0:

                if self.type_alicuot == 'R':
                    for alicuota in partner.alicuot_ret_arba_ids:
                        if alicuota.padron_activo == True:
                            alicuota.padron_activo = False
                    partner.alicuot_ret_arba_ids = [(0, 0, {
                        'partner_id': partner.id, 
                        'publication_date': self.publication_date,
                        'effective_date_from': self.effective_date_from,
                        'effective_date_to': self.effective_date_to,
                        'type_contr_insc': self.type_contr_insc,
                        'alta_baja': self.alta_baja,
                        'cambio': self.cambio,
                        'a_ret': self.a_ret,
                        'nro_grupo_ret': self.nro_grupo_ret,
                        'padron_activo': True
                    })]
                elif self.type_alicuot == 'P':
                    for alicuota in partner.alicuot_per_arba_ids:
                        if alicuota.padron_activo == True:
                            alicuota.padron_activo = False
                    partner.alicuot_per_arba_ids = [(0, 0, {
                        'partner_id': partner.id, 
                        'publication_date': self.publication_date,
                        'effective_date_from': self.effective_date_from,
                        'effective_date_to': self.effective_date_to,
                        'type_contr_insc': self.type_contr_insc,
                        'alta_baja': self.alta_baja,
                        'cambio': self.cambio,
                        'a_per': self.a_per,
                        'nro_grupo_per': self.nro_grupo_perc,
                        'padron_activo': True
                    })]
            return res
        
        return super(Padron, self).write(variables)


    
