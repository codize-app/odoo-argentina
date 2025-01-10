##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class ProductUom(models.Model):
    _inherit = "uom.uom"

    afip_code = fields.Char('Código ARCA')

    def action_get_pyafipws_product_uoms(self):
        self.get_pyafipws_product_uoms()

    def get_pyafipws_product_uoms(self, afip_ws='wsfex', company=False):
        self.ensure_one()
        if not company:
            company = self.env['res.company'].search([('localization', '=', 'argentina')], limit=1)
        if not company:
            raise UserError('No hay compañía utilizando localización Argentina')
        ws = company.get_connection(afip_ws).connect()

        if afip_ws == "wsfex":
            res = ws.GetParamUMed(sep=' ')
        else:
            raise UserError('ARCA WS %s no ha sido implementado') % (afip_ws)
        title = 'Unidad de Medida:\n%s' % '\n'.join(res)
        msg = " - ".join([
            ws.Excepcion,
            ws.ErrMsg,
            ws.Obs])
        _logger.info('%s\n%s' % (title, msg))
        raise UserError(title + msg)
