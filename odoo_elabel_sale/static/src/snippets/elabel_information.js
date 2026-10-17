import { Interaction } from "@web/public/interaction";
import { registry } from "@web/core/registry";
import { _t } from "@web/core/l10n/translation";

export class ElabelInformation extends Interaction {
    static selector = ".s_elabel_information, .s_elabel_information_inner";
    dynamicContent = { "_root": { "t-att-hidden": () => !this.editing && !this.html } };
    setup() {
        this.editing = false;
        this.html = "";
        this.sequence = 0;
    }
    async willStart() {
        await this.refresh();
    }
    start() {
        this.render();
        this.observer = new this.el.ownerDocument.defaultView.MutationObserver(() => this.refresh());
        this.observer.observe(this.el, { attributes: true, attributeFilter: ["data-elabel-product-id"] });
    }
    productId() {
        const value = this.el.dataset.elabelProductId || this.el.ownerDocument.querySelector(
            '#product_details input[name="product_template_id"], .js_main_product input[name="product_template_id"]'
        )?.value || "";
        return /^[1-9]\d*$/.test(value) ? value : "";
    }
    async refresh() {
        const sequence = ++this.sequence;
        const id = this.productId();
        let html = "";
        if (id) {
            const url = new URL(`/e-label/snippet/${id}`, this.el.ownerDocument.location.origin);
            url.searchParams.set("lang", this.el.ownerDocument.documentElement.lang || "");
            try {
                const response = await this.waitFor(fetch(url, { credentials: "same-origin", cache: "no-store" }));
                html = response.ok ? await this.waitFor(response.text()) : "";
            } catch {
                html = "";
            }
        }
        if (sequence !== this.sequence) return;
        this.html = html;
        if (this.isReady) this.render();
    }
    render() {
        const content = this.el.querySelector(".o_elabel_snippet_content");
        if (!content) return;
        // Use native protected interaction helpers, not authored DOM mutations.
        this.removeChildren(content, false);
        if (this.html) {
            const wrapper = this.el.ownerDocument.createElement("div");
            wrapper.innerHTML = this.html;
            for (const child of [...wrapper.children]) this.insert(child, content);
        } else if (this.editing) {
            const hint = this.el.ownerDocument.createElement("p");
            hint.className = "text-muted border rounded p-3 mb-0";
            hint.textContent = _t("Choose a product with a published e-label, or use the current product.");
            this.insert(hint, content);
        }
        this.updateContent();
    }

    destroy() {
        this.sequence++;
        this.observer?.disconnect();
        this.el.querySelector(".o_elabel_snippet_content")?.replaceChildren();
        this.el.hidden = false;
    }
}
registry.category("public.interactions").add("odoo_elabel_sale.information", ElabelInformation);
