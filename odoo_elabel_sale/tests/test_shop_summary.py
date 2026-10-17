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
        self.assertEqual(len(result['nutrition_lines']), 1)
        self.assertEqual(set(result), {'labels', 'ingredients', 'allergens', 'additional_substances', 'nutrition_note', 'nutrition_lines', 'analysis_lines'})

    def test_unapproved_edit_does_not_leak(self):
        p = self.publish(self.product())
        p.elabel_ingredients = 'PRIVATE UNAPPROVED CHANGES'
        self.assertEqual(p._get_website_elabel_summary(self.website)['ingredients'], 'Grapes')

    def test_unpublished_product_label_remains_public(self):
        p = self.publish(self.product())
        p.is_published = False
        self.assertEqual(p._get_website_elabel_summary(self.website)['ingredients'], 'Grapes')

    def test_disabled_label_hidden(self):
        p = self.publish(self.product())
        p.action_disable_elabel()
        self.assertFalse(p._get_website_elabel_summary(self.website))

    def test_archived_product_label_remains_public(self):
        p = self.publish(self.product())
        p.active = False
        self.assertEqual(p._get_website_elabel_summary(self.website)['ingredients'], 'Grapes')

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

    def test_shop_escapes_ingredients_and_hides_zero_nutrients(self):
        p = self.publish(self.product(elabel_ingredients='<script>alert(1)</script>'))
        html = str(self.env['ir.qweb']._render('odoo_elabel_sale.website_sale_elabel_summary', {
            'elabel_summary': p._get_website_elabel_summary(self.website)}))
        self.assertNotIn('<script>', html)
        self.assertIn('&lt;script&gt;', html)
        self.assertNotIn('0.00 g', html)
        self.assertEqual(len(p.elabel_current_revision_id._presentation('en_US')._get_elabel_nutrition_lines()), 7)

    def test_empty_summary_has_no_box(self):
        html = str(self.env['ir.qweb']._render('odoo_elabel_sale.website_sale_elabel_summary', {'elabel_summary': False}))
        self.assertNotIn('o_elabel_product_summary', html)

    def snippet_summary(self, product, website=None, lang=None):
        from types import SimpleNamespace
        from unittest.mock import patch
        from odoo.addons.odoo_elabel_sale.controllers.snippet import ElabelSnippet
        website = website or self.website
        public_env = self.env(user=website.user_id.id, context=dict(self.env.context, allowed_company_ids=[website.company_id.id]))
        with patch('odoo.addons.odoo_elabel_sale.controllers.snippet.request', SimpleNamespace(env=public_env, website=website)):
            return ElabelSnippet()._summary(product, lang)

    def test_snippet_uses_released_summary(self):
        p = self.publish(self.product())
        p.elabel_ingredients = 'UNRELEASED'
        result, code = self.snippet_summary(p.id)
        self.assertEqual(result['ingredients'], 'Grapes')

    def test_snippet_survives_unpublication_but_respects_label_disable(self):
        p = self.publish(self.product())
        p.is_published = False
        self.assertEqual(self.snippet_summary(p.id)[0]['ingredients'], 'Grapes')
        p.is_published = True
        p.action_disable_elabel()
        self.assertFalse(self.snippet_summary(p.id)[0])

    def test_snippet_rejects_foreign_site(self):
        p = self.publish(self.product())
        other = self.env['website'].create({'name': 'Other snippet site', 'company_id': self.env.company.id})
        self.assertFalse(self.snippet_summary(p.id, website=other)[0])

    def test_snippet_invalid_identifiers_are_empty(self):
        for value in [False, -1, 0, 2147483648, '42']:
            self.assertFalse(self.snippet_summary(value)[0])

    def test_snippet_language_is_restricted_to_site(self):
        p = self.publish(self.product())
        result, code = self.snippet_summary(p.id, lang='../../invalid')
        self.assertTrue(result)
        self.assertNotEqual(code, '../../invalid')

    def test_public_label_survives_all_product_statuses(self):
        cases = [dict(is_published=False), dict(sale_ok=False), dict(active=False),
                 dict(active=False, is_published=False, sale_ok=False)]
        for changes in cases:
            with self.subTest(changes=changes):
                p = self.publish(self.product())
                before = (p.elabel_token, p.elabel_current_revision_id.id)
                p.write(changes)
                p.elabel_ingredients = 'PRIVATE DRAFT AFTER WITHDRAWAL'
                public = p.with_user(self.website.user_id).with_context(allowed_company_ids=[self.env.company.id])
                summary = public._get_website_elabel_summary(self.website)
                self.assertEqual(summary['ingredients'], 'Grapes')
                self.assertEqual(self.snippet_summary(p.id)[0]['ingredients'], 'Grapes')
                self.assertEqual((p.elabel_token, p.elabel_current_revision_id.id), before)
                self.assertEqual(set(summary), {'labels', 'ingredients', 'allergens', 'additional_substances', 'nutrition_note', 'nutrition_lines', 'analysis_lines'})
                p.action_disable_elabel()
                self.assertFalse(public._get_website_elabel_summary(self.website))
                self.assertFalse(self.snippet_summary(p.id)[0])

    def test_archived_unreleased_product_still_hidden(self):
        p = self.product(active=False, is_published=False, sale_ok=False)
        self.assertFalse(p._get_website_elabel_summary(self.website))
        self.assertFalse(self.snippet_summary(p.id)[0])

    def test_archived_labels_still_respect_site_and_company(self):
        p = self.publish(self.product())
        p.write(dict(active=False, is_published=False, sale_ok=False))
        other = self.env['website'].create({'name': 'Wrong label site', 'company_id': self.env.company.id})
        self.assertFalse(self.snippet_summary(p.id, website=other)[0])
        p.website_id = False
        company = self.env['res.company'].create({'name': 'Foreign label company'})
        other.company_id = company
        self.assertFalse(self.snippet_summary(p.id, website=other)[0])

    def test_builder_domain_includes_archived_label(self):
        p = self.publish(self.product())
        p.write(dict(active=False, is_published=False, sale_ok=False))
        domain = [('id', '=', p.id), ('active', 'in', [True, False]), ('elabel_enabled', '=', True),
                  ('elabel_current_revision_id', '!=', False), ('website_id', 'in', [False, self.website.id]),
                  ('company_id', 'in', [False, self.website.company_id.id])]
        self.assertEqual(self.env['product.template'].with_context(active_test=True).search(domain), p)
        names = self.env['product.template'].with_context(active_test=True).name_search(domain=domain)
        self.assertEqual([item[0] for item in names], p.ids)

    def test_zero_stock_does_not_hide_label(self):
        if 'is_storable' not in self.env['product.template']._fields:
            self.skipTest('Stock is not installed')
        p = self.publish(self.product(is_storable=True))
        self.assertEqual(p.qty_available, 0)
        self.assertEqual(self.snippet_summary(p.id)[0]['ingredients'], 'Grapes')

    def test_label_button_outside_purchase_wrapper(self):
        view = self.env.ref('odoo_elabel_sale.website_sale_product_elabel_button')
        self.assertEqual(view.inherit_id, self.env.ref('website_sale.product'))
        from lxml import etree
        root = etree.fromstring(view.arch_db.encode())
        anchors = root.xpath('self::xpath | .//xpath')
        self.assertEqual(len(anchors), 1)
        self.assertEqual(anchors[0].get('position'), 'after')
        self.assertIn('website_sale.cta_wrapper', anchors[0].get('expr'))
        self.assertNotIn('add_to_cart_wrap', view.arch_db)

    def test_shop_all_zero_hides_nutrition_table(self):
        p = self.publish(self.product(elabel_energy_kj=0, elabel_energy_kcal=0))
        summary = p._get_website_elabel_summary(self.website)
        self.assertEqual(summary['nutrition_lines'], [])
        html = str(self.env['ir.qweb']._render('odoo_elabel_sale.website_sale_elabel_summary', {'elabel_summary': summary}))
        self.assertNotIn('<table', html)
        self.assertIn('Grapes', html)
        self.assertEqual(len(p.elabel_current_revision_id._presentation('en_US')._get_elabel_nutrition_lines()), 7)

    def test_shop_zero_energy_component_hidden_only_in_shop(self):
        p = self.publish(self.product(elabel_energy_kj=0, elabel_energy_kcal=24, elabel_fat=0.004, elabel_salt=0.01))
        summary = p._get_website_elabel_summary(self.website)
        self.assertEqual([row['value'] for row in summary['nutrition_lines']], ['24.00 kcal', '0.01 g'])
        standalone = p.elabel_current_revision_id._presentation('en_US')._get_elabel_nutrition_lines()
        self.assertEqual(standalone[0]['value'], '0.00 kJ / 24.00 kcal')
