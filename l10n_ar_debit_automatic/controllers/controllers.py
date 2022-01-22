# -*- coding: utf-8 -*-
# from odoo import http


# class L10nArDebitAutomatic(http.Controller):
#     @http.route('/l10n_ar_debit_automatic/l10n_ar_debit_automatic/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/l10n_ar_debit_automatic/l10n_ar_debit_automatic/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('l10n_ar_debit_automatic.listing', {
#             'root': '/l10n_ar_debit_automatic/l10n_ar_debit_automatic',
#             'objects': http.request.env['l10n_ar_debit_automatic.l10n_ar_debit_automatic'].search([]),
#         })

#     @http.route('/l10n_ar_debit_automatic/l10n_ar_debit_automatic/objects/<model("l10n_ar_debit_automatic.l10n_ar_debit_automatic"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('l10n_ar_debit_automatic.object', {
#             'object': obj
#         })
