##############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
##############################################################################
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class AccountPaymentGroupInvoiceWizard(models.TransientModel):
    _name = "account.payment.group.invoice.wizard"
    _description = "account.payment.group.invoice.wizard"

    @api.model
    def default_payment_group(self):
        return self.env['account.payment.group'].browse(
            self._context.get('active_id', False))

    payment_group_id = fields.Many2one(
        'account.payment.group',
        default=default_payment_group,
        ondelete='cascade',
        required=True,
    )
    journal_id = fields.Many2one(
        'account.journal',
        'Journal',
        required=True,
        ondelete='cascade',
    )
    date_invoice = fields.Date(
        string='Refund Date',
        default=fields.Date.context_today,
        required=True
    )
    currency_id = fields.Many2one(
        related='payment_group_id.currency_id',
    )
    date = fields.Date(
        string='Accounting Date'
    )
    product_id = fields.Many2one(
        'product.product',
        required=True,
        domain=[('sale_ok', '=', True)],
    )
    tax_ids = fields.Many2many(
        'account.tax',
        string='Taxes',
    )
    amount_untaxed = fields.Monetary(
        string='Untaxed Amount',
        required=True,
        compute='_compute_amount_untaxed',
        inverse='_inverse_amount_untaxed',
    )
    # we make amount total the main one and the other computed because the
    # normal case of use would be to know the total amount and also this amount
    # is the suggested one on creating the wizard
    amount_total = fields.Monetary(
        string='Total Amount',
        required=True
    )
    description = fields.Char(
        string='Reason',
    )
    company_id = fields.Many2one(
        related='payment_group_id.company_id',
    )
    account_analytic_id = fields.Many2one(
        'account.analytic.account',
        'Analytic Account',
    )

    @api.onchange('product_id')
    def change_product(self):
        self.ensure_one()
        if self.payment_group_id.partner_type == 'supplier':
            taxes = self.product_id.supplier_taxes_id
        else:
            taxes = self.product_id.taxes_id
        company = self.company_id or self.env.user.company_id
        taxes = taxes.filtered(lambda r: r.company_id == company)
        self.tax_ids = self.payment_group_id.partner_id.with_context(
            force_company=company.id).property_account_position_id.map_tax(
                taxes)

    @api.onchange('amount_untaxed', 'tax_ids')
    def _inverse_amount_untaxed(self):
        self.ensure_one()
        if self.tax_ids:
            taxes = self.tax_ids.compute_all(
                self.amount_untaxed, self.company_id.currency_id, 1.0,
                product=self.product_id,
                partner=self.payment_group_id.partner_id)
            self.amount_total = taxes['total_included']
        else:
            self.amount_total = self.amount_untaxed

    @api.depends('tax_ids', 'amount_total')
    def _compute_amount_untaxed(self):
        """
        For now we implement inverse only for percent taxes.
        """
        self.ensure_one()
        tax_percent = 0.0
        for tax in self.tax_ids.filtered(
                lambda x: not x.price_include):
            if tax.amount_type == 'percent':
                tax_percent += tax.amount
            elif tax.amount_type == 'partner_tax':
                tax_percent += tax.get_partner_alicuot(
                    self.payment_group_id.partner_id,
                    fields.Date.context_today(self)).alicuota_percepcion
            else:
                raise ValidationError(_(
                    'You can only set amount total if taxes are of type '
                    'percentage'))
        total_percent = (1 + tax_percent / 100) or 1.0
        self.amount_untaxed = self.amount_total / total_percent

    @api.onchange('payment_group_id')
    def change_payment_group(self):
        journal_type = 'sale'
        type_tax_use = 'sale'
        if self.payment_group_id.partner_type == 'supplier':
            journal_type = 'purchase'
            type_tax_use = 'purchase'
        journal_domain = [
            ('type', '=', journal_type),
            ('company_id', '=', self.payment_group_id.company_id.id),
        ]
        tax_domain = [
            ('type_tax_use', '=', type_tax_use),
            ('company_id', '=', self.payment_group_id.company_id.id)]
        self.journal_id = self.env['account.journal'].search(
            journal_domain, limit=1)
        self.amount_total = abs(self.payment_group_id.payment_difference)
        return {'domain': {
            'journal_id': journal_domain,
            'tax_ids': tax_domain,
        }}

    def _get_move_type(self):
        self.ensure_one()
        payment_group = self.payment_group_id
        if payment_group.partner_type == 'supplier':
            move_type = 'in_'
        else:
            move_type = 'out_'

        if self._context.get('refund'):
            move_type += 'refund'
        else:
            move_type += 'invoice'
        return move_type

    def confirm(self):
        self.ensure_one()
        payment_group = self.payment_group_id
        move_type = self._get_move_type()

        # Determine the account for the invoice line
        if move_type in ('out_invoice', 'out_refund'):
            account = self.product_id.property_account_income_id or \
                self.product_id.categ_id.property_account_income_categ_id
        else:
            account = self.product_id.property_account_expense_id or \
                self.product_id.categ_id.property_account_expense_categ_id

        invoice = self.env['account.move'].create({
            'move_type': move_type,
            'invoice_date': self.date_invoice,
            'date': self.date or self.date_invoice,
            'ref': self.description,
            'journal_id': self.journal_id.id,
            'partner_id': payment_group.partner_id.id,
            'invoice_line_ids': [(0, 0, {
                'product_id': self.product_id.id,
                'name': self.product_id.name,
                'price_unit': self.amount_untaxed,
                'tax_ids': [(6, 0, self.tax_ids.ids)],
                'account_id': account.id,
                'analytic_account_id': self.account_analytic_id.id if self.account_analytic_id else False,
            })],
        })
        invoice.action_post()

        self.payment_group_id.to_pay_move_line_ids += (
            invoice.line_ids.filtered(
                lambda l: l.account_id.account_type in (
                    'asset_receivable', 'liability_payable')
            )
        )
