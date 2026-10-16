import base64
from unittest.mock import patch
from odoo.addons.odoo_elabel_documents.models.documents import ElabelDocuments
from odoo import Command, fields
from odoo.exceptions import AccessError, UserError
from odoo.tests import TransactionCase, tagged
from odoo.addons.odoo_elabel_documents.hooks import uninstall_hook

@tagged('post_install','-at_install')
class TestElabelDocuments(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env.company.elabel_base_url='https://labels.example.invalid'
        cls.Doc=cls.env['documents.document']
        cls.lang=cls.env['res.lang'].search([('code','=','en_US')],limit=1)
        def user(name,groups,company=None):
            company=company or cls.env.company
            return cls.env['res.users'].with_context(no_reset_password=True).create({'name':name,'login':name,
                'company_id':company.id,'company_ids':[Command.set(company.ids)],
                'group_ids':[Command.set([cls.env.ref(g).id for g in groups])]})
        cls.editor=user('elabel-doc-editor',['product.group_product_manager','odoo_elabel.group_elabel_editor','documents.group_documents_user'])
        cls.other=user('elabel-doc-ordinary',['base.group_user','documents.group_documents_user'])
        cls.portal=user('elabel-doc-portal',['base.group_portal'])
        cls.foreign_company=cls.env['res.company'].create({'name':'TEST other label company'})
        cls.foreign=user('elabel-doc-foreign',['odoo_elabel.group_elabel_editor','documents.group_documents_user'],cls.foreign_company)

    def published(self,**values):
        p=self.env['product.template'].create({'name':'TEST managed documents','company_id':self.env.company.id,
           'elabel_ingredients':'Grapes','elabel_energy_kj':100,'elabel_energy_kcal':24,
           'elabel_nutrition_confirmed':True,'elabel_allergens_confirmed':True,'elabel_source':'Test source',
           'elabel_checked_on':fields.Date.today(),'elabel_translation_checked':True,
           'elabel_language_ids':[Command.set(self.lang.ids)]}|values)
        p.action_submit_elabel();p.action_publish_elabel()
        with patch.object(type(p),'_generate_elabel_pdf',return_value=b'%PDF-TEST'):
            p.with_user(self.editor).action_generate_elabel_documents()
        return p

    def docs(self,p):
        return self.Doc.search([('attachment_id.elabel_revision_id','=',p.elabel_current_revision_id.id)])

    def test_one_shared_root(self):
        root=self.Doc._elabel_folder();self.assertEqual(root,self.Doc._elabel_folder())
        self.assertEqual(root.name,'E-Label');self.assertEqual(root.type,'folder');self.assertFalse(root.company_id)
        self.assertEqual(self.Doc.search_count([('elabel_root','=',True)]),1)

    def test_generation_linked_without_file_copy(self):
        p=self.published();docs=self.docs(p);self.assertEqual(len(docs),2)
        self.assertEqual(docs.folder_id,self.Doc._elabel_folder())
        self.assertEqual(docs.attachment_id, self.env['ir.attachment'].search([('elabel_revision_id','=',p.elabel_current_revision_id.id)]))
        self.assertTrue(all(a.res_model=='product.template' and a.res_id==p.id for a in docs.attachment_id))

    def test_regeneration_no_duplicate_document(self):
        p=self.published();docs=self.docs(p)
        with patch.object(type(p),'_generate_elabel_pdf',return_value=b'%PDF-TEST'):
            p.with_user(self.editor).action_generate_elabel_documents()
        self.assertEqual(self.docs(p),docs)

    def test_private_links_no_members(self):
        docs=self.docs(self.published())
        self.assertTrue(all(d.access_via_link=='none' and d.is_access_via_link_hidden for d in docs))
        self.assertFalse(docs.access_ids);self.assertFalse(any(docs.attachment_id.mapped('public')))

    def test_editor_can_read(self):
        docs=self.docs(self.published()).with_user(self.editor)
        docs.check_access('read');self.assertTrue(all(x.user_permission in ('view','edit') for x in docs))

    def test_ordinary_portal_foreign_blocked(self):
        docs=self.docs(self.published())
        for user in [self.other,self.portal,self.foreign]:
            d=docs.with_user(user).with_context(allowed_company_ids=user.company_ids.ids)
            with self.assertRaises(AccessError):d.check_access('read')
            self.assertTrue(all(p=='none' for p in d.sudo()._get_permission_without_token_multi().values()))

    def test_documents_system_role_cannot_cross_company(self):
        self.foreign.group_ids=[Command.link(self.env.ref('documents.group_documents_system').id)]
        docs=self.docs(self.published()).with_user(self.foreign).with_context(allowed_company_ids=self.foreign.company_ids.ids)
        with self.assertRaises(AccessError):docs.check_access('read')
        self.assertTrue(all(x.user_permission=='none' for x in docs.sudo()))

    def test_managed_no_reshare_move_delete(self):
        docs=self.docs(self.published())
        for vals in [{'access_via_link':'view'},{'company_id':False},{'elabel_managed':False},{'folder_id':False}]:
            with self.assertRaises(AccessError):docs.write(vals)
        with self.assertRaises(UserError):docs.unlink()
        with self.assertRaises(UserError):docs[0].copy()

    def test_cannot_wrap_managed_attachment_as_public_doc(self):
        doc=self.docs(self.published())[0]
        with self.assertRaises(AccessError):self.Doc.create({'attachment_id':doc.attachment_id.id,'access_via_link':'view'})

    def test_unrelated_document_unaffected(self):
        doc=self.Doc.create({'name':'Ordinary private document','type':'folder','owner_id':self.other.id})
        doc.with_user(self.other).write({'name':'Renamed ordinary document'})
        self.assertFalse(doc.elabel_managed)

    def test_existing_document_reused_after_explicit_adoption(self):
        p=self.published()
        # A different language is intentional: only one file per revision/kind/language.
        de=self.env['res.lang']._activate_lang('de_DE')
        p.write({'elabel_language_ids':[Command.set((self.lang|de).ids)]})
        p.action_submit_elabel();p.action_publish_elabel()
        attachment=self.env['ir.attachment'].with_context(no_document=True).create({
            'name':'old_label.pdf','datas':base64.b64encode(b'%PDF-legacy'),
            'mimetype':'application/pdf','res_model':'product.template','res_id':p.id})
        existing=self.Doc.create({'attachment_id':attachment.id,'name':'old_label.pdf','access_via_link':'view'})
        wizard=self.env['wine.elabel.adoption'].create({'product_id':p.id,'lang_id':de.id,
           'attachment_ids':[Command.set(attachment.ids)],'confirmed':True})
        wizard.action_adopt();self.assertEqual(self.Doc.search([('attachment_id','=',attachment.id)]),existing)
        self.assertTrue(existing.elabel_managed);self.assertEqual(existing.folder_id,self.Doc._elabel_folder())
        self.assertEqual(existing.access_via_link,'none')

    def test_uninstall_policy_preserves_files_closes_access(self):
        docs=self.docs(self.published());attachments=docs.attachment_id
        uninstall_hook(self.env)
        self.assertEqual(len(docs.exists()),2);self.assertEqual(len(attachments.exists()),2)
        self.assertTrue(all(d.access_internal=='none' and d.access_via_link=='none' for d in docs))

    def test_shared_product_keeps_global_url_and_global_document_company(self):
        self.env['ir.config_parameter'].sudo().set_param('web.base.url','https://global-label.example.invalid')
        self.env.company.elabel_base_url='https://company-label.example.invalid'
        p=self.published(company_id=False);docs=self.docs(p)
        self.assertEqual(p._get_elabel_base_url(),'https://global-label.example.invalid')
        self.assertFalse(docs.mapped('company_id'))
        self.assertEqual(p.with_company(self.foreign.company_id)._get_elabel_base_url(),p._get_elabel_base_url())

    def test_confirmed_existing_empty_root_can_be_adopted(self):
        root=self.Doc._elabel_folder()
        super(ElabelDocuments,root).write({'elabel_root':False,'elabel_managed':False})
        self.env['wine.elabel.folder.setup'].create({'folder_id':root.id,'confirmed':True}).action_setup()
        self.assertEqual(self.Doc.search([('elabel_root','=',True)]),root)

    def test_confirmed_known_label_root_can_be_reused(self):
        p=self.published();docs=self.docs(p);root=docs.folder_id
        super(ElabelDocuments,root|docs).write({'elabel_root':False,'elabel_managed':False})
        self.env['wine.elabel.folder.setup'].create({'folder_id':root.id,'confirmed':True}).action_setup()
        self.assertEqual(self.Doc.search([('elabel_root','=',True)]),root)
        self.assertTrue(all(d.elabel_managed and d.access_via_link=='none' for d in docs))
