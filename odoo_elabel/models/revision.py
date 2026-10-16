from odoo import api, fields, models
from odoo.exceptions import AccessError, UserError
from .presentation import LabelPresentation

class WineElabelRevision(models.Model):
    _name = 'wine.elabel.revision'
    _description = 'Unveränderliche e-Label-Veröffentlichung'
    _order = 'product_id, number desc'

    product_id = fields.Many2one('product.template', required=True, ondelete='restrict', index=True)
    company_id = fields.Many2one(related='product_id.company_id', store=True, index=True)
    number = fields.Integer(string='Fassung', required=True)
    name = fields.Char(string='Bezeichnung', required=True)
    payload = fields.Json(required=True)
    content_hash = fields.Char(required=True, index=True)
    source = fields.Text(string='Datengrundlage')
    checked_on = fields.Date(string='Fachlich geprüft am')
    legacy = fields.Boolean(string='Bestandsfassung – erneute Prüfung erforderlich')
    _number_unique = models.Constraint('UNIQUE(product_id, number)', 'Die Veröffentlichungsnummer muss eindeutig sein.')

    @api.model_create_multi
    def create(self, vals_list):
        raise AccessError(self.env._('Veröffentlichungen werden ausschließlich durch die e-Label-Freigabe angelegt.'))

    def write(self, vals):
        raise AccessError(self.env._('Veröffentlichte e-Label-Fassungen sind unveränderlich.'))

    def unlink(self):
        raise UserError(self.env._('Veröffentlichte e-Label-Fassungen dürfen nicht gelöscht werden.'))

    def _presentation(self, lang=None):
        self.ensure_one()
        return LabelPresentation(self, lang or self.env.lang)
