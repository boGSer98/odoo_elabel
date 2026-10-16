from odoo import api, fields, models, Command
from odoo.exceptions import AccessError, UserError

class ElabelDocuments(models.Model):
    _inherit='documents.document'
    elabel_managed=fields.Boolean(copy=False,index=True)
    elabel_root=fields.Boolean(copy=False,index=True)
    elabel_revision_id=fields.Many2one(string='Fassung',related='attachment_id.elabel_revision_id',readonly=True)
    elabel_document_kind=fields.Selection(string='Dateiart',related='attachment_id.elabel_document_kind',readonly=True)
    elabel_document_lang=fields.Char(string='Sprache',related='attachment_id.elabel_document_lang',readonly=True)

    def _auto_init(self):
        result=super()._auto_init()
        self.env.cr.execute('CREATE UNIQUE INDEX IF NOT EXISTS documents_elabel_single_root ON documents_document (elabel_root) WHERE elabel_root')
        return result

    def _elabel_allowed(self):
        self.ensure_one()
        role=self.env.user.has_group('base.group_system') or self.env.user.has_group('odoo_elabel.group_elabel_editor')
        return bool(role and (not self.company_id or self.company_id in self.env.companies))

    def _get_permission_without_token_multi(self):
        result=super()._get_permission_without_token_multi()
        for d in self:
            if d.elabel_managed and not d._elabel_allowed():result[d]='none'
        return result

    def _ensure_user_role_without_propagation(self, role, documents_per_user):
        # Managed labels deliberately do not preserve former-owner grants when
        # adopted. This also avoids native grants to an inactive system owner.
        ordinary={owner:docs.filtered(lambda d:not d.elabel_managed) for owner,docs in documents_per_user.items()}
        ordinary={owner:docs for owner,docs in ordinary.items() if docs}
        if ordinary:
            return super()._ensure_user_role_without_propagation(role,ordinary)
        return None

    def _compute_user_permission(self):
        super()._compute_user_permission()
        for d in self:
            if d.elabel_managed and not d._elabel_allowed():d.user_permission='none'

    @api.model
    def _elabel_folder(self):
        # Transaction scoped: keep the reservation until commit, including callers
        # that generate several documents inside one business transaction.
        self.env.cr.execute('SELECT pg_advisory_xact_lock(180019014)')
        Model=self.sudo().with_context(active_test=False)
        roots=Model.search([('elabel_root','=',True)],limit=2)
        if len(roots)>1:raise UserError(self.env._('Mehrere e-Label-Wurzelordner gefunden. Bitte administrativ prüfen.'))
        if roots:
            if not roots.active:raise UserError(self.env._('Der E-Label-Ordner ist archiviert. Bitte administrativ prüfen.'))
            return roots
        if Model.search_count([('name','=','E-Label'),('type','=','folder'),('folder_id','=',False)]):
            raise UserError(self.env._('Ein Ordner E-Label existiert bereits. Bitte einen leeren Ordner über die e-Label-Ordnerkonfiguration ausdrücklich übernehmen.'))
        return super(ElabelDocuments,Model).create(self._elabel_folder_values())

    def _elabel_folder_values(self):
        return {'name':'E-Label','type':'folder','folder_id':False,'company_id':False,
                'owner_id':False,'elabel_managed':True,'elabel_root':True,
                'access_internal':'view','access_via_link':'none','is_access_via_link_hidden':True,
                'access_ids':[Command.clear()]}

    @api.model
    def _elabel_sync(self,product,attachment,revision):
        product._elabel_require_role(write=True)
        if (attachment.elabel_revision_id!=revision or revision.product_id!=product or
                attachment.res_model!='product.template' or attachment.res_id!=product.id):
            raise AccessError(self.env._('Die Datei gehört nicht zu dieser Label-Veröffentlichung.'))
        Model=self.sudo().with_context(active_test=False,no_document=True)
        root=Model._elabel_folder()
        records=Model.search([('attachment_id','=',attachment.id)])
        if len(records)>1:raise UserError(self.env._('Zu diesem Anhang existieren mehrere Dokumenteinträge. Bitte vor Übernahme administrativ prüfen.'))
        vals={'name':attachment.name,'attachment_id':attachment.id,'folder_id':root.id,
              'company_id':product.company_id.id,'owner_id':False,'active':True,
              'elabel_managed':True,'access_internal':'view','access_via_link':'none',
              'is_access_via_link_hidden':True,'access_ids':[Command.clear()]}
        if records:
            super(ElabelDocuments,records).write(vals)
        else:
            records=super(ElabelDocuments,Model).create(vals)
        # Native ownership changes may preserve previous-owner access. Remove
        # explicit memberships after the move, preserving only our gated policy.
        super(ElabelDocuments,records).write({'access_ids':[Command.clear()]})
        return records

    @api.model_create_multi
    def create(self,vals_list):
        for vals in vals_list:
            if vals.get('elabel_managed') or vals.get('elabel_root') or (vals.get('attachment_id') and
               self.env['ir.attachment'].sudo().browse(vals['attachment_id']).elabel_revision_id):
                raise AccessError(self.env._('Verwenden Sie die e-Label-Dokumentaktionen.'))
        return super().create(vals_list)

    def write(self,vals):
        # Native read-authorized thumbnail generation is presentation metadata,
        # not a change to the immutable file or its sharing policy.
        if self and set(vals) <= {'thumbnail','thumbnail_status'} and all(d.elabel_managed and d._elabel_allowed() for d in self):
            return super().write(vals)
        if any(k.startswith('elabel_') for k in vals) or self.filtered('elabel_managed') or (
            vals.get('attachment_id') and self.env['ir.attachment'].sudo().browse(vals['attachment_id']).elabel_revision_id):
            raise AccessError(self.env._('e-Label-Dokumente sind nachweisgeschützt. Freigabe, Ablage und Zugriff werden über das e-Label-Modul verwaltet.'))
        return super().write(vals)

    def unlink(self):
        if self.filtered('elabel_managed'):raise UserError(self.env._('e-Label-Nachweisdokumente und ihr gemeinsamer Ordner dürfen nicht gelöscht werden.'))
        return super().unlink()

    def copy(self,default=None):
        if self.elabel_managed:raise UserError(self.env._('Verwenden Sie die e-Label-Dokumenterzeugung statt einer unkontrollierten Kopie.'))
        return super().copy(default)

class ProductTemplate(models.Model):
    _inherit='product.template'
    def _elabel_after_attachment(self,attachment,revision):
        super()._elabel_after_attachment(attachment,revision)
        self.env['documents.document']._elabel_sync(self,attachment,revision)

    def action_elabel_documents(self):
        self.ensure_one();self._elabel_require_role()
        return {'type':'ir.actions.act_window','name':'E-Label-Dokumente','res_model':'documents.document',
                'view_mode':'list,form','domain':[('elabel_managed','=',True),('res_model','=','product.template'),('res_id','=',self.id)]}

class ElabelFolderSetup(models.TransientModel):
    _name='wine.elabel.folder.setup'
    _description='Gemeinsamen E-Label-Ordner konfigurieren'
    folder_id=fields.Many2one('documents.document',domain="[('type','=','folder'),('name','=','E-Label')]",string='Vorhandenen E-Label-Ordner übernehmen')
    confirmed=fields.Boolean(string='Geprüften Labelordner übernehmen und auf private e-Label-Berechtigungen umstellen')

    def action_setup(self):
        self.ensure_one()
        if not self.env.is_admin():raise AccessError(self.env._('Nur die technische Administration darf den gemeinsamen Ordner konfigurieren.'))
        Model=self.env['documents.document']
        self.env.cr.execute('SELECT pg_advisory_xact_lock(180019014)')
        if self.folder_id:
            folder=self.folder_id
            folder.check_access('write')
            children=Model.sudo().with_context(active_test=False).search([('folder_id','child_of',folder.id),('id','!=',folder.id)])
            if (not self.confirmed or folder.type!='folder' or folder.name!='E-Label' or
                    any(d.type!='binary' or not d.attachment_id.elabel_revision_id for d in children)):
                raise UserError(self.env._('Nur ein bestätigter leerer Ordner oder ausschließlich nachweislich verwaltete e-Label-Dateien dürfen übernommen werden.'))
            if Model.sudo().search_count([('elabel_root','=',True),('id','!=',folder.id)]):
                raise UserError(self.env._('Der gemeinsame E-Label-Ordner ist bereits eingerichtet.'))
            super(ElabelDocuments,folder.sudo()).write(Model._elabel_folder_values())
            super(ElabelDocuments,folder.sudo()).write({'access_ids':[Command.clear()]})
            for child in children:
                product=child.attachment_id.elabel_revision_id.product_id.with_env(self.env)
                Model._elabel_sync(product,child.attachment_id,child.attachment_id.elabel_revision_id)
        else:folder=Model._elabel_folder()
        return {'type':'ir.actions.act_window','name':'E-Label','res_model':'documents.document',
                'view_mode':'list,form','domain':[('id','=',folder.id)]}
