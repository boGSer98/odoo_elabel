import ipaddress
from urllib.parse import urlsplit
from odoo import api, fields, models
from odoo.exceptions import ValidationError

class ResCompany(models.Model):
    _inherit='res.company'
    elabel_base_url=fields.Char(string='Dauerhafte e-Label-Basisadresse',
        help='Eigene stabile HTTPS-Adresse ohne Pfad. Leer: globale Odoo-Basisadresse. HTTP-Testbetrieb kann in den E-Label-Einstellungen ausdrücklich erlaubt werden.')

    def _elabel_validate_base_url(self,value):
        http_test=self.env['ir.config_parameter'].sudo().get_param('odoo_elabel.allow_http_test','False').strip().lower() in ('true','1','yes')
        try:
            u=urlsplit(value or '')
            host=u.hostname
            local=host=='localhost'
            try:local=local or ipaddress.ip_address(host or '').is_private
            except ValueError:pass
            valid=bool(host and u.scheme in ('http','https') and u.username is None and u.password is None and
                       not u.query and not u.fragment and u.path in ('','/') and (u.scheme=='https' or local or http_test))
            _=u.port
        except ValueError:valid=False
        if not valid:
            raise ValidationError(self.env._('Bitte eine dauerhafte HTTPS-Basisadresse ohne Zugangsdaten, Pfad oder Parameter verwenden. HTTP ist nur für lokale Adressen oder bei ausdrücklich aktivierter HTTP-Testfreigabe erlaubt.'))

    @api.constrains('elabel_base_url')
    def _check_elabel_base_url(self):
        for c in self.filtered('elabel_base_url'):c._elabel_validate_base_url(c.elabel_base_url)
