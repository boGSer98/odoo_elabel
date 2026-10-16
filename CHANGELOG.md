# Changelog

## 19.0.1.4.0

- Datenbankweite, dauerhaft reservierte Tokens einschließlich archivierter Produkte; kontrollierter Abbruch bei Bestandskollisionen statt Änderung gedruckter Kennungen.
- Rollenbasierter Entwurf-/Prüf-/Freigabeablauf, unveränderliche Veröffentlichungen, Bestandsmigration und explizite Deaktivierung.
- Quellen-/Prüfbestätigungen, Zahlen-/Nährwertplausibilität und lesende Vorschau ohne versteckte Schreibzugriffe.
- Stabile Dokumentidentität je Fassung/Dateiart/Sprache, Quellenhash und Änderungsanzeige; Historie bleibt erhalten.
- Optionale native Dokumente-Brücke mit gemeinsamem privaten E-Label-Ordner, kontrollierter Bestandszuordnung und Firmen-/Rollenprüfung auch beim Download.
- Mehrsprachige Veröffentlichung, DE/EN/NL-Ausgabe, lokalisierte PDF-Zahlen, HTTPS-Domainprüfung, No-Store/CSP und Route ohne neue Session-Cookies.
- Separates automatisch installierbares Shop-Addon; Basismodul funktioniert ohne Dokumente und Shop.
- Native Regressionstests, Paketvalidator, GitHub CI und Betriebs-/Migrationsdokumentation ergänzt.

## 19.0.1.3.3

- Deutsche Übersetzungen verwenden echte Umlaute und ß statt ASCII-Umschreibungen wie `ae`, `oe`, `ue` und `ss`.

## 19.0.1.3.2

- Web- und PDF-Ueberschriften werden ueber Python-Labels uebersetzt, damit die e-Label-Ausgabe nicht von uebersetzten QWeb-Architekturen abhaengt.
- PO-Referenzen fuer Web/PDF-Labels um Python-Code-Quellen erweitert.

## 19.0.1.3.1

- Deutsche PO-Dateien bereinigt, damit Odoo die Uebersetzungen ohne doppelte `msgid`-Eintraege importieren kann.
- Oeffentliche e-Label-Seite beruecksichtigt jetzt den Website-Sprach-Cookie sowie allgemeine Sprachcodes wie `de`.
- PDF-Rendering nutzt einen expliziten Sprachkontext und setzt die Report-Sprache am gemeinsamen QWeb-Baustein.
- e-Label-Token werden nur noch fuer aktive e-Labels vergeben und bei Duplikaten automatisch erneuert.
