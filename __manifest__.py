{
    "name": "Wine e-Label",
    "summary": "EU wine e-label page with ingredients and nutrition declaration",
    "description": """
Wine e-Label for Odoo 19 CE.

Features:
- Product-level e-label data fields
- Public e-label page with token URL
- Nutrition declaration and ingredients
- QR code (SVG) and PDF generation as product documents
- Multilingual output based on user/browser language
""",
    "version": "saas~19.4.1.3.4",
    "category": "Inventory/Product",
    "author": "Custom",
    "license": "AGPL-3",
    "depends": ["product", "website", "website_sale"],
    "data": [
        "views/elabel_menu.xml",
        "views/product_template_views.xml",
        "views/elabel_templates.xml",
        "views/elabel_report.xml",
        "views/website_sale_templates.xml",
    ],
    "installable": True,
    "application": True,
}
