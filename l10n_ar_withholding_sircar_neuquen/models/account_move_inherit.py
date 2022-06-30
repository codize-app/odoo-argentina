# -*- coding: utf-8 -*-
from odoo import models, api, fields
from collections import defaultdict
from odoo.tools.misc import formatLang, format_date, get_lang
import logging
_logger = logging.getLogger(__name__)

class AccountMoveInherit(models.Model):
    _inherit = "account.move"

    def _check_balanced(self):
        for rec in self:
            if rec.move_type == 'out_invoice' or rec.move_type == 'out_refund':
                if rec.invoice_line_ids:
                    if rec.partner_id:
                        if len(rec.partner_id.alicuot_per_sircar_neuquen_ids) > 0:
                            return True
        res = super(AccountMoveInherit, self)._check_balanced()
        return res

    def calculate_perceptions(self):
        if self.move_type == 'out_invoice' or self.move_type == 'out_refund':
            if self.invoice_line_ids:
                if self.partner_id:
                    if len(self.partner_id.alicuot_per_sircar_neuquen_ids) > 0:
                        #Busco el impuesto a utilizar para la percepcion
                        imp_per_sircar_neuquen = self.env['account.tax'].browse(int(self.env['ir.config_parameter'].sudo().get_param('l10n_ar_tax.sircar_neuquen')))

                        # Cambio el amount del impuesto por el valor que tenga el partner en el padron
                        imp_per_sircar_neuquen.amount = self.partner_id.alicuot_per_sircar_neuquen_ids.filtered(lambda l: l.padron_activo == True)[0].a_per
                        # Recomerremos las lineas en busca de si ya se encuentra el impuesto de percepcion, de caso contrario se agrega
                        for iline in self.invoice_line_ids:
                            _tiene_precepcion = 0

                            for tax in iline.tax_ids:
                                if str(imp_per_sircar_neuquen.id) == str(tax.id)[-2:]:
                                    _tiene_precepcion = 1
                            if not _tiene_precepcion:
                                iline.write({'tax_ids': [(4, imp_per_sircar_neuquen.id)]})
                                
                        # Recomputamos Apuntes contables y actualizamos el valor de Cuenta a Pagar por el total de la factura
                        self._recompute_tax_lines(recompute_tax_base_amount=False)
                        for lac in self.line_ids:
                            if lac.account_id.id == self.partner_id.property_account_receivable_id.id:
                                lac.write({'debit' : self.amount_total})

        return super(AccountMoveInherit, self).calculate_perceptions()