# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import datetime
import base64
import csv
from datetime import date as dt
import logging
_logger = logging.getLogger(__name__)



class ImportPadronArba(models.Model):
    _name = 'import.padron.arba'
    _description = 'import.padron.arba'

    def btn_process(self):
        _procesados = ""
        _procesados_stock = ""
        _noprocesados = ""
        vals={}    
        self.ensure_one()
        if not self.padron_match:
            raise ValidationError('Debe seleccionar metodo de busqueda de Clientes')
        if not self.delimiter:
            raise ValidationError('Debe ingresar el delimitador')
        if not self.padron_file:
            raise ValidationError('Debe seleccionar el archivo')
        if self.state != 'draft':
            raise ValidationError('Archivo procesado!')
        self.file_content = base64.decodebytes(self.padron_file)
        lines = self.file_content.split('\n')

        #Guardamos todos los cuit de clientes para luego consultar si el cliente existe y evitar hacer un search por cada linea de TXT
        partners = self.env['res.partner'].search([('vat','!=',False),('parent_id','=',False)])
        cuit_partners = []
        for c in partners:
            cuit_partners.append(c.vat)

        for i,line in enumerate(lines):
            if self.skip_first_line and i == 0:
                continue
            lista = line.split(self.delimiter)
            if len(lista) > 10:
                #Consultamos si existe el cliente segun el cuit sino seguimos a la siguiente linea para minimizar el proceso
                cuit = lista[4]
                if cuit not in cuit_partners:
                    continue
                tipo = lista[0]
                publication_date = lista[1]
                effective_date_from = lista[2]
                effective_date_to = lista[3]
                type_contr_insc = lista[5]
                alta_baja = lista[6]
                cambio = lista[7]
                a_per = False
                a_ret = False
                nro_grupo_perc = False
                nro_grupo_ret = False
                if tipo == 'P':
                    a_per = lista[8]
                    nro_grupo_perc = lista[9]
                else:
                    a_ret = lista[8]
                    nro_grupo_ret = lista[9]

                vals.clear()

                # Carga vals
                if tipo == 'P' or tipo == 'R': 
                    vals['publication_date'] = datetime.strptime((publication_date[:2] + '/' + publication_date[2:4] + '/' + publication_date[4:]), '%d/%m/%Y')
                    vals['effective_date_from'] = datetime.strptime((effective_date_from[:2] + '/' + effective_date_from[2:4] + '/' + effective_date_from[4:]), '%d/%m/%Y')
                    vals['effective_date_to'] = datetime.strptime((effective_date_to[:2] + '/' + effective_date_to[2:4] + '/' + effective_date_to[4:]), '%d/%m/%Y')
                    vals['name'] = cuit
                    vals['type_contr_insc'] = type_contr_insc
                    vals['alta_baja'] = alta_baja
                    if a_per:
                        vals['type_alicuot'] = 'P'
                        vals['a_per'] = float(a_per.replace(',','.'))
                        vals['a_ret'] = 0.0
                    else:
                        vals['type_alicuot'] = 'R'
                        vals['a_per'] = 0.0
                        vals['a_ret'] = float(a_ret.replace(',','.'))
                    if nro_grupo_perc:
                        vals['nro_grupo_perc'] = nro_grupo_perc
                    if nro_grupo_ret:
                        vals['nro_grupo_ret'] = nro_grupo_ret

                    padron_existe = self.env['arba.padron'].search([('name','=',cuit)])
                    if len(padron_existe) > 0:
                        a = lambda a : vals['a_per'] if tipo =='P' else 0.0
                        padron_existe.sudo().update({
                            'a_per' : vals['a_per'],
                            'a_ret' : vals['a_ret']
                        })
                    else:
                        self.env['arba.padron'].sudo().create(vals)
                    _procesados += "{} \n".format(cuit)
                
                else:
                    _noprocesados += "{} \n".format(cuit)

            elif len(lista) == 1:
                continue
            else:
                raise ValidationError("El CSV no se procesara por estar mal formado en la linea {0}, contenido de linea: {1}. Se necesitan al menos 11 columnas".format(i, line))
        self.clientes_cargados = _procesados
        self.not_processed_content = _noprocesados
        self.state = 'processed'

    
    @api.depends('padron_file')
    def compute_lineas_archivo(self):
        for rec in self:
            if rec.padron_file != False:
                rec.file_content_tmp = base64.decodebytes(rec.padron_file)
                lines = rec.file_content_tmp.split('\n')
                for i,line in enumerate(lines):
                    rec.lineas_archivo += 1


            else:
                rec.lineas_archivo = 0
        pass

    name = fields.Char('Nombre')
    padron_file = fields.Binary('Archivo')
    delimiter = fields.Char('Delimitador',default=";")
    state = fields.Selection(selection=[('draft','Borrador'),('processed','Procesado')],string='Estado',default='draft')
    file_content = fields.Text('Texto archivo')
    file_content_tmp = fields.Text('Texto archivo')
    not_processed_content = fields.Text('Texto no procesado')
    clientes_cargados = fields.Text('Clientes cargados')
    skip_first_line = fields.Boolean('Saltear primera linea',default=True)
    padron_match = fields.Selection(selection=[('cuit','CUIT')],string='Buscar clientes por...',default='cuit')
    lineas_archivo = fields.Integer(compute=compute_lineas_archivo, store=True)