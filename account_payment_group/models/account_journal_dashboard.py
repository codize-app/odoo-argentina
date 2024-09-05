# -*- coding: utf-8 -*-
from odoo import api, fields, models, _, Command
from odoo.osv import expression
from odoo.exceptions import UserError, ValidationError
from odoo.addons.base.models.res_bank import sanitize_account_number
from odoo.tools import remove_accents
import logging
import re
import warnings

class AccountJournal(models.Model):
    _inherit = "account.journal"

    inbound_payment_method_ids = fields.Many2many(
        comodel_name='account.payment.method',
        relation='account_journal_inbound_payment_method_rel',
        column1='journal_id',
        column2='inbound_payment_method',
        domain=[('payment_type', '=', 'inbound')],
        string='Inbound Payment Methods',
        compute='_compute_inbound_payment_method_line_ids',
        store=True,
        readonly=False,
        help="Manual: Reciba el pago en efectivo, cheque o cualquier otro método fuera de Odoo.\n"
             "Electrónico: Reciba el pago automáticamente a través de un adquirente de pagos solicitando una transacción"
             " en una tarjeta guardada por el cliente al comprar o suscribirse en línea (token de pago).\n"
             "Depósito por lotes: Encajone varios cheques de clientes a la vez generando un depósito por lotes para"
             " enviarlo a su banco. Al codificar el extracto bancario en Odoo, se le sugiere que"
             " concilie la transacción con el depósito por lotes. Habilite esta opción desde la configuración."
    )
    outbound_payment_method_ids = fields.Many2many(
        comodel_name='account.payment.method',
        relation='account_journal_outbound_payment_method_rel',
        column1='journal_id',
        column2='outbound_payment_method',
        domain=[('payment_type', '=', 'outbound')],
        string='Outbound Payment Methods',
        compute='_compute_outbound_payment_method_line_ids',
        store=True,
        readonly=False,
        help="Manual: Pagar facturas en efectivo o con cualquier otro método fuera de Odoo.\n"
             "Cheque: Pagar facturas con cheque e imprimirlo desde Odoo.\n"
             "Transferencia de crédito SEPA: Pagar facturas desde un archivo de transferencia de crédito SEPA que envíe a su banco. Habilite esta opción desde la configuración."
    )
    at_least_one_inbound = fields.Boolean(compute='_methods_compute', store=True)
    at_least_one_outbound = fields.Boolean(compute='_methods_compute', store=True)

    @api.depends('type')
    def _compute_default_account_type(self):
        default_account_id_types = {
            'bank': 'account.data_account_type_liquidity',
            'cash': 'account.data_account_type_liquidity',
            'sale': 'account.data_account_type_revenue',
            'purchase': 'account.data_account_type_expenses'
        }

        for journal in self:
            if journal.type in default_account_id_types:
                journal.default_account_type = self.env.ref(
                    default_account_id_types[journal.type]).id
            else:
                journal.default_account_type = False

    @api.depends('type', 'currency_id')
    def _compute_inbound_payment_method_line_ids(self):
        for journal in self:
            pay_method_line_ids_commands = [Command.clear()]
            if journal.type in ('bank', 'cash'):
                default_methods = journal._default_inbound_payment_methods()
                pay_method_line_ids_commands += [Command.create({
                    'name': pay_method.name,
                    'payment_method_id': pay_method.id,
                }) for pay_method in default_methods]
            journal.inbound_payment_method_line_ids = pay_method_line_ids_commands
            journal.inbound_payment_method_ids = journal.inbound_payment_method_line_ids.mapped('payment_method_id').ids

    @api.depends('type', 'currency_id')
    def _compute_outbound_payment_method_line_ids(self):
        for journal in self:
            pay_method_line_ids_commands = [Command.clear()]
            if journal.type in ('bank', 'cash'):
                default_methods = journal._default_outbound_payment_methods()
                pay_method_line_ids_commands += [Command.create({
                    'name': pay_method.name,
                    'payment_method_id': pay_method.id,
                }) for pay_method in default_methods]
            journal.outbound_payment_method_line_ids = pay_method_line_ids_commands
            journal.outbound_payment_method_ids = journal.outbound_payment_method_line_ids.mapped('payment_method_id').ids

    @api.depends('inbound_payment_method_ids', 'outbound_payment_method_ids')
    def _methods_compute(self):
        for journal in self:
            journal.at_least_one_inbound = bool(
                len(journal.inbound_payment_method_ids))
            journal.at_least_one_outbound = bool(
                len(journal.outbound_payment_method_ids))
