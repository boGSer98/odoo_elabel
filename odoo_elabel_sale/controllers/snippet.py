from odoo import http
from odoo.http import request
from odoo.exceptions import AccessError


class ElabelSnippet(http.Controller):
    def _summary(self, product_id, lang=None):
        if isinstance(product_id, bool) or not isinstance(product_id, int) or not 0 < product_id < 2147483648:
            return False, request.env.lang
        website = request.website
        languages = website.language_ids.mapped('code')
        normalized = (lang or '').lower().replace('-', '_') if isinstance(lang, str) else ''
        code = next((c for c in languages if c.lower() == normalized), None)
        code = code or next((c for c in languages if c.split('_')[0].lower() == normalized.split('_')[0]), request.env.lang)
        domain = [('id', '=', product_id), ('is_published', '=', True), ('sale_ok', '=', True),
                  ('elabel_enabled', '=', True), ('website_id', 'in', [False, website.id]),
                  ('company_id', 'in', [False, website.company_id.id])]
        try:
            product = request.env['product.template'].with_context(lang=code).search(domain, limit=1)
            return (product._get_website_elabel_summary(website) if product else False), code
        except AccessError:
            return False, code

    @http.route('/e-label/snippet/<int:product_id>', type='http', auth='public', website=True,
                sitemap=False, methods=['GET'], save_session=False, readonly=True)
    def contents(self, product_id, lang=None, **kwargs):
        # Shared addon code can also be loaded by an older, non-upgraded DB.
        available = request.env.ref('odoo_elabel_sale.website_sale_elabel_summary', raise_if_not_found=False)
        summary, code = self._summary(product_id, lang) if available else (False, request.env.lang)
        content = request.env['ir.qweb'].with_context(lang=code, inherit_branding=False, edit_translations=False)._render(
            'odoo_elabel_sale.website_sale_elabel_summary', {'elabel_summary': summary}) if summary else ''
        return request.make_response(content, headers=[
            ('Content-Type', 'text/html; charset=utf-8'), ('Cache-Control', 'no-store, max-age=0'),
            ('X-Robots-Tag', 'noindex, nofollow'), ('X-Content-Type-Options', 'nosniff')])
