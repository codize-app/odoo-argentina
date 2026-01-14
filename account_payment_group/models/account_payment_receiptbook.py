from odoo import models, fields, api

class AccountPaymentReceiptbook(models.Model):
    _name = 'account.payment.receiptbook'
    _description = 'Account payment Receiptbook'
    _order = 'sequence asc'

    sequence = fields.Integer(
        'Secuencia',
        help="Utilizado para ordenar los talonarios",
        default=10,
    )
    name = fields.Char(
        'Nombre',
        size=64,
        required=True,
        index=True,
    )
    partner_type = fields.Selection(
        [('customer', 'Cliente'), ('supplier', 'Proveedor')],
        required=True,
        index=True,
    )
    next_number = fields.Integer(
        related='sequence_id.number_next_actual',
        readonly=False,
    )

    # payment_type = fields.Selection(
    #     [('inbound', 'Inbound'), ('outbound', 'Outbound')],
    #     # [('receipt', 'Receipt'), ('payment', 'Payment')],
    #     string='Type',
    #     required=True,
    # )
    # lo dejamos solo como ayuda para generar o no la secuencia pero lo que
    # termina definiendo si es manual o por secuencia es si tiene secuencia
    sequence_type = fields.Selection(
        [('automatic', 'Automático'), ('manual', 'Manual')],
        string='Tipo de Secuencia',
        readonly=False,
        default='automatic',
    )
    sequence_id = fields.Many2one(
        'ir.sequence',
        'Entry Sequence',
        help="Este campo contiene información relacionada al número de los apuntes en el recibo del talonario",
        copy=False,
    )
    company_id = fields.Many2one(
        'res.company',
        'Compañía',
        required=True,
        default=lambda self: self.env[
            'res.company']._company_default_get('account.payment.receiptbook')
    )
    prefix = fields.Char(
        'Prefijo'
    )
    padding = fields.Integer(
        'Número de Padding',
        help="Agregar '0' a la izquierda del número para obtener el numéro de secuencia necesario"
    )
    active = fields.Boolean(
        'Activo',
        default=True,
    )
    mail_template_id = fields.Many2one(
        'mail.template',
        'Plantilla del Mail',
        domain=[('model', '=', 'account.payment.group')],
        help="If set an email will be sent to the customer when the related"
        " account.payment.group has been posted.",
    )

    def write(self, vals):
        """
        If user change prefix we change prefix of sequence.
        TODO: we can use related field but we need to implement manual
        receipbooks with sequences. We should also make padding
        related to sequence
        """
        prefix = vals.get('prefix')
        for rec in self:
            if prefix and rec.sequence_id:
                rec.sequence_id.prefix = prefix
        return super(AccountPaymentReceiptbook, self).write(vals)

    @api.model
    def create(self, vals):
        sequence_type = vals.get(
            'sequence_type',
            self._context.get('default_sequence_type', False))
        prefix = vals.get(
            'prefix',
            self._context.get('default_prefix', False))
        company_id = vals.get(
            'company_id',
            self._context.get('default_company_id', False))

        if (
                sequence_type == 'automatic' and
                not vals.get('sequence_id', False) and
                company_id):
            seq_vals = {
                'name': vals['name'],
                'implementation': 'no_gap',
                'prefix': prefix,
                'padding': 8,
                'number_increment': 1
            }
            sequence = self.env['ir.sequence'].sudo().create(seq_vals)
            vals.update({
                'sequence_id': sequence.id
            })
        return super(AccountPaymentReceiptbook, self).create(vals)
