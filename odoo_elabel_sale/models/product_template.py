from odoo import models
from odoo.tools.misc import formatLang
from odoo.tools.float_utils import float_is_zero


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    def _get_website_elabel_summary(self, website):
        """Only expose the same immutable publication as the public e-label."""
        self.ensure_one()
        website.ensure_one()
        # A released label is public independently of product/shop permissions.
        # Elevate only this read-only projection; never return the private product.
        self = self.sudo().with_context(active_test=False)
        if (not self.exists() or (self.website_id and self.website_id != website)
                or (self.company_id and self.company_id != website.company_id)
                or not self.elabel_enabled or not self.elabel_token):
            return False
        # Keep site/company boundaries and explicit label release; expose only display
        # values from the immutable revision, never a product or raw payload.
        revision = self.sudo().elabel_current_revision_id
        if not revision or revision.product_id.id != self.id:
            return False
        label = revision._presentation(self.env.lang)
        fmt = lambda value: formatLang(label.env, value, digits=2)
        visible = lambda value: not float_is_zero(value, precision_digits=2)
        original = label._get_elabel_nutrition_lines()
        energy = ['%s %s' % (fmt(value), unit) for value, unit in
                  [(label.elabel_energy_kj, 'kJ'), (label.elabel_energy_kcal, 'kcal')] if visible(value)]
        nutrition = ([dict(original[0], value=' / '.join(energy))] if energy else [])
        for line, field in zip(original[1:], ['elabel_fat', 'elabel_saturates', 'elabel_carbohydrate',
                                            'elabel_sugars', 'elabel_protein', 'elabel_salt']):
            if visible(getattr(label, field)):
                nutrition.append(line)
        values = revision.payload.get('wine_analysis', {})
        analysis = []
        for name, title, unit in [('elabel_acidity_g_l', 'Acidity', 'g/l'),
                                  ('elabel_residual_sugar_g_l', 'Residual sugar', 'g/l'),
                                  ('elabel_alcohol_percent', 'Alcohol content', '%')]:
            value = values.get(name, 0.0)
            if visible(value):
                analysis.append({'label': label.env._(title), 'value': '%s %s' % (fmt(value), unit)})
        return {
            'labels': label._get_elabel_display_labels(),
            'ingredients': label.elabel_ingredients,
            'allergens': label.elabel_allergen_statement,
            'additional_substances': label.elabel_additional_substances,
            'nutrition_note': label.elabel_nutrition_note,
            'nutrition_lines': nutrition,
            'analysis_lines': analysis,
        }
