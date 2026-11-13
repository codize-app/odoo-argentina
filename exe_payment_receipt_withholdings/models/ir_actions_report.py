from collections import OrderedDict
from io import BytesIO

from odoo import models, _
from odoo.exceptions import UserError


RECEIPT_REPORT = 'account_payment_group.report_payment_group'
WITHHOLDING_REPORT = 'l10n_ar_withholding_automatic.report_payment_withholding'
MERGING_CONTEXT = 'exe_receipt_withholdings_rendering'


class IrActionsReport(models.Model):
    _inherit = 'ir.actions.report'

    def _render_qweb_pdf_prepare_streams(self, report_ref, data, res_ids=None):
        report = self._get_report(report_ref)
        if (
            self.env.context.get(MERGING_CONTEXT)
            or report.model != 'account.payment.group'
            or report.report_name != RECEIPT_REPORT
            or not res_ids
        ):
            return super()._render_qweb_pdf_prepare_streams(report_ref, data, res_ids=res_ids)

        ids = [res_ids] if isinstance(res_ids, int) else list(res_ids)
        # Isolate each receipt so that batch printing remains receipt/certificates,
        # receipt/certificates, including receipts that occupy several pages.
        renderer = self.with_context(**{
            MERGING_CONTEXT: True,
            'report_pdf_no_attachment': True,
        })
        result = OrderedDict()
        groups = self.env['account.payment.group'].browse(list(dict.fromkeys(ids)))
        for group in groups:
            originals = super(IrActionsReport, renderer)._render_qweb_pdf_prepare_streams(
                report_ref, dict(data or {}), res_ids=[group.id],
            )
            original = originals.get(group.id) or originals.get(False)
            if not original or original.get('stream') is None:
                raise UserError(_('No se pudo generar el PDF de la orden de pago.'))
            payments = group._exe_receipt_withholding_payments()
            if not payments:
                result[group.id] = original
                continue

            streams = [original['stream']]
            try:
                for payment in payments:
                    certificate, kind = renderer._render_qweb_pdf(
                        WITHHOLDING_REPORT, res_ids=[payment.id], data={},
                    )
                    if kind != 'pdf' or not certificate:
                        raise UserError(_('No se pudo generar el certificado de retención.'))
                    streams.append(BytesIO(certificate))
                for stream in streams:
                    stream.seek(0)
                merged = renderer._merge_pdfs(streams)
                # Odoo appends the merged stream to `streams`; retain only its
                # bytes before closing all intermediate streams.
                merged.seek(0)
                content = merged.read()
                if merged not in streams:
                    merged.close()
            finally:
                for stream in streams:
                    stream.close()
            result[group.id] = dict(original, stream=BytesIO(content))
        return result
