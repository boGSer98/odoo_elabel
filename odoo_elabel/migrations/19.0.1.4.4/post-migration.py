from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    menu = env.ref('odoo_elabel.menu_elabel_root', raise_if_not_found=False)
    if not menu:
        return
    # Read the raw reference: fetching a broken Reference can itself fail.
    cr.execute('SELECT action FROM ir_ui_menu WHERE id=%s', [menu.id])
    action = cr.fetchone()[0]
    if not action or not action.startswith('ir.actions.act_window,'):
        return
    action_id = int(action.split(',', 1)[1])
    if not env['ir.actions.act_window'].browse(action_id).exists():
        menu.write({'action': False})
