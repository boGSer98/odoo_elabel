# Changelog

## 19.0.1.3.2

- Web- und PDF-Ueberschriften werden ueber Python-Labels uebersetzt, damit die e-Label-Ausgabe nicht von uebersetzten QWeb-Architekturen abhaengt.
- PO-Referenzen fuer Web/PDF-Labels um Python-Code-Quellen erweitert.

## 19.0.1.3.1

- Deutsche PO-Dateien bereinigt, damit Odoo die Uebersetzungen ohne doppelte `msgid`-Eintraege importieren kann.
- Oeffentliche e-Label-Seite beruecksichtigt jetzt den Website-Sprach-Cookie sowie allgemeine Sprachcodes wie `de`.
- PDF-Rendering nutzt einen expliziten Sprachkontext und setzt die Report-Sprache am gemeinsamen QWeb-Baustein.
- e-Label-Token werden nur noch fuer aktive e-Labels vergeben und bei Duplikaten automatisch erneuert.
