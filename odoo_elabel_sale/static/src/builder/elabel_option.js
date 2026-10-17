import { BaseOptionComponent } from "@html_builder/core/utils";
import { BuilderAction } from "@html_builder/core/builder_action";
import { Plugin } from "@html_editor/plugin";
import { withSequence } from "@html_editor/utils/resource";
import { SNIPPET_SPECIFIC_END } from "@html_builder/utils/option_sequence";
import { registry } from "@web/core/registry";
import { onWillStart } from "@odoo/owl";

export class ElabelOption extends BaseOptionComponent {
    static template = "odoo_elabel_sale.ElabelOption";
    static selector = ".s_elabel_information, .s_elabel_information_inner";
    setup() {
        super.setup();
        this.websiteId = Number(this.document.documentElement.dataset.websiteId);
        this.companyId = 0;
        onWillStart(async () => {
            const [website] = await this.services.orm.read("website", [this.websiteId], ["company_id"]);
            this.companyId = website.company_id[0];
        });
    }
    get domain() {
        return [["active", "in", [true, false]], ["elabel_enabled", "=", true],
            ["elabel_current_revision_id", "!=", false], ["website_id", "in", [false, this.websiteId]],
            ["company_id", "in", [false, this.companyId]]];
    }
}
class ElabelProductAction extends BuilderAction {
    static id = "elabelSnippetProduct";
    getValue({ editingElement }) {
        const id = Number(editingElement.dataset.elabelProductId);
        return id ? JSON.stringify({ id }) : undefined;
    }
    apply({ editingElement, value }) {
        const selected = value ? JSON.parse(value) : null;
        if (selected?.id) editingElement.dataset.elabelProductId = selected.id;
        else delete editingElement.dataset.elabelProductId;
    }
}
class ElabelAutomaticAction extends BuilderAction {
    static id = "elabelSnippetAutomatic";
    apply({ editingElement }) { delete editingElement.dataset.elabelProductId; }
}
class ElabelOptionPlugin extends Plugin {
    static id = "elabelSnippetOption";
    resources = {
        builder_options: [withSequence(SNIPPET_SPECIFIC_END, ElabelOption)],
        builder_actions: { ElabelProductAction, ElabelAutomaticAction },
        so_snippet_addition_selector: [".s_elabel_information_inner"],
        so_content_addition_selector: [".s_elabel_information_inner"],
        is_movable_selector: { selector: ".s_elabel_information_inner", direction: "vertical" },
        clean_for_save_handlers: ({ root }) => {
            const sections = [...(root.matches?.(".s_elabel_information, .s_elabel_information_inner") ? [root] : []), ...root.querySelectorAll(".s_elabel_information, .s_elabel_information_inner")];
            for (const section of sections) {
                section.querySelector(".o_elabel_snippet_content")?.replaceChildren();
                section.removeAttribute("hidden");
            }
        },
    };
}
registry.category("website-plugins").add(ElabelOptionPlugin.id, ElabelOptionPlugin);
