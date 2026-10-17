from odoo import Command, fields
from odoo.tests import TransactionCase, tagged
from odoo.exceptions import ValidationError, AccessError


@tagged('post_install', '-at_install')
class TestWineAnalysis(TransactionCase):
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


    def test_analysis_snapshot_and_draft_isolation(self):
        p = self.publish(self.product(elabel_acidity_g_l=6.5, elabel_residual_sugar_g_l=12.2, elabel_alcohol_percent=11.5))
        token = p.elabel_token
        before = p._get_website_elabel_summary(self.website)['analysis_lines']
        self.assertEqual([r['value'] for r in before], ['6.50 g/l', '12.20 g/l', '11.50 %'])
        self.assertEqual([r['label'] for r in before], ['Acidity', 'Residual sugar', 'Alcohol content'])
        p.elabel_acidity_g_l = 7.25
        self.assertEqual(p.elabel_state, 'draft')
        self.assertTrue(p.elabel_pending_changes)
        self.assertEqual(p._get_website_elabel_summary(self.website)['analysis_lines'], before)
        self.publish(p)
        self.assertEqual(p._get_website_elabel_summary(self.website)['analysis_lines'][0]['value'], '7.25 g/l')
        self.assertEqual(p.elabel_token, token)

    def test_zero_optional_fields_and_legacy_payload(self):
        p = self.publish(self.product())
        self.assertNotIn('wine_analysis', p.elabel_current_revision_id.payload)
        self.assertFalse(p.elabel_pending_changes)
        self.assertEqual(p._get_website_elabel_summary(self.website)['analysis_lines'], [])
        p.elabel_alcohol_percent = 12.3
        self.assertTrue(p.elabel_pending_changes)
        self.assertEqual(p._get_website_elabel_summary(self.website)['analysis_lines'], [])

    def test_zero_fields_hidden_after_publication(self):
        p = self.publish(self.product(elabel_acidity_g_l=0, elabel_residual_sugar_g_l=0.004, elabel_alcohol_percent=12.3))
        rows = p._get_website_elabel_summary(self.website)['analysis_lines']
        self.assertEqual(rows, [{'label': 'Alcohol content', 'value': '12.30 %'}])
        p.elabel_alcohol_percent = 0
        self.publish(p)
        self.assertEqual(p._get_website_elabel_summary(self.website)['analysis_lines'], [])

    def test_standalone_stays_mandatory_only(self):
        p = self.publish(self.product(elabel_acidity_g_l=6.5, elabel_residual_sugar_g_l=8.7, elabel_alcohol_percent=11.5))
        label = p.elabel_current_revision_id._presentation('en_US')
        self.assertFalse(hasattr(label, 'elabel_acidity_g_l'))
        rows = label._get_elabel_nutrition_lines()
        self.assertEqual(len(rows), 7)
        self.assertIn('0.00 g', [r['value'] for r in rows])
        html = str(self.env['ir.qweb']._render('odoo_elabel.wine_elabel_page', {'product_tmpl':label, 'lang_code':'en_US', 'elabel_languages':[]}))
        self.assertNotIn('6.50 g/l', html)
        self.assertIn('0.00 g', html)

    def test_invalid_analysis_rejected(self):
        for key in ['elabel_acidity_g_l', 'elabel_residual_sugar_g_l', 'elabel_alcohol_percent']:
            for value in [-1, float('nan'), float('inf')]:
                with self.subTest(key=key,value=value), self.assertRaises(ValidationError), self.cr.savepoint():
                    self.product(**{key:value})

    def test_analysis_writes_require_label_role(self):
        user = self.env['res.users'].with_context(no_reset_password=True).create({'name':'Analysis ordinary user','login':'analysis-ordinary@example.invalid',
          'group_ids':[Command.set([self.env.ref('base.group_user').id])]})
        p = self.product()
        with self.assertRaises(AccessError):
            p.with_user(user).write({'elabel_acidity_g_l':5.5})
        with self.assertRaises(AccessError):
            self.env['product.template'].with_user(user).create({'name':'Unauthorized analysis', 'elabel_alcohol_percent':12.2})

    def test_pdf_analysis_uses_released_snapshot_not_draft(self):
        p = self.publish(self.product(elabel_acidity_g_l=6.5, elabel_residual_sugar_g_l=12.2, elabel_alcohol_percent=11.5))
        before = p._get_elabel_pdf_analysis_lines()
        self.assertEqual([row['label'] for row in before], ['Alcohol content', 'Residual sugar', 'Acidity'])
        self.assertEqual([row['value'] for row in before], ['11.50 %', '12.20 g/l', '6.50 g/l'])
        p.elabel_alcohol_percent = 19.99
        self.assertEqual(p._get_elabel_pdf_analysis_lines(), before)
        self.publish(p)
        self.assertEqual(p._get_elabel_pdf_analysis_lines()[0]['value'], '19.99 %')

    def test_pdf_legacy_and_unreleased_have_no_invented_analysis(self):
        p = self.product()
        self.assertEqual(p._get_elabel_pdf_analysis_lines(), [])
        self.publish(p)
        self.assertEqual(p._get_elabel_pdf_analysis_lines(), [])
        p.elabel_alcohol_percent = 12.3
        self.assertEqual(p._get_elabel_pdf_analysis_lines(), [])

    def test_pdf_keeps_released_zero_values_separate_from_shop_filter(self):
        p = self.publish(self.product(elabel_alcohol_percent=12.3))
        self.assertEqual([row['value'] for row in p._get_elabel_pdf_analysis_lines()], ['12.30 %', '0.00 g/l', '0.00 g/l'])
        self.assertEqual(len(p._get_website_elabel_summary(self.website)['analysis_lines']), 1)

    def test_pdf_html_has_analysis_and_full_nutrition(self):
        p = self.publish(self.product(elabel_acidity_g_l=6.5, elabel_residual_sugar_g_l=12.2, elabel_alcohol_percent=11.5))
        p.elabel_alcohol_percent = 19.99
        rendered = str(self.env['ir.qweb'].with_context(lang='en_US')._render(
            'odoo_elabel.report_wine_elabel_pdf_document', {'docs':p}))
        self.assertIn('o_elabel_pdf_analysis', rendered)
        self.assertIn('11.50 %', rendered)
        self.assertNotIn('19.99 %', rendered)
        self.assertIn('12.20 g/l', rendered)
        self.assertIn('6.50 g/l', rendered)
        self.assertIn('0.00 g', rendered)
