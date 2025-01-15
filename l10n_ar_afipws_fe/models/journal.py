##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
from odoo import models, api, fields, _
import logging
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

class AccountJournal(models.Model):
    _inherit = 'account.journal'

    sequences = fields.One2many(comodel_name='ir.sequence',inverse_name='journal_id',string='Secuencias')
    _afip_ws_selection = (lambda self, *args, **kwargs: self._get_afip_ws_selection(*args, **kwargs))

    @api.model
    def _get_afip_ws_selection(self):
        return [
            ('wsfe', 'Mercado interno -sin detalle- RG2485 (WSFEv1)'),
            ('wsmtxca', 'Mercado interno -con detalle- RG2904 (WSMTXCA)'),
            ('wsfex', 'Exportación -con detalle- RG2758 (WSFEXv1)'),
            ('wsbfe', 'Bono Fiscal -con detalle- RG2557 (WSBFE)'),
        ]

    afip_ws = fields.Selection(selection=_get_afip_ws_selection, string='ARCA WS')

    def get_name_and_code_suffix(self):
        name = super(AccountJournal, self).get_name_and_code_suffix()
        if self.afip_ws == 'wsfex':
            name += ' Exportación'
        return name

    @api.model
    def create(self, vals):
        journal = super(AccountJournal, self).create(vals)
        if journal.l10n_ar_afip_pos_system == 'RLI_RLM' and journal.afip_ws:
            try:
                journal.sync_document_local_remote_number()
            except Exception:
                _logger.info('No se puede sincronizar números locales y remotos')
        return journal

    @api.constrains('point_of_sale_type', 'afip_ws')
    def check_afip_ws_and_type(self):
        for rec in self:
            if rec.l10n_ar_afip_pos_system != 'RLI_RLM' and rec.afip_ws:
                raise UserError('Solo se puede utilizar un ARCA WS si el tipo es "Electrónico"')

    def get_journal_letter(self, counterpart_partner=False):
        """Function to be inherited by afip ws fe"""
        letters = super(AccountJournal, self).get_journal_letter(counterpart_partner=counterpart_partner)
        # filter only for sales journals

        if self.type != 'sale':
            return letters
        if self.afip_ws == 'wsfe':
            letters = letters.filtered(
                lambda r: r.name != 'E')
        elif self.afip_ws == 'wsfex':
            letters = letters.filtered(
                lambda r: r.name == 'E')
        return letters

    def sync_document_local_remote_number(self):
        if self.type != 'sale':
            return True
        for journal_document_type in self.journal_document_type_ids:
            next_by_ws = int(journal_document_type.get_pyafipws_last_invoice()['result']) + 1
            journal_document_type.sequence_id.number_next_actual = next_by_ws

    def check_document_local_remote_number(self):
        msg = ''
        if self.type != 'sale':
            return True
        #for journal_document_type in self.journal_document_type_ids:
        for sequence in self.l10n_ar_sequence_ids:
            journal_document_type = sequence.l10n_latam_document_type_id
            result = journal_document_type.get_pyafipws_last_invoice(None,journal_document_type,self,sequence)
            next_by_ws = int(result['result']) + 1
            next_by_seq = sequence.number_next_actual
            if next_by_ws != next_by_seq:
                msg += _(
                    '* El Tipo de Documento %s, Local %i, Remoto %i\n' % (
                        journal_document_type.name,
                        next_by_seq,
                        next_by_ws))
        if msg:
            msg = 'Hay algunos documentos desincronizados:\n' + msg
            raise UserError(msg)
        else:
            raise UserError('Todos los documentos están sincronizados')

    def test_pyafipws_dummy(self):
        """
        ARCA Description: Método Dummy para verificación de funcionamiento de
        infraestructura (FEDummy)
        """
        self.ensure_one()
        if self.l10n_ar_afip_pos_system != 'FEERCEL':
            afip_ws = self.afip_ws
        else:
            afip_ws = 'wsfex'
        if not afip_ws:
            raise UserError(_('No se seleccionó ARCA WS'))
        ws = self.company_id.get_connection(afip_ws).connect()
        ws.Dummy()
        title = _("Servicio ARCA %s\n") % afip_ws
        msg = (
            "AppServerStatus: %s DbServerStatus: %s AuthServerStatus: %s" % (
                ws.AppServerStatus,
                ws.DbServerStatus,
                ws.AuthServerStatus))
        raise UserError(title + msg)

    def test_pyafipws_taxes(self):
        self.ensure_one()
        afip_ws = self.afip_ws
        if not afip_ws:
            raise UserError(_('No se seleccionó ARCA WS'))
        ws = self.company_id.get_connection(afip_ws).connect()
        ret = ws.ParamGetTiposTributos(sep="")
        msg = (_(" %s %s") % (
            '. '.join(ret), " - ".join([ws.Excepcion, ws.ErrMsg, ws.Obs])))
        title = _('Tributos en ARCA\n')
        raise UserError(title + msg.replace('NULL.', '\n'))


    def test_pyafipws_point_of_sales(self):
        self.ensure_one()
        afip_ws = self.afip_ws
        if not afip_ws:
            raise UserError(_('No se seleccionó ARCA WS'))
        ws = self.company_id.get_connection(afip_ws).connect()
        if afip_ws == 'wsfex':
            ret = ws.GetParamPtosVenta()
        elif afip_ws == 'wsfe':
            ret = ws.ParamGetPtosVenta(sep=" ")
        else:
            raise UserError(_(
                'Obtener el punto de venta desde WS %s no está implementado') % (
                afip_ws))
        msg = (_(" %s %s") % (
            '. '.join(ret), " - ".join([ws.Excepcion, ws.ErrMsg, ws.Obs])))
        title = _('Puntos de Venta Habilitados en ARCA\n')
        raise UserError(title + msg)

    def get_pyafipws_cuit_document_classes(self):
        self.ensure_one()
        afip_ws = self.afip_ws
        if not afip_ws:
            raise UserError(_('No se seleccionó ARCA WS'))
        ws = self.company_id.get_connection(afip_ws).connect()
        if afip_ws == 'wsfex':
            ret = ws.GetParamTipoCbte(sep=",")
        elif afip_ws == 'wsfe':
            ret = ws.ParamGetTiposCbte(sep=",")
        elif afip_ws == 'wsbfe':
            ret = ws.GetParamTipoCbte()
        else:
            raise UserError(_(
                'Get document types for ws %s is not implemented yet') % (
                afip_ws))
        msg = (_(
            "Documentos Autorizados en ARCA\n%s\n. \nObservaciones: %s") % (
            '\n '.join(ret), ".\n".join([ws.Excepcion, ws.ErrMsg, ws.Obs])))
        raise UserError(msg)

    def get_pyafipws_zonas(self):
        self.ensure_one()
        afip_ws = self.afip_ws
        if not afip_ws:
            raise UserError(_('No AFIP WS selected'))
        ws = self.company_id.get_connection(afip_ws).connect()
        if afip_ws == 'wsbfe':
            ret = ws.GetParamZonas()
        else:
            raise UserError(_(
                'Zonas para el WS %s no se ha implementado') % (
                afip_ws))
        msg = (_(
            "Zonas on AFIP\n%s\n. \nObservations: %s") % (
            '\n '.join(ret), ".\n".join([ws.Excepcion, ws.ErrMsg, ws.Obs])))
        raise UserError(msg)

    def get_pyafipws_NCM(self):
        self.ensure_one()
        afip_ws = self.afip_ws
        if not afip_ws:
            raise UserError(_('No AFIP WS selected'))
        ws = self.company_id.get_connection(afip_ws).connect()
        if afip_ws == 'wsbfe':
            ret = ws.GetParamNCM()
        else:
            raise UserError(_(
                'NCM para WS %s no se ha implementado') % (
                afip_ws))
        msg = (_(
            "Zonas en ARCA\n%s\n. \nObservaciones: %s") % (
            '\n '.join(ret), ".\n".join([ws.Excepcion, ws.ErrMsg, ws.Obs])))
        raise UserError(msg)

    def get_pyafipws_currencies(self):
        self.ensure_one()
        return self.env['res.currency'].get_pyafipws_currencies(
            afip_ws=self.afip_ws, company=self.company_id)

    def action_get_connection(self):
        self.ensure_one()
        afip_ws = self.afip_ws
        if not afip_ws:
            raise UserError(_('No se ha seleccionado ARCA WS'))
        self.company_id.get_connection(afip_ws).connect()

    def get_pyafipws_currency_rate(self, currency):
        raise UserError(currency.get_pyafipws_currency_rate(
            afip_ws=self.afip_ws,
            company=self.company_id,
        )[1])
