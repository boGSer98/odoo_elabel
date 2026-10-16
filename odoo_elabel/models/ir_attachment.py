from odoo import api, fields, models
from odoo.exceptions import AccessError, UserError

class IrAttachment(models.Model):
    _inherit='ir.attachment'

    elabel_revision_id=fields.Many2one('wine.elabel.revision',ondelete='restrict',copy=False,index=True)
    elabel_document_kind=fields.Selection([('pdf','PDF'),('svg','QR-SVG')],copy=False)
    elabel_document_lang=fields.Char(copy=False)
    elabel_source_hash=fields.Char(copy=False)
    _elabel_document_unique=models.Constraint('UNIQUE(elabel_revision_id,elabel_document_kind,elabel_document_lang)',
        'Für diese Label-Fassung, Sprache und Dokumentart existiert bereits ein Dokument.')

    def _elabel_store(self,vals):
        revision=self.env['wine.elabel.revision'].browse(vals['elabel_revision_id']).exists()
        if not revision or vals.get('res_model')!='product.template' or vals.get('res_id')!=revision.product_id.id:
            raise AccessError(self.env._('Ungültige Label-Dokumentzuordnung.'))
        product=revision.product_id.with_user(self.env.user)
        product._elabel_require_role(write=True)
        if self and (len(self)!=1 or self.res_model!='product.template' or self.res_id!=product.id):
            raise AccessError(self.env._('Ein fremder Anhang darf nicht als Label überschrieben werden.'))
        vals=dict(vals,public=False,access_token=False)
        target=self.sudo().with_context(no_document=True)
        if target:
            super(IrAttachment,target).write(vals)
            return target
        return super(IrAttachment,target).create(vals)

    def write(self,vals):
        # Native mail PDF previews persist a thumbnail after checking write
        # access. Keep that auxiliary cache writable, never the PDF/SVG bytes.
        if set(vals) <= {'thumbnail'}:
            self.with_user(self.env.user).check_access('write')
            return super().write(vals)
        if self.env.su and set(vals) <= {'index_content'}:
            return super().write(vals)
        if any(k.startswith('elabel_') for k in vals) or self.filtered('elabel_revision_id'):
            raise AccessError(self.env._('Verwaltete e-Label-Dateien werden nur über die Label-Aktionen geändert.'))
        return super().write(vals)

    @api.model_create_multi
    def create(self,vals_list):
        values=vals_list if isinstance(vals_list,list) else [vals_list]
        if any(any(k.startswith('elabel_') for k in v) for v in values):
            raise AccessError(self.env._('Verwenden Sie die Label-Dokumenterzeugung.'))
        return super().create(vals_list)

    def copy(self,default=None):
        if self.elabel_revision_id:
            raise UserError(self.env._('Verwenden Sie die e-Label-Dokumenterzeugung statt unkontrollierter Dateikopien.'))
        return super().copy(default)

    def unlink(self):
        if self.filtered('elabel_revision_id'):
            raise UserError(self.env._('Label-Veröffentlichungsdokumente werden aus Nachweisgründen aufbewahrt.'))
        return super().unlink()
