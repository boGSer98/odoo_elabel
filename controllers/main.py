from odoo import http
from odoo.http import request


class WineElabelController(http.Controller):
    def _normalize_lang_code(self, code, available_codes):
        if not code:
            return None
        candidate = code.strip()
        test_values = [
            candidate,
            candidate.replace("-", "_"),
            candidate.replace("_", "-"),
            candidate.split("-")[0],
            candidate.split("_")[0],
        ]
        for test in test_values:
            if test in available_codes:
                return test
            lower_test = test.lower()
            for available in available_codes:
                if available.lower() == lower_test:
                    return available
        return None

    def _resolve_request_lang(self, requested_lang=None):
        lang_model = request.env["res.lang"].sudo()
        available_codes = lang_model.search([]).mapped("code")
        if not available_codes:
            return None

        normalized = self._normalize_lang_code(requested_lang, available_codes)
        if normalized:
            return normalized

        context_lang = self._normalize_lang_code(request.env.context.get("lang"), available_codes)
        if context_lang:
            return context_lang

        browser_langs = getattr(request.httprequest, "accept_languages", None)
        if browser_langs:
            accepted = []
            for lang, _quality in browser_langs:
                accepted.append(self._normalize_lang_code(lang, available_codes))
            for accepted_lang in accepted:
                if accepted_lang:
                    return accepted_lang

        user_lang = self._normalize_lang_code(request.env.user.lang, available_codes)
        if user_lang:
            return user_lang

        return self._normalize_lang_code("en_US", available_codes) or available_codes[0]

    @http.route(
        "/wine/e-label/<string:token>",
        type="http",
        auth="public",
        methods=["GET"],
        website=False,
        sitemap=False,
    )
    def wine_elabel(self, token, **kwargs):
        lang_code = self._resolve_request_lang(kwargs.get("lang"))
        if lang_code:
            request.update_context(lang=lang_code)

        product_model = request.env["product.template"].sudo()
        if lang_code:
            product_model = product_model.with_context(lang=lang_code)

        product_tmpl = product_model.search(
            [
                ("elabel_enabled", "=", True),
                ("elabel_token", "=", token),
            ],
            limit=1,
        )
        if not product_tmpl:
            return request.not_found()

        response = request.render(
            "odoo_elabel.wine_elabel_page",
            {"product_tmpl": product_tmpl},
        )
        response.headers["Cache-Control"] = "public, max-age=3600"
        if lang_code:
            response.headers["Content-Language"] = lang_code.replace("_", "-")
        return response
