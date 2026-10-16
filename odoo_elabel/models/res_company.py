import ipaddress
from urllib.parse import urlsplit
from odoo import api, fields, models
from odoo.exceptions import ValidationError

class ResCompany(models.Model):
    _inherit='res.company'
    elabel_base_url=fields.Char(string='Dauerhafte e-Label-Basisadresse',
        help='Eigene stabile HTTPS-Adresse ohne Pfad. Leer: globale Odoo-Basisadresse. HTTP nur für lokale Testadressen.')

    def _elabel_validate_base_url(self,value):
        try:
            u=urlsplit(value or '')
            host=u.hostname
            local=host=='localhost'
            try:local=local or ipaddress.ip_address(host or '').is_private
            except ValueError:pass
            valid=bool(host and u.scheme in ('http','https') and not u.username and not u.password and
                       not u.query and not u.fragment and u.path in ('','/') and (u.scheme=='https' or local))
            _=u.port
        except ValueError:valid=False
        if not valid:
            raise ValidationError(self.env._('Bitte eine dauerhafte HTTPS-Basisadresse ohne Zugangsdaten, Pfad oder Parameter verwenden. HTTP ist nur für lokale Testadressen erlaubt.'))

    @api.constrains('elabel_base_url')
    def _check_elabel_base_url(self):
        for c in self.filtered('elabel_base_url'):c._elabel_validate_base_url(c.elabel_base_url)
