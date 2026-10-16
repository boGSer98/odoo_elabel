from odoo import http
from odoo.http import request

class WineElabelController(http.Controller):
    def _normalize_lang_code(self,code,codes):
        if not isinstance(code,str):return None
        code=code.lower().replace('-','_')
        return next((x for x in codes if x.lower()==code),None) or next((x for x in codes if x.split('_')[0].lower()==code.split('_')[0]),None)

    def _resolve_request_lang(self,codes,requested=None):
        candidates=[requested]
        candidates += [lang for lang,quality in request.httprequest.accept_languages if quality>0]
        candidates += [request.env.context.get('lang')]
        return next((v for x in candidates if (v:=self._normalize_lang_code(x,codes))),codes[0])

    @http.route('/wine/e-label/<string:token>',type='http',auth='public',methods=['GET'],website=False,sitemap=False,save_session=False)
    def wine_elabel(self,token,**kwargs):
        headers={
            'Cache-Control':'no-store, max-age=0','Pragma':'no-cache',
            'X-Robots-Tag':'noindex, nofollow, noarchive','Referrer-Policy':'no-referrer',
            'X-Content-Type-Options':'nosniff','X-Frame-Options':'DENY',
            'Content-Security-Policy':"default-src 'none'; style-src 'unsafe-inline'; img-src 'self' data:; base-uri 'none'; form-action 'none'; frame-ancestors 'none'",
        }
        if len(token)>200:return request.make_response('Nicht gefunden',headers=headers,status=404)
        products=request.env['product.template'].sudo().with_context(active_test=False).search([
            ('elabel_enabled','=',True),('elabel_token','=',token)],limit=2)
        if len(products)!=1 or not products.elabel_current_revision_id:
            return request.make_response('Nicht gefunden',headers=headers,status=404)
        revision=products.elabel_current_revision_id
        codes=list(revision.payload['translations'])
        lang=self._resolve_request_lang(codes,kwargs.get('lang'))
        request.update_context(lang=lang)
        languages=request.env['res.lang'].sudo().with_context(active_test=False).search([('code','in',codes)])
        content=request.env['ir.qweb'].sudo()._render('odoo_elabel.wine_elabel_page',{
            'product_tmpl':revision._presentation(lang),'lang_code':lang,
            'elabel_languages':[(l.code,l.name) for l in languages]})
        headers.update({'Content-Type':'text/html; charset=utf-8','Content-Language':lang.replace('_','-')})
        return request.make_response(content,headers=headers)
