##############################################################################
#
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
    'name': 'Actualización de Tipos de Cambio',
    'author': 'ADHOC SA, Exemax, Codize',
    'license': 'AGPL-3',
    'category': 'Accounting/Localizations',
    'data': [
        'views/currency_view.xml',
        'data/cron_jobs.xml'
    ],
    'demo': [],
    'depends': [
        'l10n_ar',
        'l10n_ar_afipws',
        'l10n_ar_afipws_fe'
    ],
    'installable': True,
    'test': [],
    'version': '14.0.1.1.0',
}
