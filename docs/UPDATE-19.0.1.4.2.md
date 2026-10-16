# 19.0.1.4.2 – ausdrückliche HTTP-Testfreigabe

Technische Administratoren können unter **E-Label → Einstellungen** die Option **HTTP für e-Label-Testzwecke erlauben** aktivieren. Der datenbanklokale Systemparameter lautet `odoo_elabel.allow_http_test`; Standard ist deaktiviert. Auf der ausdrücklich freigegebenen Testdatenbank wird er beim Deployment aktiviert. Produktivsysteme werden weder aktualisiert noch umkonfiguriert.

Mit aktivierter Option sind auch HTTP-Domains erlaubt, nicht nur lokale IP-Adressen. HTTPS bleibt immer zulässig. Anmeldedaten, Pfade, Queryparameter, Fragmente und ungültige Ports bleiben gesperrt. Normale Labelbearbeiter können die Option nicht aktivieren; manipulierte RPC-Kontextwerte ersetzen sie nicht. Das Abschalten sperrt neue Freigaben mit öffentlichem HTTP-Ursprung wieder, ohne gespeicherte QR-Kennungen oder vorhandene Dateien zu ändern.

Abnahme auf frischer isolierter Datenbank: **51 native Odoo-Tests, keine Fehler**, einschließlich HTTP-Veröffentlichung ohne Textbestätigung, aktivem/inaktivem Testmodus und weiterhin abgelehnten unsicheren URL-Bestandteilen.
