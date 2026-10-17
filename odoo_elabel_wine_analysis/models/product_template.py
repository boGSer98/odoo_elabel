import math
from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools.misc import formatLang
from odoo.addons.odoo_elabel.models.presentation import CONTENT_FIELDS

ANALYSIS_FIELDS = ('elabel_acidity_g_l', 'elabel_residual_sugar_g_l', 'elabel_alcohol_percent')


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    elabel_acidity_g_l = fields.Float(string='Säuregehalt (g/l)', digits=(16, 2))
    elabel_residual_sugar_g_l = fields.Float(string='Restsüße (g/l)', digits=(16, 2))
    elabel_alcohol_percent = fields.Float(string='Alkoholgehalt (%)', digits=(16, 2))

    def _elabel_content_fields(self):
        return super()._elabel_content_fields() + ANALYSIS_FIELDS

    def _elabel_check_input(self, vals):
        super()._elabel_check_input(vals)
        for name in ANALYSIS_FIELDS:
            if name in vals:
                try:
                    valid = math.isfinite(float(vals[name] or 0)) and float(vals[name] or 0) >= 0
                except (ValueError, TypeError, OverflowError):
                    valid = False
                if not valid:
                    raise ValidationError(self.env._('Weinanalytik benötigt endliche, nicht negative Zahlen.'))

    @api.constrains(*ANALYSIS_FIELDS)
    def _check_elabel_analysis(self):
        for product in self:
            product._elabel_check_input({name: product[name] for name in ANALYSIS_FIELDS})

    def _elabel_validate_publication(self):
        super()._elabel_validate_publication()
        self._check_elabel_analysis()

    def _elabel_payload(self):
        payload = super()._elabel_payload()
        values = {name: self[name] for name in ANALYSIS_FIELDS}
        # Preserve legacy payload hashes when the optional fields are all unset.
        if any(values.values()):
            payload['wine_analysis'] = values
        return payload

    @api.depends(*CONTENT_FIELDS, *ANALYSIS_FIELDS, 'name', 'elabel_current_revision_id', 'elabel_language_ids')
    def _compute_elabel_document_state(self):
        return super()._compute_elabel_document_state()

    def _get_elabel_pdf_analysis_lines(self):
        """Only released values, independent of live drafts and website scope."""
        self.ensure_one()
        self.check_access('read')
        revision = self.elabel_current_revision_id
        if not revision:
            return []
        values = revision.payload.get('wine_analysis', {})
        if not values:
            return []
        label = self._elabel_document_record()
        return [{'label': label.env._(title),
                 'value': '%s %s' % (formatLang(label.env, values[field], digits=2), unit)}
                for field, title, unit in [
                    ('elabel_alcohol_percent', 'Alcohol content', '%'),
                    ('elabel_residual_sugar_g_l', 'Residual sugar', 'g/l'),
                    ('elabel_acidity_g_l', 'Acidity', 'g/l')]
                if field in values]
