from odoo import models


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
        return {
            'labels': label._get_elabel_display_labels(),
            'ingredients': label.elabel_ingredients,
            'allergens': label.elabel_allergen_statement,
            'additional_substances': label.elabel_additional_substances,
            'nutrition_note': label.elabel_nutrition_note,
            'nutrition_lines': label._get_elabel_nutrition_lines(),
        }
