# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import fields
from odoo.addons.account_reports.tests.common import TestAccountReportsCommon
from odoo.tools import date_utils
from odoo.modules.module import get_module_resource
from dateutil.relativedelta import relativedelta
import logging
import codecs

_logger = logging.getLogger(__name__)


class TestReports(TestAccountReportsCommon):

    @classmethod
    def setUpClass(cls, chart_template_ref='l10n_ar.l10nar_ri_chart_template'):
        super().setUpClass(chart_template_ref=chart_template_ref)
        cls.maxDiff = None

        # TODO these test cases depend on demo data that could be modified by the user before
        # running the tests
        # Login to (AR) Responsable Inscripto company
        company_ri = cls.env.ref('l10n_ar.company_ri')
        cls.env.user.write({'company_ids': [(4, company_ri.id)]})
        context = dict(cls.env.context, allowed_company_ids=[company_ri.id])
        cls.env = cls.env(context=context)

        cls.vat_book = cls.env['l10n_ar.vat.book']
        today = fields.Date.today()
        cls.options = cls._init_options(
            cls,
            cls.vat_book,
            today + relativedelta(years=0, month=1, day=1),
            today + relativedelta(years=0, month=12, day=31),
        )

    def _test_txt_file(self, filename):
        filetype = 1 if 'IVA' in filename else 0
        out_txt = self.vat_book._get_txt_files(self.options)[filetype].decode('ISO-8859-1')
        res_file = codecs.open(get_module_resource('l10n_ar_reports', 'tests', filename), 'r', encoding='ISO-8859-1').read()

        # The example files where generate on 2021-03-01, we need to update this files dates to ensure
        # that will match the date where this test is running
        today = fields.Date.today()
        # Replace last date of month with last date of the last date of the next month
        res_file = res_file.replace('20210430', (fields.Date.end_of(date_utils.add(today, months=1), 'month')).strftime('%Y%m%d'))
        # change all 202103xx dates to the current month
        res_file = res_file.replace('202103', today.strftime('%Y%m'))

        self.assertEqual(out_txt, res_file)

    def test_01_sale_vat_book_vouchers(self):
        self.options.update({'journal_type': 'sale', 'txt_type': 'sale'})
        self._test_txt_file('Ventas.txt')

    def test_02_sale_vat_book_aliquots(self):
        self.options.update({'journal_type': 'sale', 'txt_type': 'sale'})
        self._test_txt_file('IVA_Ventas.txt')

    def test_03_purchase_vat_book_purchases_voucher(self):
        self.options.update({'journal_type': 'purchase', 'txt_type': 'purchases'})
        self._test_txt_file('Compras.txt')

    def test_04_purchase_vat_book_purchases_aliquots(self):
        self.options.update({'journal_type': 'purchase', 'txt_type': 'purchases'})
        self._test_txt_file('IVA_Compras.txt')

    def test_05_purchase_vat_book_goods_import_voucher(self):
        self.options.update({'journal_type': 'purchase', 'txt_type': 'goods_import'})
        self._test_txt_file('Importaciones_de_Bienes.txt')

    def test_06_purchase_vat_book_goods_import_aliquots(self):
        self.options.update({'journal_type': 'purchase', 'txt_type': 'goods_import'})
        self._test_txt_file('IVA_Importaciones_de_Bienes.txt')
