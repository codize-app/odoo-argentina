from odoo import fields, models, api

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'
    tax_ret_sircar_neuquen = fields.Many2one(
        'account.tax',
        'Impuesto de Retencion',
        domain=[('type_tax_use', '=', 'sale'),('tax_group_id.l10n_ar_tribute_afip_code','=','07')], 
        config_parameter='l10n_ar_tax.sircar_neuquen'
    )