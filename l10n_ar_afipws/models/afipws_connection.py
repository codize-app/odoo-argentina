from odoo import fields, models, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)

class AfipwsConnection(models.Model):
    _name = "afipws.connection"
    _description = "ARCA Conexión WS"
    _rec_name = "afip_ws"
    _order = "expirationtime desc"

    company_id = fields.Many2one(
        'res.company',
        'Compañía',
        required=True,
        index=True,
        auto_join=True,
    )
    uniqueid = fields.Char(
        'Unique ID',
        readonly=True,
    )
    token = fields.Text(
        'Token',
        readonly=True,
    )
    sign = fields.Text(
        'Sign',
        readonly=True,
    )
    generationtime = fields.Datetime(
        'Generation Time',
        readonly=True
    )
    expirationtime = fields.Datetime(
        'Expiration Time',
        readonly=True
    )
    afip_login_url = fields.Char(
        'ARCA Login URL',
        compute='_compute_afip_urls',
    )
    afip_ws_url = fields.Char(
        'ARCA WS URL',
        compute='_compute_afip_urls',
    )
    type = fields.Selection(
        [('production', 'Producción'), ('homologation', 'Homologación')],
        'Type',
        required=True,
    )
    afip_ws = fields.Selection([
        ('ws_sr_padron_a4', 'Servicio de Consulta de Padrón Alcance 4'),
        ('ws_sr_padron_a5', 'Servicio de Consulta de Padrón Alcance 5'),
        ('ws_sr_padron_a10', 'Servicio de Consulta de Padrón Alcance 10'),
        ('ws_sr_padron_a100', 'Servicio de Consulta de Padrón Alcance 100'),
        ('ws_sr_constancia_inscripcion', 'Constancia de Inscripción')
    ],
        'ARCA WS',
        required=True,
    )

    @api.depends('type', 'afip_ws')
    def _compute_afip_urls(self):
        for rec in self:
            rec.afip_login_url = rec.get_afip_login_url(rec.type)

            afip_ws_url = rec.get_afip_ws_url(rec.afip_ws, rec.type)
            if rec.afip_ws and not afip_ws_url:
                raise UserError('Webservice %s no soportado' % rec.afip_ws)
            rec.afip_ws_url = afip_ws_url

    @api.model
    def get_afip_login_url(self, environment_type):
        if environment_type == 'production':
            afip_login_url = ('https://wsaa.afip.gov.ar/ws/services/LoginCms')
        else:
            afip_login_url = ('https://wsaahomo.afip.gov.ar/ws/services/LoginCms')
        return afip_login_url

    @api.model
    def get_afip_ws_url(self, afip_ws, environment_type):
        """
        Function to be inherited on each module that add a new webservice
        """
        _logger.info('URL para ARCA WS %s en %s' % (afip_ws, environment_type))
        afip_ws_url = False
        if afip_ws == 'ws_sr_padron_a4':
            if environment_type == 'production':
                afip_ws_url = (
                    "https://aws.afip.gov.ar/sr-padron/webservices/"
                    "personaServiceA4?wsdl")
            else:
                afip_ws_url = (
                    "https://awshomo.afip.gov.ar/sr-padron/webservices/"
                    "personaServiceA4?wsdl")
        elif afip_ws == 'ws_sr_padron_a5' or afip_ws == 'ws_sr_constancia_inscripcion':
            if environment_type == 'production':
                afip_ws_url = (
                    "https://aws.afip.gov.ar/sr-padron/webservices/"
                    "personaServiceA5?wsdl")
            else:
                afip_ws_url = (
                    "https://awshomo.afip.gov.ar/sr-padron/webservices/"
                    "personaServiceA5?wsdl")
        return afip_ws_url
    
    @api.model
    def _get_ws(self, afip_ws):
        """
        Method to be inherited
        """
        _logger.info('WS %s de la librería' % afip_ws)
        ws = False
        if afip_ws == 'ws_sr_padron_a4':
            from pyafipws.ws_sr_padron import WSSrPadronA4
            ws = WSSrPadronA4()
        elif afip_ws == 'ws_sr_padron_a5' or afip_ws == 'ws_sr_constancia_inscripcion':
            from pyafipws.ws_sr_padron import WSSrPadronA5
            ws = WSSrPadronA5()
        return ws

    def check_afip_ws(self, afip_ws):
        self.ensure_one()
        if self.afip_ws != afip_ws:
            raise UserError('Este método es para conexiones %s y se están llamando para una conexión %s' % (afip_ws, self.afip_ws))

    def connect(self):
        """
        Method to be called
        """
        self.ensure_one()
        _logger.info(
            'Getting connection to ws %s from libraries on '
            'connection id %s' % (self.afip_ws, self.id))
        ws = self._get_ws(self.afip_ws)

        if not ws:
            raise UserError('ARCA Webservice %s no implementado' % (self.afip_ws))
        # TODO implementar cache y proxy
        # create the proxy and get the configuration system parameters:
        # cfg = self.pool.get('ir.config_parameter').sudo()
        # cache = cfg.get_param(cr, uid, 'pyafipws.cache', context=context)
        # proxy = cfg.get_param(cr, uid, 'pyafipws.proxy', context=context)

        wsdl = self.afip_ws_url

        ws.Conectar("", wsdl or "", "")
        cuit = self.company_id.vat
        ws.Cuit = cuit
        ws.Token = self.token
        ws.Sign = self.sign
        ws.Obs = ''
        ws.Errores = []

        _logger.info('Conexión con URL "%s", CUIT "%s"' % (wsdl, ws.Cuit))
        return ws
