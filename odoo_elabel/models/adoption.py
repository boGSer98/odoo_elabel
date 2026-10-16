from odoo import api, fields, models
from odoo.exceptions import UserError

class ElabelDocumentAdoption(models.TransientModel):
    _name='wine.elabel.adoption'
    _description='Bestandsdateien nach ausdrücklicher Prüfung zuordnen'
    product_id=fields.Many2one('product.template',required=True)
    attachment_ids=fields.Many2many('ir.attachment',string='Geprüfte vorhandene PDF-/SVG-Dateien',
        domain="[('res_model','=','product.template'),('res_id','=',product_id),('elabel_revision_id','=',False),('mimetype','in',['application/pdf','image/svg+xml'])]")
    lang_id=fields.Many2one('res.lang',required=True,default=lambda self:self.env['res.lang'].search([('code','=',self.env.lang)],limit=1))
    confirmed=fields.Boolean(string='Herkunft, Produktzuordnung und Fassung geprüft; private Ablage ausdrücklich bestätigt')

    def action_adopt(self):
        self.ensure_one();p=self.product_id;p._elabel_require_role(review=True,write=True);p._elabel_lock()
        if not self.confirmed or not self.attachment_ids:
            raise UserError(self.env._('Bitte Dateien auswählen und die Zuordnungsprüfung ausdrücklich bestätigen.'))
        revision=p.elabel_current_revision_id
        if not revision:raise UserError(self.env._('Zuerst eine Label-Fassung freigeben bzw. den migrierten Bestand prüfen.'))
        if self.lang_id.code not in revision.payload['translations']:
            raise UserError(self.env._('Diese Sprache gehört nicht zur Veröffentlichung.'))
        kinds=[]
        for a in self.attachment_ids:
            a.check_access('write')
            if a.res_model!='product.template' or a.res_id!=p.id:
                raise UserError(self.env._('Die Auswahl enthält fremde Produktdateien.'))
            if a.elabel_revision_id and a.elabel_revision_id.product_id!=p:
                raise UserError(self.env._('Die vorhandene Fassung gehört zu einem anderen Produkt.'))
            kind={'application/pdf':'pdf','image/svg+xml':'svg'}.get(a.mimetype)
            if not kind or kind in kinds:raise UserError(self.env._('Bitte höchstens eine PDF und eine SVG pro Sprache auswählen. Weitere Altdateien bleiben erhalten.'))
            kinds.append(kind)
        for a in self.attachment_ids:
            if a.elabel_revision_id:
                # Retrying a confirmed assignment must never rebind history or
                # clear an already verified source hash.
                p._elabel_after_attachment(a,a.elabel_revision_id)
                continue
            kind='pdf' if a.mimetype=='application/pdf' else 'svg'
            if self.env['ir.attachment'].sudo().search_count([('elabel_revision_id','=',revision.id),('elabel_document_kind','=',kind),('elabel_document_lang','=',self.lang_id.code)]):
                raise UserError(self.env._('Für diese Fassung, Sprache und Dateiart ist bereits eine Datei zugeordnet. Altduplikate bleiben unverändert; bitte historisch prüfen.'))
            vals={'res_model':'product.template','res_id':p.id,'elabel_revision_id':revision.id,
                  'elabel_document_kind':kind,'elabel_document_lang':self.lang_id.code,'elabel_source_hash':False}
            a=a.sudo().with_context(no_document=True)._elabel_store(vals)
            p._elabel_after_attachment(a,revision)
        return {'type':'ir.actions.act_window_close'}
