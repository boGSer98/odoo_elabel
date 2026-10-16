import base64
import uuid
from unittest.mock import patch
from psycopg2 import IntegrityError
from odoo import Command, fields
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tests import TransactionCase, tagged
from odoo.addons.odoo_elabel.models.product_template import ProductTemplate
from odoo.addons.odoo_elabel.models.presentation import NUMBER_FIELDS

@tagged('post_install','-at_install')
class TestElabel(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Product=cls.env['product.template']
        cls.env.company.elabel_base_url='https://labels.example.invalid'
        def user(name,groups):
            return cls.env['res.users'].with_context(no_reset_password=True).create({
                'name':name,'login':name,'company_id':cls.env.company.id,
                'company_ids':[Command.set(cls.env.companies.ids)],
                'group_ids':[Command.set([cls.env.ref(g).id for g in groups])]})
        cls.reader=user('elabel-reader',['base.group_user'])
        cls.writer=user('elabel-product-only',['base.group_user','product.group_product_manager'])
        cls.editor=user('elabel-editor',['product.group_product_manager','odoo_elabel.group_elabel_editor'])
        cls.reviewer=user('elabel-reviewer',['product.group_product_manager','odoo_elabel.group_elabel_reviewer'])
        cls.portal=user('elabel-portal',['base.group_portal'])
        cls.lang=cls.env['res.lang'].search([('code','=','en_US')],limit=1)

    def product(self,**values):
        return self.Product.create({'name':'TEST e-Label','company_id':self.env.company.id,
            'elabel_ingredients':'Grapes','elabel_energy_kj':100,'elabel_energy_kcal':24,
            'elabel_nutrition_confirmed':True,'elabel_allergens_confirmed':True,
            'elabel_source':'Synthetic laboratory fixture','elabel_checked_on':fields.Date.today(),
            'elabel_translation_checked':True,'elabel_language_ids':[Command.set(self.lang.ids)],**values})

    def publish(self,p):
        p.with_user(self.editor).action_submit_elabel()
        p.with_user(self.reviewer).action_publish_elabel()
        return p

    def generate(self,p):
        with patch.object(type(p),'_generate_elabel_pdf',return_value=b'%PDF-TEST-ONLY'):
            p.with_user(self.editor).action_generate_elabel_documents()
        return self.env['ir.attachment'].search([('elabel_revision_id','=',p.elabel_current_revision_id.id)])

    def test_draft_not_public(self):
        p=self.product();self.assertFalse(p.elabel_enabled);self.assertFalse(p.elabel_token)

    def test_workflow_and_stable_token(self):
        p=self.publish(self.product());token=p.elabel_token;first=p.elabel_current_revision_id
        p.with_user(self.editor).write({'elabel_ingredients':'Grapes, test ingredient'})
        self.assertEqual(p.elabel_state,'draft');self.assertTrue(p.elabel_enabled)
        self.assertEqual(first._presentation('en_US').elabel_ingredients,'Grapes')
        self.publish(p);self.assertEqual(p.elabel_token,token);self.assertEqual(p.elabel_current_revision_id.number,2)

    def test_publisher_needs_review(self):
        p=self.product()
        with self.assertRaises(UserError):p.with_user(self.reviewer).action_publish_elabel()

    def test_editor_cannot_publish(self):
        p=self.product();p.with_user(self.editor).action_submit_elabel()
        with self.assertRaises(AccessError):p.with_user(self.editor).action_publish_elabel()

    def test_product_writer_cannot_edit_label(self):
        p=self.product()
        with self.assertRaises(AccessError):p.with_user(self.writer).write({'elabel_ingredients':'Changed'})

    def test_direct_publish_and_token_override_denied(self):
        p=self.product()
        for vals in [{'elabel_enabled':True},{'elabel_token':'guessable'},{'elabel_state':'published'}]:
            with self.assertRaises(AccessError):p.write(vals)
        with self.assertRaises(AccessError):self.Product.create({'name':'bad','elabel_token':str(uuid.uuid4())})

    def test_readonly_preview_without_write(self):
        p=self.publish(self.product())
        p.with_user(self.reader).check_access('read')
        with self.assertRaises(AccessError):p.with_user(self.reader).check_access('write')
        self.assertTrue(p.with_user(self.reader).action_view_elabel_url()['url'])
        self.assertTrue(p.with_user(self.reader).action_view_elabel_qr_code()['url'])

    def test_reader_and_portal_cannot_generate(self):
        p=self.publish(self.product())
        for user in [self.reader,self.portal]:
            with self.assertRaises(AccessError):p.with_user(user).action_generate_elabel_documents()

    def test_empty_label_rejected(self):
        p=self.product(elabel_ingredients=False)
        with self.assertRaises(UserError):p.action_submit_elabel()

    def test_confirmations_source_date_languages_required(self):
        for vals in [{'elabel_nutrition_confirmed':False},{'elabel_allergens_confirmed':False},
                     {'elabel_source':False},{'elabel_checked_on':False},
                     {'elabel_language_ids':[Command.clear()]}]:
            p=self.product(**vals)
            with self.assertRaises(UserError):p.action_submit_elabel()

    def test_energy_screening(self):
        p=self.product(elabel_energy_kcal=1)
        self.assertTrue(p.elabel_nutrition_warning);self.publish(p)
        self.assertTrue(p.elabel_enabled)

    def test_invalid_numerical_values(self):
        for value in [-1,float('nan'),float('inf')]:
            with self.assertRaises(ValidationError):self.product(elabel_energy_kj=value)

    def test_nutrition_relationships(self):
        for vals in [{'elabel_sugars':8,'elabel_carbohydrate':1},{'elabel_saturates':4,'elabel_fat':1}]:
            p=self.product(**vals);self.assertTrue(p.elabel_nutrition_warning)
            self.publish(p);self.assertTrue(p.elabel_enabled)

    def test_archive_preserves_publication(self):
        p=self.publish(self.product());token=p.elabel_token;p.active=False
        self.assertTrue(p.elabel_enabled);self.assertEqual(p.elabel_token,token)
        self.assertEqual(self.Product.with_context(active_test=False).search([('elabel_token','=',token)]),p)

    def test_unique_token_includes_archive(self):
        p=self.publish(self.product());p.active=False
        with self.assertRaises(IntegrityError),self.cr.savepoint():
            super(ProductTemplate,self.Product).create({'name':'collision','elabel_token':p.elabel_token})

    def test_revision_cannot_be_mutated_or_deleted(self):
        p=self.publish(self.product());r=p.elabel_current_revision_id
        with self.assertRaises(AccessError):r.write({'payload':{}})
        with self.assertRaises(UserError):r.unlink()
        with self.assertRaises(UserError):p.unlink()

    def test_disable_keeps_token(self):
        p=self.publish(self.product());token=p.elabel_token;p.with_user(self.reviewer).action_disable_elabel()
        self.assertFalse(p.elabel_enabled);self.assertEqual(p.elabel_token,token)

    def test_document_identity_no_duplicates(self):
        p=self.publish(self.product());docs=self.generate(p);self.assertEqual(len(docs),2)
        p.default_code='Changed reference';self.assertEqual(self.generate(p),docs)
        self.assertFalse(any(docs.mapped('public')));self.assertFalse(any(docs.mapped('access_token')))

    def test_pending_edits_and_new_revision_documents(self):
        p=self.publish(self.product());docs=self.generate(p)
        p.with_user(self.editor).write({'elabel_ingredients':'Changed grapes'})
        self.assertTrue(p.elabel_pending_changes);self.assertTrue(p.elabel_documents_stale)
        self.assertEqual(p.elabel_current_revision_id._presentation('en_US').elabel_ingredients,'Grapes')
        self.publish(p);newdocs=self.generate(p);self.assertFalse(docs & newdocs)
        self.assertTrue(docs.exists());self.assertFalse(p.elabel_pending_changes)

    def test_managed_attachment_changes_denied(self):
        docs=self.generate(self.publish(self.product()))
        for vals in [{'public':True},{'datas':base64.b64encode(b'tampered')},{'elabel_source_hash':'fake'}]:
            with self.assertRaises(AccessError):docs.write(vals)
        with self.assertRaises(UserError):docs.unlink()

    def test_company_url_validation(self):
        for url in ['http://public.example.com','https://user:pass@example.com','https://example.com/path','javascript:alert(1)']:
            with self.assertRaises(ValidationError):self.env.company._elabel_validate_base_url(url)
        for url in ['https://labels.example.com','http://127.0.0.1:8998']:
            self.env.company._elabel_validate_base_url(url)

    def test_record_company_cannot_change(self):
        p=self.publish(self.product())
        with self.assertRaises(UserError):p.write({'company_id':False})

    def test_adoption_requires_explicit_confirmation(self):
        p=self.publish(self.product())
        a=self.env['ir.attachment'].create({'name':'old.pdf','datas':base64.b64encode(b'%PDF-old'),
           'res_model':'product.template','res_id':p.id,'mimetype':'application/pdf'})
        w=self.env['wine.elabel.adoption'].create({'product_id':p.id,'lang_id':self.lang.id,'attachment_ids':[Command.set(a.ids)]})
        with self.assertRaises(UserError):w.action_adopt();w.action_adopt()
        w.confirmed=True;w.action_adopt();w.action_adopt();self.assertEqual(a.elabel_revision_id,p.elabel_current_revision_id)
        self.assertFalse(a.elabel_source_hash)

    def test_regular_product_unaffected(self):
        p=self.Product.with_user(self.writer).create({'name':'Normal product'})
        p.write({'name':'Normal edited'});self.assertFalse(p.elabel_enabled)

    def test_managed_attachments_deny_plain_product_reader(self):
        p=self.product();self.publish(p);a=self.generate(p)
        self.assertTrue(p.with_user(self.reader).has_access('read'))
        for item in a:
            self.assertFalse(item.with_user(self.reader).has_access('read'))
            with self.assertRaises(AccessError):item.with_user(self.reader).read(['datas'])
        self.assertFalse(a.with_user(self.reader).search([('id','in',a.ids)]))

    def test_product_copy_starts_without_publication_or_token(self):
        p=self.product();self.publish(p);c=p.copy()
        self.assertFalse(c.elabel_token);self.assertFalse(c.elabel_enabled)
        self.assertFalse(c.elabel_current_revision_id);self.assertEqual(c.elabel_state,'draft')

    def test_native_thumbnail_cache_does_not_modify_or_share_label_bytes(self):
        p=self.publish(self.product());a=self.generate(p).filtered(lambda a:a.elabel_document_kind=='pdf')
        original=a.raw
        a.sudo().write({'thumbnail':base64.b64encode(b'<svg xmlns="http://www.w3.org/2000/svg"/>')})
        self.assertEqual(a.raw,original);self.assertFalse(a.public);self.assertFalse(a.access_token)
        with self.assertRaises(AccessError):a.with_user(self.reader).sudo().write({'thumbnail':False})

    def test_text_confirmation_not_required_even_for_multiple_languages(self):
        languages=self.env['res.lang'].search([('active','=',True)])
        p=self.product(elabel_translation_checked=False,elabel_language_ids=[Command.set(languages.ids)])
        self.publish(p);self.assertTrue(p.elabel_enabled);self.assertEqual(len(self.generate(p)),2)

    def test_zero_energy_warns_but_can_be_published(self):
        p=self.product(elabel_energy_kj=0,elabel_energy_kcal=0,elabel_translation_checked=False)
        self.assertTrue(p.elabel_nutrition_warning);self.publish(p);self.assertTrue(p.elabel_enabled)

    def test_nutrition_warning_clears_after_correction(self):
        p=self.product(elabel_sugars=8,elabel_carbohydrate=1)
        self.assertTrue(p.elabel_nutrition_warning)
        p.elabel_carbohydrate=8;self.assertFalse(p.elabel_nutrition_warning)

    def test_warning_display_does_not_modify_input_or_snapshot(self):
        p=self.product(elabel_sugars=8,elabel_carbohydrate=1)
        self.publish(p);r=p.elabel_current_revision_id
        self.assertEqual(r.payload['numbers']['elabel_sugars'],8)
        self.assertEqual(r.payload['numbers']['elabel_carbohydrate'],1)
