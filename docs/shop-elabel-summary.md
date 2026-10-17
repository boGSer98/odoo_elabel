# e-Label information on the product page

The optional `odoo_elabel_sale` bridge keeps the existing e-Label button and adds a small bordered information panel directly after the native purchase CTA and before purchase terms. It displays ingredients, the configured allergen statement, optional additional substances/nutrition note and all seven nutrient rows per 100 ml.

There is no second data-entry area. Only the active immutable publication is displayed, using the same `LabelPresentation` formatter and published-language fallback as the dedicated e-Label page. Unapproved edits never appear in the shop until republished. Disabling the public label hides the box; products without a published label get no empty box.

The read-only label projection checks explicit label activation/release and website/company scope before reading the protected revision. As explicitly requested, it remains available independently of stock, sale eligibility, publication and archive state. Only released display data is read with narrowly scoped elevation; no product record or product-page access is granted. It returns only display strings and nutrient lines, not revision records, private source data or a raw payload. Text is QWeb-escaped. Shared products keep native shared website semantics.

The standalone e-Label route, publication workflow, generated PDF/SVG files, tax/pricing/stock logic and purchased addons remain unchanged. Existing documents do not need regeneration for this display-only change. Website language selects an available released translation; otherwise the existing released-language fallback applies, without inventing translations.

Validate the native inherited view, public shop rendering at desktop/mobile sizes, released-vs-draft and disabled behavior, language fallback, zero nutrition values, escaping and cross-site/company denial on a neutralized clone. This is technical rendering, not legal certification of supplied content.
