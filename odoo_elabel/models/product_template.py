import base64
import math
import uuid
from urllib.parse import quote

from odoo import api, fields, models
from odoo.exceptions import AccessError, UserError, ValidationError
from .presentation import CONTENT_FIELDS, TEXT_FIELDS, NUMBER_FIELDS, digest
from .revision import WineElabelRevision

PROTECTED = {'elabel_token', 'elabel_enabled', 'elabel_state', 'elabel_current_revision_id'}

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    elabel_enabled = fields.Boolean(string='Öffentlich erreichbar', copy=False, readonly=True)
    elabel_token = fields.Char(string='Dauerhafter e-Label-Token', copy=False, readonly=True, index=True)
    elabel_public_url = fields.Char(string='Öffentliche e-Label-URL', compute='_compute_elabel_urls')
    elabel_qr_code_url = fields.Char(string='QR-Code-URL', compute='_compute_elabel_urls')
    elabel_state = fields.Selection([('draft','Entwurf'), ('review','Zur Prüfung'), ('published','Freigegeben')],
                                   default='draft', required=True, copy=False, readonly=True)
    elabel_current_revision_id = fields.Many2one('wine.elabel.revision', string='Freigegebene Fassung', copy=False, readonly=True, ondelete='restrict')
    elabel_revision_ids = fields.One2many('wine.elabel.revision','product_id', string='Veröffentlichungen', readonly=True)
    elabel_ingredients = fields.Text(string='Zutatenliste', translate=True)
    elabel_additional_substances = fields.Text(string='Weitere Inhaltsstoffe', translate=True)
    elabel_allergen_statement = fields.Char(string='Allergenhinweis', translate=True)
    elabel_nutrition_note = fields.Char(string='Ergänzender Nährwerthinweis', translate=True)
    elabel_energy_kj = fields.Float(string='Energie (kJ/100 ml)', digits=(16,2))
    elabel_energy_kcal = fields.Float(string='Energie (kcal/100 ml)', digits=(16,2))
    elabel_fat = fields.Float(string='Fett (g/100 ml)', digits=(16,2))
    elabel_saturates = fields.Float(string='Gesättigte Fettsäuren (g/100 ml)', digits=(16,2))
    elabel_carbohydrate = fields.Float(string='Kohlenhydrate (g/100 ml)', digits=(16,2))
    elabel_sugars = fields.Float(string='Zucker (g/100 ml)', digits=(16,2))
    elabel_protein = fields.Float(string='Eiweiß (g/100 ml)', digits=(16,2))
    elabel_salt = fields.Float(string='Salz (g/100 ml)', digits=(16,2))
    elabel_nutrition_confirmed = fields.Boolean(string='Nährwerte einschließlich Nullwerten fachlich bestätigt')
    elabel_allergens_confirmed = fields.Boolean(string='Allergenstatus und physisches Etikett geprüft')
    elabel_source = fields.Text(string='Datengrundlage / Messquelle')
    elabel_checked_on = fields.Date(string='Fachlich geprüft am')
    elabel_translation_checked = fields.Boolean(string='Ausgewählte Sprachfassungen geprüft')
    elabel_language_ids = fields.Many2many('res.lang', 'product_elabel_lang_rel','product_id','lang_id',
        string='Freizugebende Sprachen', default=lambda self:self.env['res.lang'].search([('code','=',self.env.lang)],limit=1))
    elabel_pending_changes = fields.Boolean(string='Unveröffentlichte Änderungen / Dokumentprüfung erforderlich', compute='_compute_elabel_document_state')
    elabel_documents_stale = fields.Boolean(string='Dokumente fehlen oder sind veraltet', compute='_compute_elabel_document_state')
    _token_unique = models.Constraint('UNIQUE(elabel_token)', 'Der e-Label-Token ist einschließlich archivierter Produkte bereits vergeben.')

    def _elabel_require_role(self, review=False, write=False):
        if not (self.env.is_admin() or self.env.user.has_group('odoo_elabel.group_elabel_reviewer' if review else 'odoo_elabel.group_elabel_editor')):
            raise AccessError(self.env._('Diese Aktion benötigt die entsprechende e-Label-Berechtigung.'))
        self.check_access('write' if write else 'read')

    def _elabel_content_fields(self):
        """Extension hook; no additional fields in databases without opt-in addons."""
        return CONTENT_FIELDS

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if (any(vals.get(k) for k in PROTECTED - {'elabel_state'}) or vals.get('elabel_state', 'draft') != 'draft'):
                raise AccessError(self.env._('Tokens und Veröffentlichung werden ausschließlich durch die Freigabe verwaltet.'))
            self._elabel_check_input(vals)
            if any(vals.get(k) for k in self._elabel_content_fields()):
                self._elabel_require_role()
        return super().create(vals_list)

    def write(self, vals):
        self._elabel_check_input(vals)
        if PROTECTED.intersection(vals):
            raise AccessError(self.env._('Verwenden Sie die e-Label-Freigabe bzw. Deaktivierung. Gedruckte Tokens sind unveränderlich.'))
        if any(k.startswith('elabel_') for k in vals):
            self._elabel_require_role(write=True)
        if 'company_id' in vals and any(p.elabel_token and p.company_id.id != vals['company_id'] for p in self):
            raise UserError(self.env._('Das Unternehmen eines veröffentlichten Labels darf nicht gewechselt werden.'))
        result = super().write(vals)
        changes = set(self._elabel_content_fields()) | {'name','elabel_source','elabel_checked_on','elabel_nutrition_confirmed',
                   'elabel_allergens_confirmed','elabel_language_ids','elabel_translation_checked'}
        if changes.intersection(vals):
            for p in self.filtered(lambda r:r.elabel_state != 'draft'):
                super(ProductTemplate,p).write({'elabel_state':'draft'})
        return result

    def unlink(self):
        if any(self.mapped('elabel_token')):
            raise UserError(self.env._('Produkte mit dauerhaftem e-Label-Link dürfen nur archiviert werden.'))
        return super().unlink()

    def _elabel_check_input(self, vals):
        for name in NUMBER_FIELDS:
            if name not in vals:
                continue
            try:
                valid=math.isfinite(float(vals[name] or 0)) and float(vals[name] or 0)>=0
            except (ValueError, TypeError, OverflowError):
                valid=False
            if not valid:
                raise ValidationError(self.env._("Nährwerte müssen endliche, nicht negative Zahlen sein."))

    elabel_nutrition_warning = fields.Text(string='Nährwerthinweise', compute='_compute_elabel_nutrition_warning')

    @api.depends(*NUMBER_FIELDS)
    def _compute_elabel_nutrition_warning(self):
        for p in self:
            warnings=[]
            if p.elabel_sugars > p.elabel_carbohydrate + 0.005:
                warnings.append(self.env._('Zucker liegt über den angegebenen Kohlenhydraten.'))
            if p.elabel_saturates > p.elabel_fat + 0.005:
                warnings.append(self.env._('Gesättigte Fettsäuren liegen über dem angegebenen Gesamtfett.'))
            if p.elabel_energy_kj <= 0 or p.elabel_energy_kcal <= 0:
                warnings.append(self.env._('Eine Energieangabe ist null. Bitte die Angaben bei Bedarf kontrollieren.'))
            else:
                expected=p.elabel_energy_kcal * 4.184
                if abs(p.elabel_energy_kj-expected) > max(5.0,expected*0.1):
                    warnings.append(self.env._('Die kJ-/kcal-Angaben passen rechnerisch nicht zusammen.'))
            p.elabel_nutrition_warning='\n'.join(warnings) if warnings else False

    @api.constrains(*NUMBER_FIELDS)
    def _check_elabel_nutrition_values(self):
        for p in self:
            if any(not math.isfinite(p[f]) or p[f] < 0 for f in NUMBER_FIELDS):
                raise ValidationError(self.env._('Nährwerte müssen endliche, nicht negative Zahlen sein.'))

    def _elabel_payload(self):
        self.ensure_one()
        langs = self.elabel_language_ids.mapped('code') or [self.env.lang or 'en_US']
        translations = {}
        for lang in sorted(langs):
            p = self.with_context(lang=lang)
            translations[lang] = {'name':p.name, **{f:p[f] or '' for f in TEXT_FIELDS}}
        return {'translations':translations,'numbers':{f:self[f] for f in NUMBER_FIELDS}}

    def _elabel_validate_publication(self):
        self.ensure_one()
        self._check_elabel_nutrition_values()
        if not (self.elabel_nutrition_confirmed and self.elabel_allergens_confirmed and
                (self.elabel_source or '').strip() and self.elabel_checked_on and self.elabel_language_ids):
            raise UserError(self.env._('Bitte Nährwerte und Allergenstatus bestätigen sowie Messquelle, Prüfdatum und Sprachen angeben.'))
        if self.elabel_checked_on > fields.Date.context_today(self):
            raise UserError(self.env._('Das Prüfdatum darf nicht in der Zukunft liegen.'))
        if any(not (v['elabel_ingredients'] or '').strip() for v in self._elabel_payload()['translations'].values()):
            raise UserError(self.env._('Jede freizugebende Sprachfassung benötigt eine Zutatenliste.'))
        self.company_id._elabel_validate_base_url(self._get_elabel_base_url())

    def _elabel_lock(self):
        self.ensure_one()
        self.env.cr.execute('SELECT id FROM product_template WHERE id=%s FOR UPDATE',[self.id])
        self.invalidate_recordset()

    def action_submit_elabel(self):
        self.ensure_one();self._elabel_require_role(write=True);self._elabel_validate_publication()
        super(ProductTemplate,self).write({'elabel_state':'review'})
        return True

    def _elabel_make_revision(self, legacy=False):
        payload=self._elabel_payload()
        Revision=self.env['wine.elabel.revision'].sudo()
        number=Revision.search_count([('product_id','=',self.id)])+1
        revision=super(WineElabelRevision,Revision).create({
            'product_id':self.id,'number':number,'name':'%s – Fassung %s' % (self.name,number),
            'payload':payload,'content_hash':digest(payload),'source':self.elabel_source,
            'checked_on':self.elabel_checked_on,'legacy':legacy})
        return revision

    def action_publish_elabel(self):
        self.ensure_one();self._elabel_require_role(review=True,write=True);self._elabel_lock()
        if self.elabel_state != 'review':
            raise UserError(self.env._('Das Label muss zuerst zur Prüfung eingereicht werden.'))
        self._elabel_validate_publication()
        revision=self._elabel_make_revision()
        super(ProductTemplate,self).write({'elabel_token':self.elabel_token or str(uuid.uuid4()),
            'elabel_current_revision_id':revision.id,'elabel_enabled':True,'elabel_state':'published'})
        self.message_post(body=self.env._('e-Label-Fassung %s freigegeben.',revision.number))
        return True

    def _get_elabel_base_url(self):
        # Shared products use the global canonical base, never the viewer company.
        company=self.company_id
        return (company.elabel_base_url or self.env['ir.config_parameter'].sudo().get_param('web.base.url','')).rstrip('/')

    def _get_elabel_public_route(self):
        self.ensure_one();return '/wine/e-label/%s' % (self.elabel_token or '')

    def _get_elabel_public_url(self):
        return self._get_elabel_base_url()+self._get_elabel_public_route()

    @api.depends('elabel_token','elabel_enabled','company_id')
    def _compute_elabel_urls(self):
        for p in self:
            p.elabel_public_url=p._get_elabel_public_url() if p.elabel_token else False
            p.elabel_qr_code_url=('/report/barcode/?barcode_type=QR&value=%s&width=240&height=240' %
                quote(p.elabel_public_url,safe='')) if p.elabel_public_url else False

    def action_view_elabel_url(self):
        self.ensure_one();self.check_access('read')
        if not self.elabel_token:raise UserError(self.env._('Noch keine freigegebene Veröffentlichung vorhanden.'))
        return {'type':'ir.actions.act_url','url':self.elabel_public_url,'target':'new'}

    def action_view_elabel_qr_code(self):
        result=self.action_view_elabel_url();result['url']=self.elabel_qr_code_url;return result

    def action_disable_elabel(self):
        self.ensure_one();self._elabel_require_role(review=True,write=True);self._elabel_lock()
        super(ProductTemplate,self).write({'elabel_enabled':False})
        self.message_post(body=self.env._('Öffentliche e-Label-Ausgabe deaktiviert; Token bleibt reserviert.'))
        return True

    def _elabel_document_record(self):
        self.ensure_one()
        rev=self.elabel_current_revision_id
        if not rev:raise UserError(self.env._('Bitte zuerst eine geprüfte Label-Fassung veröffentlichen.'))
        return rev._presentation(self.env.context.get('lang'))

    def _get_elabel_render_lang(self):
        self.ensure_one()
        codes=list(self.elabel_current_revision_id.payload['translations'])
        return self.env.context.get('lang') if self.env.context.get('lang') in codes else codes[0]

    def _generate_elabel_qr_svg(self,value):
        from reportlab.graphics import renderSVG
        from reportlab.graphics.barcode.qr import QrCodeWidget
        from reportlab.graphics.shapes import Drawing
        widget=QrCodeWidget(value);x1,y1,x2,y2=widget.getBounds();drawing=Drawing(x2-x1,y2-y1);drawing.add(widget)
        value=renderSVG.drawToString(drawing)
        return value.encode() if isinstance(value,str) else value

    def _generate_elabel_pdf(self):
        data,_=self.env['ir.actions.report'].with_context(lang=self._get_elabel_render_lang())._render_qweb_pdf(
            'odoo_elabel.action_report_wine_elabel_pdf',res_ids=self.ids)
        return data

    def _elabel_after_attachment(self,attachment,revision):
        return None

    def _create_or_update_elabel_documents(self):
        self.ensure_one();self._elabel_require_role(write=True);self._elabel_lock()
        revision=self.elabel_current_revision_id
        if not revision:raise UserError(self.env._('Bitte zuerst eine Fassung freigeben.'))
        if revision.legacy:
            raise UserError(self.env._('Bestandsfassungen müssen vor neuer Dokumenterzeugung fachlich freigegeben werden. Vorhandene Dateien können nach Prüfung übernommen werden.'))
        lang=self._get_elabel_render_lang()
        for kind,blob,mime in [('svg',self._generate_elabel_qr_svg(self.elabel_public_url),'image/svg+xml'),
                               ('pdf',self._generate_elabel_pdf(),'application/pdf')]:
            Attachment=self.env['ir.attachment'].sudo().with_context(no_document=True)
            domain=[('elabel_revision_id','=',revision.id),('elabel_document_kind','=',kind),('elabel_document_lang','=',lang)]
            attachment=Attachment.search(domain,limit=1)
            vals={'name':'e-label_%s_v%s_%s.%s' % (self.id,revision.number,lang,kind),'datas':base64.b64encode(blob),
                  'type':'binary','mimetype':mime,'res_model':'product.template','res_id':self.id,
                  'company_id':self.company_id.id,'public':False,'access_token':False,
                  'elabel_revision_id':revision.id,'elabel_document_kind':kind,
                  'elabel_document_lang':lang,'elabel_source_hash':digest({'content':revision.content_hash,'url':self.elabel_public_url,'lang':lang})}
            attachment=attachment._elabel_store(vals)
            self._elabel_after_attachment(attachment,revision)
        return True

    def action_generate_elabel_documents(self):
        self._create_or_update_elabel_documents()
        return {'type':'ir.actions.client','tag':'display_notification','params':{'title':'E-Label',
            'message':'PDF und QR-SVG der freigegebenen Fassung gespeichert.','type':'success'}}

    def action_open_elabel(self):
        return self.action_generate_elabel_documents()

    @api.depends(*CONTENT_FIELDS,'name','elabel_current_revision_id','elabel_language_ids')
    def _compute_elabel_document_state(self):
        for p in self:
            r=p.elabel_current_revision_id
            p.elabel_pending_changes=bool(r and digest(p._elabel_payload())!=r.content_hash)
            if not r:p.elabel_documents_stale=True;continue
            docs=self.env['ir.attachment'].sudo().search([('elabel_revision_id','=',r.id)])
            p.elabel_documents_stale=bool(p.elabel_pending_changes or not {'pdf','svg'}.issubset(set(docs.mapped('elabel_document_kind'))) or any(a.elabel_source_hash!=digest({'content':r.content_hash,'url':p.elabel_public_url,'lang':a.elabel_document_lang}) for a in docs))
