import uuid
from odoo import api, SUPERUSER_ID, Command
from odoo.addons.odoo_elabel.models.product_template import ProductTemplate

def migrate(cr, version):
    env=api.Environment(cr,SUPERUSER_ID,{})
    languages=env['res.lang'].search([])
    for p in env['product.template'].with_context(active_test=False).search([('elabel_enabled','=',True),('elabel_current_revision_id','=',False)]):
        super(ProductTemplate,p).write({'elabel_language_ids':[Command.set(languages.ids)]})
        revision=p._elabel_make_revision(legacy=True)
        super(ProductTemplate,p).write({'elabel_current_revision_id':revision.id,'elabel_state':'review',
            'elabel_token':p.elabel_token or str(uuid.uuid4())})
