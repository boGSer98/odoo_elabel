# Changelog

## 19.0.1.4.2

- Administrator-Einstellung für ausdrückliche HTTP-Testfreigabe ergänzt; erlaubt auch öffentliche Testdomains ohne TLS. Standard bleibt HTTPS bzw. lokale HTTP-Adressen.
- URL-Zugangsdaten, Pfade, Queryparameter, Fragmente und ungültige Ports bleiben unabhängig vom Testmodus gesperrt.
- 51 native Tests bestanden; positive HTTP-Freigabe, Abschalten, Kontextmanipulation und unberechtigte Parameteränderung abgedeckt.

## 19.0.1.4.1

- Text-/Sprachfassungsbestätigung ist kein Freigabekriterium mehr; Prüffeld aus der Produktansicht entfernt.
- Nährwertauffälligkeiten werden als gelbe Hinweise angezeigt und verhindern weder Speichern noch Freigabe; Werte werden nicht automatisch korrigiert.
- Negative bzw. nicht endliche Zahlen bleiben gesperrt. Rechte, Quellen-/Allergenbestätigung, unveränderliche Fassungen und private Dokumentablage bleiben erhalten.
- 46 native Tests im frischen Prüfbestand erfolgreich, einschließlich Freigabe auffälliger Nährwerte ohne Sprachbestätigung.

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
