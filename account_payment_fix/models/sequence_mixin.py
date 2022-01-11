from odoo import fields, models, api
# from odoo.exceptions import ValidationError
import logging
_logger = logging.getLogger(__name__)

class SequenceMixin(models.AbstractModel):
    _inherit = 'sequence.mixin'

    def _get_sequence_temp(self):
        """get the las  sequence.
        """
        self.ensure_one()
        last_sequence = self._get_last_sequence()
        new = not last_sequence
        if new:
            last_sequence = self._get_last_sequencep(relaxed=True) or self._get_starting_sequence()

        format, format_values = self._get_sequence_format_param(last_sequence)
        if new:
            format_values['seq'] = 0
            format_values['year'] = self[self._sequence_date_field].year % (10 ** format_values['year_length'])
            format_values['month'] = self[self._sequence_date_field].month
        format_values['seq'] = format_values['seq']

        self[self._sequence_field] = format.format(**format_values)
        self._compute_split_sequence()