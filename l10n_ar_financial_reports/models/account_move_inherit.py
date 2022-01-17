from odoo import models, api, fields, _
from odoo.exceptions import ValidationError


class AccountMove(models.Model):
    _inherit = "account.move"

    @api.depends('invoice_line_ids')
    def _get_tax(self):
        for rec in self:
            rec.iva21 = 0
            rec.iva10 = 0
            rec.iva27 = 0
            rec.no_gravado = 0
            rec.iva_no_corresponde = 0
            rec.iva_exento = 0
            if rec.invoice_line_ids:
                for line in rec.invoice_line_ids:
                    if len(line.tax_ids) > 0:
                        for tax in line.tax_ids:
                            if tax.tax_group_id.l10n_ar_vat_afip_code == '5':
                                rec.iva21 = rec.iva21 + line.price_subtotal * 0.21
                            elif tax.tax_group_id.l10n_ar_vat_afip_code == '4':
                                rec.iva10 = rec.iva10 + line.price_subtotal * 0.105
                            elif tax.tax_group_id.l10n_ar_vat_afip_code == '6':
                                rec.iva27 = rec.iva27 + line.price_subtotal * 0.27
                            elif tax.tax_group_id.l10n_ar_vat_afip_code == '1':
                                rec.no_gravado = rec.no_gravado + line.price_subtotal
                            elif tax.tax_group_id.l10n_ar_vat_afip_code == '0':
                                rec.iva_no_corresponde = rec.iva_no_corresponde + line.price_subtotal
                            elif tax.tax_group_id.l10n_ar_vat_afip_code == '2':
                                rec.iva_exento = rec.iva_exento + line.price_subtotal
                

    document_partner = fields.Char(string="Documento", related = 'partner_id.vat')
    
    iva10 = fields.Float(string="Iva %10.5", compute=_get_tax)
    iva21 = fields.Float(string="Iva %21", compute=_get_tax)
    iva27 = fields.Float(string="Iva %27", compute=_get_tax)
    no_gravado = fields.Float(string="Iva No Gravado", compute=_get_tax)
    iva_no_corresponde = fields.Float(string="Iva No Corresponde", compute=_get_tax)
    iva_exento = fields.Float(string="Iva Exento", compute=_get_tax)