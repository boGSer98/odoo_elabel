# Changelog

## 19.0.1.3.1

- Deutsche PO-Dateien bereinigt, damit Odoo die Uebersetzungen ohne doppelte `msgid`-Eintraege importieren kann.
- Oeffentliche e-Label-Seite beruecksichtigt jetzt den Website-Sprach-Cookie sowie allgemeine Sprachcodes wie `de`.
- PDF-Rendering nutzt einen expliziten Sprachkontext und setzt die Report-Sprache am gemeinsamen QWeb-Baustein.
- e-Label-Token werden nur noch fuer aktive e-Labels vergeben und bei Duplikaten automatisch erneuert.
