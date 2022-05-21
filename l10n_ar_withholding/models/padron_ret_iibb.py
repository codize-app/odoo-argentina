# -*- coding: utf-8 -*-
from odoo import models, fields
import logging
_logger = logging.getLogger(__name__)

class PadronRetIIBB(models.Model):
    _name = 'arba.padron'


    name = fields.Char('CUIT')
    publication_date = fields.Date('Fecha de publicacion')
    effective_date_from = fields.Date('Fecha de vigencia desde')
    effective_date_to = fields.Date('Fecha de vigencia hasta')
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
    a_ret = fields.Float('Alicuota-Retencion')
    nro_grupo_perc = fields.Char('Nro Grupo Percepcion')
    nro_grupo_ret = fields.Char('Nro Grupo Retencion')


    
