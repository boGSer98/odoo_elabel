from odoo import Command, fields
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestShopSummary(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.website = cls.env['website'].create({'name': 'QA e-Label shop', 'company_id': cls.env.company.id})
        cls.env.company.elabel_base_url = 'https://labels.example.invalid'
        cls.lang = cls.env['res.lang'].search([('code', '=', 'en_US')], limit=1)

    def product(self, **values):
        return self.env['product.template'].with_context(lang='en_US').create({
            'name': 'Synthetic shop e-Label', 'sale_ok': True,
            'company_id': self.env.company.id, 'website_id': self.website.id, 'is_published': True,
            'elabel_ingredients': 'Grapes', 'elabel_allergen_statement': 'Contains sulphites',
            'elabel_energy_kj': 100, 'elabel_energy_kcal': 24,
            'elabel_source': 'Synthetic test data', 'elabel_checked_on': fields.Date.today(),
            'elabel_nutrition_confirmed': True, 'elabel_allergens_confirmed': True,
            'elabel_language_ids': [Command.set(self.lang.ids)], **values})

    def publish(self, product):
        product.action_submit_elabel()
        product.action_publish_elabel()
        return product

    def test_no_publication_no_summary(self):
        self.assertFalse(self.product()._get_website_elabel_summary(self.website))

    def test_public_user_gets_whitelisted_snapshot(self):
        p = self.publish(self.product())
        result = p.with_user(self.website.user_id).with_context(allowed_company_ids=[self.env.company.id])._get_website_elabel_summary(self.website)
        self.assertEqual(result['ingredients'], 'Grapes')
        self.assertEqual(result['allergens'], 'Contains sulphites')
        self.assertEqual(len(result['nutrition_lines']), 7)
        self.assertEqual(set(result), {'labels', 'ingredients', 'allergens', 'additional_substances', 'nutrition_note', 'nutrition_lines'})

    def test_unapproved_edit_does_not_leak(self):
        p = self.publish(self.product())
        p.elabel_ingredients = 'PRIVATE UNAPPROVED CHANGES'
        self.assertEqual(p._get_website_elabel_summary(self.website)['ingredients'], 'Grapes')

    def test_unpublished_product_hidden(self):
        p = self.publish(self.product())
        p.is_published = False
        self.assertFalse(p._get_website_elabel_summary(self.website))

    def test_disabled_label_hidden(self):
        p = self.publish(self.product())
        p.action_disable_elabel()
        self.assertFalse(p._get_website_elabel_summary(self.website))

    def test_archived_product_hidden(self):
        p = self.publish(self.product())
        p.active = False
        self.assertFalse(p._get_website_elabel_summary(self.website))

    def test_other_website_hidden(self):
        p = self.publish(self.product())
        other = self.env['website'].create({'name': 'Other QA site', 'company_id': self.env.company.id})
        self.assertFalse(p._get_website_elabel_summary(other))

    def test_other_company_hidden(self):
        p = self.publish(self.product(website_id=False))
        company = self.env['res.company'].new({'name': 'Other synthetic company'})
        other = self.env['website'].new({'name': 'Other company site', 'company_id': company.id})
        self.assertFalse(p._get_website_elabel_summary(other))

    def test_missing_language_uses_published_fallback(self):
        p = self.publish(self.product())
        self.assertEqual(p.with_context(lang='de_DE')._get_website_elabel_summary(self.website)['ingredients'], 'Grapes')

    def test_template_escapes_ingredients_and_preserves_zero_nutrients(self):
        p = self.publish(self.product(elabel_ingredients='<script>alert(1)</script>'))
        html = str(self.env['ir.qweb']._render('odoo_elabel_sale.website_sale_elabel_summary', {
            'elabel_summary': p._get_website_elabel_summary(self.website)}))
        self.assertNotIn('<script>', html)
        self.assertIn('&lt;script&gt;', html)
        self.assertIn('0.00 g', html)

    def test_empty_summary_has_no_box(self):
        html = str(self.env['ir.qweb']._render('odoo_elabel_sale.website_sale_elabel_summary', {'elabel_summary': False}))
        self.assertNotIn('o_elabel_product_summary', html)
