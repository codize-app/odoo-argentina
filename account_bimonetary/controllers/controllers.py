# -*- coding: utf-8 -*-
# from odoo import http


# class AccountBimonetary(http.Controller):
#     @http.route('/account_bimonetary/account_bimonetary', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/account_bimonetary/account_bimonetary/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('account_bimonetary.listing', {
#             'root': '/account_bimonetary/account_bimonetary',
#             'objects': http.request.env['account_bimonetary.account_bimonetary'].search([]),
#         })

#     @http.route('/account_bimonetary/account_bimonetary/objects/<model("account_bimonetary.account_bimonetary"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('account_bimonetary.object', {
#             'object': obj
#         })
