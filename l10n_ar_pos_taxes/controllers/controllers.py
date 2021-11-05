# -*- coding: utf-8 -*-
# from odoo import http


# class L10nArPosInternalTaxes(http.Controller):
#     @http.route('/l10n_ar_pos_internal_taxes/l10n_ar_pos_internal_taxes/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/l10n_ar_pos_internal_taxes/l10n_ar_pos_internal_taxes/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('l10n_ar_pos_internal_taxes.listing', {
#             'root': '/l10n_ar_pos_internal_taxes/l10n_ar_pos_internal_taxes',
#             'objects': http.request.env['l10n_ar_pos_internal_taxes.l10n_ar_pos_internal_taxes'].search([]),
#         })

#     @http.route('/l10n_ar_pos_internal_taxes/l10n_ar_pos_internal_taxes/objects/<model("l10n_ar_pos_internal_taxes.l10n_ar_pos_internal_taxes"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('l10n_ar_pos_internal_taxes.object', {
#             'object': obj
#         })
