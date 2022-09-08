# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError
import logging
_logger = logging.getLogger(__name__)

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    def update_internal_taxes(self):
        has_internal_sale = False
        has_internal_purchase = False

        if not self.has_internal_taxes:
           return

        for rec in self.taxes_id:
            if rec.tax_group_id.l10n_ar_tribute_afip_code == '04':
                has_internal_sale = True
                rec.amount = self.internal_taxes
                if self.default_code:
                    rec.name = 'Imp. Int. ' + self.default_code
                else:
                    rec.name = 'Imp. Int. ' + self.name
                break

        for rec in self.supplier_taxes_id:
            if rec.tax_group_id.l10n_ar_tribute_afip_code == '04':
                has_internal_purchase = True
                rec.amount = self.internal_taxes
                if self.default_code:
                    rec.name = 'Imp. Int. ' + self.default_code
                else:
                    rec.name = 'Imp. Int. ' + self.name
                break

        group = self.env['account.tax.group'].search([('l10n_ar_tribute_afip_code', '=', '04')], limit=1)
        account = self.env['account.account'].search([('name', 'like', 'Impuestos Internos')], limit=1)

        if not has_internal_sale:
            if self.default_code:
                t_name = 'Imp. Int. ' + self.default_code
            else:
                t_name = 'Imp. Int. ' + self.name

            vals = {
                    'name': t_name,
                    'amount': self.internal_taxes,
                    'tax_group_id': group.id,
                    'type_tax_use': 'sale',
                    'amount_type': 'fixed'
            }
            self.taxes_id = [(0, 0, vals)]
            for rec in self.taxes_id:
                if rec.tax_group_id.l10n_ar_tribute_afip_code == '04':
                    rec.invoice_repartition_line_ids[1].account_id = account.id
                    rec.refund_repartition_line_ids[1].account_id = account.id

        if not has_internal_purchase:
            if self.default_code:
                t_name = 'Imp. Int. ' + self.default_code
            else:
                t_name = 'Imp. Int. ' + self.name

            vals = {
                    'name': t_name,
                    'amount': self.internal_taxes,
                    'tax_group_id': group.id,
                    'type_tax_use': 'purchase',
                    'amount_type': 'fixed'
            }
            self.supplier_taxes_id = [(0, 0, vals)]
            for rec in self.supplier_taxes_id:
                if rec.tax_group_id.l10n_ar_tribute_afip_code == '04':
                    rec.invoice_repartition_line_ids[1].account_id = account.id
                    rec.refund_repartition_line_ids[1].account_id = account.id

    has_internal_taxes = fields.Boolean('¿Tiene Impuestos Internos?')
    internal_taxes = fields.Float('Impuestos Internos', help='Suma total de los impuestos internos de este producto. Este valor se descontará del Precio de venta al ser facturado.')

class ProductProduct(models.Model):
    _inherit = 'product.product'

    internal_taxes = fields.Float('Impuestos Internos', related='product_tmpl_id.internal_taxes', readonly=True)
