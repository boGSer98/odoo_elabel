from odoo import Command
from .models.documents import ElabelDocuments

def post_init_hook(env):
    Model=env['documents.document']
    # Do not hijack an existing unmarked folder; finish installation so the
    # administrator can explicitly review/take it over in the setup wizard.
    if Model.sudo().search_count([('type','=','folder'),('name','=','E-Label'),('folder_id','=',False),('elabel_root','=',False)]):
        return
    Model._elabel_folder()

def uninstall_hook(env):
    # Records have no module-owned external IDs. Retain all user files and close
    # generic internal/link access before the additional gates are removed.
    docs=env['documents.document'].sudo().with_context(active_test=False).search([('elabel_managed','=',True)])
    if docs:
        super(ElabelDocuments,docs).write({'access_internal':'none','access_via_link':'none',
            'is_access_via_link_hidden':True,'access_ids':[Command.clear()]})
