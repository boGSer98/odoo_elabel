import { ElabelInformation } from "./elabel_information";
import { registry } from "@web/core/registry";
const Edit = (I) => class extends I {
    setup() { super.setup(); this.editing = true; }
};
registry.category("public.interactions.edit").add("odoo_elabel_sale.information", {
    Interaction: ElabelInformation, mixin: Edit,
});
