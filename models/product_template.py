import uuid
import base64
import re
from urllib.parse import quote

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class ProductTemplate(models.Model):
    _inherit = "product.template"
    _product_elabel_token_uniq = models.Constraint(
        "unique(elabel_token)",
        "The e-label token must be unique.",
    )

    elabel_enabled = fields.Boolean(
        string="Wine e-Label",
        help="Enable a public electronic label page for this wine product.",
    )
    elabel_token = fields.Char(
        string="e-Label Token",
        copy=False,
        readonly=True,
        index=True,
        default=lambda self: str(uuid.uuid4()),
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
            if not vals.get("elabel_token"):
                vals["elabel_token"] = str(uuid.uuid4())
        return super().create(vals_list)

    def write(self, vals):
        res = super().write(vals)
        for record in self.filtered(lambda p: p.elabel_enabled and not p.elabel_token):
            record.elabel_token = str(uuid.uuid4())
        return res

    @api.depends("elabel_enabled", "elabel_token")
    def _compute_elabel_urls(self):
        base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url", "").rstrip("/")
        for record in self:
            if not (record.elabel_enabled and record.elabel_token):
                record.elabel_public_url = False
                record.elabel_qr_code_url = False
                continue

            route = f"/wine/e-label/{record.elabel_token}"
            public_url = f"{base_url}{route}" if base_url else route
            record.elabel_public_url = public_url
            encoded_url = quote(public_url, safe="")
            record.elabel_qr_code_url = (
                f"/report/barcode/?barcode_type=QR&value={encoded_url}&width=240&height=240"
            )

    def action_open_elabel(self):
        self.ensure_one()
        if not self.elabel_enabled:
            raise UserError(_("Please enable Wine e-Label before generating the public page."))
        if not self.elabel_token:
            self.elabel_token = str(uuid.uuid4())
        self._compute_elabel_urls()
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
        self.ensure_one()
        if not self.elabel_enabled:
            raise UserError(_("Please enable Wine e-Label before opening the public page."))
        if not self.elabel_token:
            self.elabel_token = str(uuid.uuid4())
        self._compute_elabel_urls()
        return {
            "type": "ir.actions.act_url",
            "name": _("Public e-Label"),
            "url": self.elabel_public_url,
            "target": "new",
        }

    def action_view_elabel_qr_code(self):
        self.ensure_one()
        if not self.elabel_enabled:
            raise UserError(_("Please enable Wine e-Label before opening the QR code."))
        if not self.elabel_token:
            self.elabel_token = str(uuid.uuid4())
        self._compute_elabel_urls()
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
        pdf_bytes, _content_type = self.env["ir.actions.report"].sudo()._render_qweb_pdf(
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
        self.ensure_one()
        if not self.elabel_enabled:
            raise UserError(_("Please enable Wine e-Label before generating documents."))

        if not self.elabel_token:
            self.elabel_token = str(uuid.uuid4())
        self._compute_elabel_urls()
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
