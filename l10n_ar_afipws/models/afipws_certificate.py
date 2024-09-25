##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
from odoo.exceptions import UserError
from odoo import fields, models, api, _
try:
    from OpenSSL import crypto
except ImportError:
    crypto = None
try:
    from base64 import encodestring
except ImportError:
    from base64 import encodebytes as encodestring
import logging
_logger = logging.getLogger(__name__)


class AfipwsCertificate(models.Model):
    _name = "afipws.certificate"
    _description = "Certificado AFIP"
    _rec_name = "alias_id"

    alias_id = fields.Many2one(
        'afipws.certificate_alias',
        ondelete='cascade',
        string='Alias del Certificado',
        required=True,
        auto_join=True,
        index=True,
    )
    csr = fields.Text(
        'Solicitud de Certificado (CSR)',
        help='Solicitud de Certificado (CSR) en formato PEM.'
    )
    crt = fields.Text(
        'Certificado (CRT)',
        help='Certificado (CRT) en formato PEM.'
    )
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('cancel', 'Cancelled'),
    ],
        'Estado',
        index=True,
        readonly=True,
        default='draft',
        help="* The 'Draft' state is used when a user is creating a new pair "
        "key. Warning: everybody can see the key."
        "\n* The 'Confirmed' state is used when a certificate is valid."
        "\n* The 'Canceled' state is used when the key is not more used. You "
        "cant use this key again."
    )
    request_file = fields.Binary(
        'Descargar Solicitud de Certificado Firmada',
        compute='_compute_request_file',
        readonly=True,
        store=True
    )
    request_filename = fields.Char(
        'Nombre de Archivo',
        readonly=True,
        compute='_compute_request_file',
        store=True
    )
    company_id = fields.Many2one(
        'res.company',
        'Compañía',
        required=True,
        default=lambda self: self.env.user.company_id,
        auto_join=True,
        index=True,
    )

    @api.depends('csr')
    def _compute_request_file(self):
        for rec in self.filtered('csr'):
            rec.request_filename = 'request.csr'
            #rec.request_file = base64.encodestring(self.csr.encode('utf-8'))
            rec.request_file = encodestring(self.csr.encode('utf-8'))

    def action_to_draft(self):
        if self.alias_id.state != 'confirmed':
            raise UserError(_('Certificate Alias must be confirmed first!'))
        self.write({'state': 'draft'})
        return True

    def action_cancel(self):
        self.write({'state': 'cancel'})
        return True

    def action_confirm(self):
        self.verify_crt()
        self.write({'state': 'confirmed'})
        return True

    def verify_crt(self):
        """
        Verify if certificate is well formed
        """
        for rec in self:
            crt = rec.crt
            msg = False

            if not crt:
                msg = _(
                    'Invalid action! Please, set the certification string to '
                    'continue.')
            certificate = rec.get_certificate()
            if certificate is None:
                msg = _(
                    'Invalid action! Your certificate string is invalid. '
                    'Check if you forgot the header CERTIFICATE or forgot/ '
                    'append end of lines.')
            if msg:
                raise UserError(msg)
        return True

    def get_certificate(self):
        """
        Return Certificate object.
        """
        self.ensure_one()
        if self.crt:
            try:
                certificate = crypto.load_certificate(
                    crypto.FILETYPE_PEM, self.crt.encode('ascii'))
            except Exception as e:
                if 'Expecting: CERTIFICATE' in e[0]:
                    raise UserError(_(
                        'Wrong Certificate file format.\nBe sure you have '
                        'BEGIN CERTIFICATE string in your first line.'))
                else:
                    raise UserError(_(
                        'Unknown error.\nX509 return this message:\n %s') % (
                        e[0]))
        else:
            certificate = None
        return certificate
