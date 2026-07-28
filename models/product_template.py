import uuid
import base64
import re
from urllib.parse import quote

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class ProductTemplate(models.Model):
    _inherit = "product.template"

    elabel_enabled = fields.Boolean(
        string="Wine e-Label",
        help="Enable a public electronic label page for this wine product.",
    )
    elabel_token = fields.Char(
        string="e-Label Token",
        copy=False,
        readonly=True,
        index=True,
    )
    elabel_public_url = fields.Char(
        string="Public e-Label URL",
        compute="_compute_elabel_urls",
        readonly=True,
    )
    elabel_qr_code_url = fields.Char(
        string="QR Code URL",
        compute="_compute_elabel_urls",
        readonly=True,
    )

    elabel_ingredients = fields.Text(
        string="Ingredients List",
        translate=True,
        help="Ingredients shown on the electronic label.",
    )
    elabel_additional_substances = fields.Text(
        string="Additional Substances",
        translate=True,
        help="Additional substances or composition information shown after allergens.",
    )
    elabel_allergen_statement = fields.Char(
        string="Allergen Statement (for physical label)",
        default=lambda self: _("Contains sulphites"),
        translate=True,
        help=(
            "Allergens must remain on the physical label. "
            "Keep this field aligned with your printed bottle label."
        ),
    )

    elabel_energy_kj = fields.Float(string="Energy (kJ/100 ml)", digits=(16, 2))
    elabel_energy_kcal = fields.Float(string="Energy (kcal/100 ml)", digits=(16, 2))
    elabel_fat = fields.Float(string="Fat (g/100 ml)", digits=(16, 2))
    elabel_saturates = fields.Float(string="of which saturates (g/100 ml)", digits=(16, 2))
    elabel_carbohydrate = fields.Float(string="Carbohydrate (g/100 ml)", digits=(16, 2))
    elabel_sugars = fields.Float(string="of which sugars (g/100 ml)", digits=(16, 2))
    elabel_protein = fields.Float(string="Protein (g/100 ml)", digits=(16, 2))
    elabel_salt = fields.Float(string="Salt (g/100 ml)", digits=(16, 2))
    elabel_nutrition_note = fields.Char(
        string="Optional Nutrition Note",
        translate=True,
        help='Example: "Contains negligible amounts of fat, saturates, protein and salt."',
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("elabel_enabled") and not vals.get("elabel_token"):
                vals["elabel_token"] = str(uuid.uuid4())
        return super().create(vals_list)

    def write(self, vals):
        res = super().write(vals)
        for record in self.filtered(lambda p: p.elabel_enabled):
            record._ensure_unique_elabel_token()
        return res

    @api.constrains("elabel_token")
    def _check_elabel_token_unique(self):
        for record in self.filtered("elabel_token"):
            domain = [
                ("id", "!=", record.id),
                ("elabel_token", "=", record.elabel_token),
            ]
            if self.search_count(domain, limit=1):
                raise ValidationError(_("The e-label token must be unique."))

    @api.constrains(
        "elabel_energy_kj",
        "elabel_energy_kcal",
        "elabel_fat",
        "elabel_saturates",
        "elabel_carbohydrate",
        "elabel_sugars",
        "elabel_protein",
        "elabel_salt",
    )
    def _check_elabel_nutrition_values(self):
        nutrition_fields = self._get_elabel_nutrition_field_labels()
        for record in self:
            invalid_labels = [
                label for field_name, label in nutrition_fields if record[field_name] < 0
            ]
            if invalid_labels:
                raise ValidationError(
                    _("Nutrition values cannot be negative: %s")
                    % ", ".join(invalid_labels)
                )

    def _get_elabel_nutrition_field_labels(self):
        return [
            ("elabel_energy_kj", _("Energy (kJ)")),
            ("elabel_energy_kcal", _("Energy (kcal)")),
            ("elabel_fat", _("Fat")),
            ("elabel_saturates", _("of which saturates")),
            ("elabel_carbohydrate", _("Carbohydrate")),
            ("elabel_sugars", _("of which sugars")),
            ("elabel_protein", _("Protein")),
            ("elabel_salt", _("Salt")),
        ]

    def _format_elabel_float(self, value):
        return "%.2f" % (value or 0.0)

    def _get_elabel_display_labels(self):
        return {
            "title": _("Wine e-Label"),
            "nutrition_declaration": _("Nutrition declaration"),
            "information_per_100_ml": _("Information per 100 ml"),
            "ingredients": _("Ingredients"),
            "allergens": _("Allergens"),
            "additional_substances": _("Additional substances"),
            "mandatory_information_only": _(
                "This page contains mandatory e-label information only."
            ),
        }

    def _get_elabel_nutrition_lines(self):
        self.ensure_one()
        return [
            {
                "label": _("Energy"),
                "value": _("%(kj)s kJ / %(kcal)s kcal")
                % {
                    "kj": self._format_elabel_float(self.elabel_energy_kj),
                    "kcal": self._format_elabel_float(self.elabel_energy_kcal),
                },
            },
            {
                "label": _("Fat"),
                "value": _("%s g") % self._format_elabel_float(self.elabel_fat),
            },
            {
                "label": _("of which saturates"),
                "value": _("%s g") % self._format_elabel_float(self.elabel_saturates),
            },
            {
                "label": _("Carbohydrate"),
                "value": _("%s g") % self._format_elabel_float(self.elabel_carbohydrate),
            },
            {
                "label": _("of which sugars"),
                "value": _("%s g") % self._format_elabel_float(self.elabel_sugars),
            },
            {
                "label": _("Protein"),
                "value": _("%s g") % self._format_elabel_float(self.elabel_protein),
            },
            {
                "label": _("Salt"),
                "value": _("%s g") % self._format_elabel_float(self.elabel_salt),
            },
        ]

    def _ensure_elabel_ready(self, action_message):
        self.ensure_one()
        if not self.elabel_enabled:
            raise UserError(action_message)
        self._ensure_unique_elabel_token()
        self._compute_elabel_urls()

    def _ensure_unique_elabel_token(self):
        self.ensure_one()
        if self.elabel_token:
            duplicate = self.search(
                [
                    ("id", "!=", self.id),
                    ("elabel_token", "=", self.elabel_token),
                ],
                limit=1,
            )
            if not duplicate:
                return
        self.elabel_token = str(uuid.uuid4())

    def _get_elabel_public_route(self):
        self.ensure_one()
        return f"/wine/e-label/{self.elabel_token}"

    def _get_elabel_public_url(self):
        self.ensure_one()
        base_url = self.env["ir.config_parameter"].sudo().get_str("web.base.url", "").rstrip("/")
        route = self._get_elabel_public_route()
        return f"{base_url}{route}" if base_url else route

    def _get_elabel_qr_code_url(self):
        self.ensure_one()
        encoded_url = quote(self.elabel_public_url, safe="")
        return f"/report/barcode/?barcode_type=QR&value={encoded_url}&width=240&height=240"

    def _get_elabel_render_lang(self):
        self.ensure_one()
        available_codes = set(self.env["res.lang"].sudo().search([]).mapped("code"))
        for lang_code in (self.env.context.get("lang"), self.env.user.lang, "de_DE", "de"):
            if lang_code in available_codes:
                return lang_code
        return self.env.context.get("lang")

    @api.depends("elabel_enabled", "elabel_token")
    def _compute_elabel_urls(self):
        for record in self:
            if not (record.elabel_enabled and record.elabel_token):
                record.elabel_public_url = False
                record.elabel_qr_code_url = False
                continue

            record.elabel_public_url = record._get_elabel_public_url()
            record.elabel_qr_code_url = record._get_elabel_qr_code_url()

    def action_open_elabel(self):
        self._ensure_elabel_ready(
            _("Please enable Wine e-Label before generating the public page.")
        )
        self._create_or_update_elabel_documents()
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("e-Label generated"),
                "message": _("The e-Label documents have been generated for this product."),
                "type": "success",
                "sticky": False,
            },
        }

    def action_view_elabel_url(self):
        self._ensure_elabel_ready(
            _("Please enable Wine e-Label before opening the public page.")
        )
        return {
            "type": "ir.actions.act_url",
            "name": _("Public e-Label"),
            "url": self.elabel_public_url,
            "target": "new",
        }

    def action_view_elabel_qr_code(self):
        self._ensure_elabel_ready(
            _("Please enable Wine e-Label before opening the QR code.")
        )
        return {
            "type": "ir.actions.act_url",
            "name": _("QR Code URL"),
            "url": self.elabel_qr_code_url,
            "target": "new",
        }

    def _get_elabel_document_basename(self):
        self.ensure_one()
        name_source = self.default_code or self.name or f"product_{self.id}"
        normalized = re.sub(r"[^A-Za-z0-9._-]+", "_", name_source).strip("_")
        if not normalized:
            normalized = f"product_{self.id}"
        return f"wine_elabel_{normalized}"

    def _generate_elabel_qr_svg(self, value):
        self.ensure_one()
        try:
            from reportlab.graphics import renderSVG
            from reportlab.graphics.barcode.qr import QrCodeWidget
            from reportlab.graphics.shapes import Drawing
        except ImportError as exc:
            raise UserError(_("QR code generation is unavailable: %s", exc))

        qr_widget = QrCodeWidget(value)
        x1, y1, x2, y2 = qr_widget.getBounds()
        drawing = Drawing(x2 - x1, y2 - y1)
        drawing.add(qr_widget)
        svg_content = renderSVG.drawToString(drawing)
        if isinstance(svg_content, str):
            return svg_content.encode("utf-8")
        return svg_content

    def _generate_elabel_pdf(self):
        self.ensure_one()
        lang_code = self._get_elabel_render_lang()
        pdf_bytes, _content_type = self.env["ir.actions.report"].sudo().with_context(
            lang=lang_code
        )._render_qweb_pdf(
            "odoo_elabel.action_report_wine_elabel_pdf",
            res_ids=self.ids,
        )
        return pdf_bytes

    def _upsert_elabel_attachment(self, filename, file_bytes, mimetype):
        self.ensure_one()
        Attachment = self.env["ir.attachment"].sudo()
        attachment = Attachment.search(
            [
                ("res_model", "=", "product.template"),
                ("res_id", "=", self.id),
                ("name", "=", filename),
                ("type", "=", "binary"),
            ],
            limit=1,
        )
        vals = {
            "name": filename,
            "type": "binary",
            "datas": base64.b64encode(file_bytes),
            "mimetype": mimetype,
            "res_model": "product.template",
            "res_id": self.id,
        }
        if attachment:
            attachment.write(vals)
            return attachment
        return Attachment.create(vals)

    def _create_or_update_elabel_documents(self):
        self.ensure_one()
        basename = self._get_elabel_document_basename()
        svg_content = self._generate_elabel_qr_svg(self.elabel_public_url)
        pdf_content = self._generate_elabel_pdf()

        self._upsert_elabel_attachment(f"{basename}.svg", svg_content, "image/svg+xml")
        self._upsert_elabel_attachment(f"{basename}.pdf", pdf_content, "application/pdf")

    def action_generate_elabel_documents(self):
        self._ensure_elabel_ready(
            _("Please enable Wine e-Label before generating documents.")
        )
        self._create_or_update_elabel_documents()

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("e-Label documents regenerated"),
                "message": _("The QR SVG and PDF have been updated for this product."),
                "type": "success",
                "sticky": False,
            },
        }

    def action_disable_elabel(self):
        self.ensure_one()
        self.write({"elabel_enabled": False})
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("e-Label deactivated"),
                "message": _("The e-Label has been disabled for this product."),
                "type": "warning",
                "sticky": False,
                "next": {
                    "type": "ir.actions.client",
                    "tag": "reload",
                },
            },
        }
