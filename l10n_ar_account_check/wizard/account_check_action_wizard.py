##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class AccountCheckActionWizard(models.TransientModel):
    _name = 'account.check.action.wizard'
    _description = 'Account Check Action Wizard'

    date = fields.Date(
        string="Fecha",
        default=fields.Date.context_today,
        required=True,
    )
    journal_id = fields.Many2one(
        'account.journal',
        string='Diario'
    )
    action_type = fields.Char(
        'Tipo de acción pasada en el contexto',
        required=True,
    )

    reference = fields.Char(
        string='Referencia'
    )
    
    grouped_entry = fields.Boolean(string='Asiento Agrupado', default=False)

    def action_confirm(self):
        self.ensure_one()
        if self.action_type not in [
                'claim', 'bank_debit', 'bank_deposit','reject', 'customer_return']:
            raise ValidationError(_(
                'La Acción %s no está soportada en cheques') % self.action_type)
        checks = self.env['account.check'].browse(
            self._context.get('active_ids'))

        if self.grouped_entry:
            total_amount = sum(check.amount for check in checks)
            if self.action_type == 'bank_deposit':
                res = checks[0].bank_deposit(date=self.date, journal_id=self.journal_id, ref=self.reference, checks=checks)
            else:
                res = getattr(
                    checks[0].with_context(action_date=self.date, journal_id=self.journal_id, amount=total_amount, ref=self.reference), self.action_type)()
        else:
            for check in checks:
                if self.action_type == 'bank_deposit':
                    res = check.bank_deposit(date=self.date, journal_id=self.journal_id, ref=self.reference, checks=[check])
                else:
                    res = getattr(
                        check.with_context(action_date=self.date, journal_id=self.journal_id, ref=self.reference), self.action_type)()

        if len(checks) == 1:
            return res
        else:
            return True