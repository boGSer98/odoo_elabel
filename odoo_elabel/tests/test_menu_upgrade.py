import importlib.util
from pathlib import Path

from odoo import tools
from odoo.exceptions import MissingError
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestMenuUpgrade(TransactionCase):
    def test_xml_upgrade_explicitly_clears_legacy_root_action(self):
        menu = self.env.ref('odoo_elabel.menu_elabel_root')
        action = self.env['ir.actions.act_window'].create({
            'name': 'Synthetic legacy e-Label action',
            'res_model': 'product.template', 'view_mode': 'list,form'})
        menu.write({'action': 'ir.actions.act_window,%s' % action.id})
        tools.convert_file(self.env, 'odoo_elabel', 'views/product_template_views.xml', {}, mode='update')
        self.assertFalse(menu.action)
        self.assertTrue(self.env['ir.ui.menu'].with_user(2).load_menus(False))

    def test_orphaned_root_action_migration_repairs_backend_menu_loading(self):
        menu = self.env.ref('odoo_elabel.menu_elabel_root')
        missing_id = 1000000000
        self.assertFalse(self.env['ir.actions.act_window'].browse(missing_id).exists())
        self.env.flush_all()
        self.env.cr.execute('UPDATE ir_ui_menu SET action=%s WHERE id=%s',
                            ['ir.actions.act_window,%s' % missing_id, menu.id])
        self.env.invalidate_all()
        self.env.registry.clear_cache()
        with self.assertRaises(MissingError):
            self.env['ir.ui.menu'].with_user(2).load_menus(False)
        path = Path(__file__).resolve().parents[1] / 'migrations/19.0.1.4.4/post-migration.py'
        spec = importlib.util.spec_from_file_location('elabel_menu_upgrade', path)
        assert spec and spec.loader
        migration = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(migration)
        migration.migrate(self.env.cr, '19.0.1.4.3')
        migration.migrate(self.env.cr, '19.0.1.4.3')
        self.assertFalse(menu.action)
        self.assertTrue(self.env['ir.ui.menu'].with_user(2).load_menus(False))
