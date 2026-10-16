from odoo import fields, models

class ResConfigSettings(models.TransientModel):
    _inherit='res.config.settings'
    elabel_allow_http_test=fields.Boolean(
        string='HTTP für e-Label-Testzwecke erlauben',
        config_parameter='odoo_elabel.allow_http_test',groups='base.group_system',
        help='Erlaubt auch HTTP-Domains ohne TLS. Nur für Testbetrieb aktivieren; für Produktivbetrieb HTTPS verwenden.')
