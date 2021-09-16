##############################################################################
#
#    Copyright (C) 2015  ADHOC SA  (http://www.adhoc.com.ar)
#    All Rights Reserved.
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
{
    'author': 'ADHOC SA',
    'license': 'AGPL-3',
    'category': 'Accounting & Finance',
    'data': [
        'views/account_tax_view.xml',
        'views/account_payment_group_view.xml',
        'views/account_payment_view.xml',
        'security/ir.model.access.csv',
    ],
    'demo': [
    ],
    'depends': [
        'account_payment_group',
        'account_withholding',
    ],
    'installable': True,
    'name': 'Retenciones automaticas en pagos',
    'test': [],
    'version': '13.0.1.1.0',
}
