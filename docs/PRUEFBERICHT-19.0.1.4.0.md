# Technischer Prüfbericht – 19.0.1.4.0

## Umfang und Umgebung

Umsetzung des freigegebenen Maßnahmenplans für `boGSer98/odoo_elabel`, Ausgangsstand `e50184f`, Version 19.0.1.3.3. Getrenntes Basismodul, Dokumente-Brücke und Shop-Brücke. Kein Odoo-/Webkul-Corepatch und kein Live-Deployment.

Native Abnahme auf Odoo Enterprise `19.0+e-20260323`, Python 3.12.3. Drei getrennte Wegwerfdatenbanken: Bestandsklon für Funktions-/HTTPprüfungen, Restore des Originalbackups für echte 1.3.3→1.4.0-Migration, frische Minimalinstallation ohne Dokumente und Shop. Cron, ein-/ausgehende Mailverarbeitung der Bestandsklone deaktiviert; ausschließlich synthetische Geschäftsvorgänge. Keine echten Sendungen, Buchungen, Rechnungen oder Zahlungen.

## Automatisierte native Tests

- **42 Tests**, keine Fehler: Basismodul und Dokumente-Brücke gemeinsam im Enterprise-Bestandsklon.
- **27 Basismodultests**, keine Fehler: frische Installation mit `documents`, `website_sale` und beiden optionalen Brücken **nicht installiert**. Diese 27 sind dieselben Basismodulfälle in einer zweiten Abhängigkeitskonfiguration, nicht 27 zusätzliche eigenständige Testfälle.
- Geprüft: rollenbasierte Aktionen; fremde Firmen; Portal; reine Produktleser; positive Bearbeiter-/Prüferaktionen; Daten-/Token-/Fassungsmanipulation; bestätigte Nullwerte; negative/NaN/Infinity-Werte; Zucker/Kohlenhydrate, gesättigte Fettsäuren/Fett, Energieplausibilität; Prüfpflichten; Kopien; permanente Tokens; Dokumentmetadaten, Zuordnung, Regeneration, Dateischutz, Vorschaubilder und Ordnerwiederverwendung.
- Absichtlich provozierte UNIQUE-Verletzungen erscheinen im Testlog als SQL-Fehler; die jeweiligen Negativtests und das Gesamtergebnis bestehen.

## Zusätzliche echte Laufzeitprüfungen

1. Zwei unabhängige Datenbanktransaktionen mit identischem synthetischem Token: genau eine erfolgreiche Transaktion, zweite mit `UniqueViolation`. Kein gleichzeitiger Doppelbesitz.
2. Upgrade aus tatsächlich altem 1.3.3-Code und wiederhergestellter Datenbank: archivierte Tokenkollision führt zum kontrollierten Upgradeabbruch. Nur der künstlich angelegte kollidierende Datensatz wurde anschließend mit altem Code entfernt; ursprünglicher Token blieb unverändert.
3. Danach erfolgreiche echte 1.3.3→1.4.0-Migration: archiviertes aktiviertes Label wird als prüfbedürftige Bestandsfassung erhalten, deaktiviertes Label bleibt deaktiviert, Quelleninhalt und Tokens bleiben gleich.
4. Bestands-PDF nach ausdrücklicher Zuordnungsbestätigung zweimal übernommen: gleiche Anhangs-/Dokument-Identität, unveränderte Dateibytes und geschlossene Freigabe. Kein bestätigter Quellenhash wird für unbekannte historische Binärdaten erfunden.
5. Dokumente-Brücke wirklich deinstalliert und neu installiert: normale Dokumentdatensätze einschließlich wesentlicher Metadaten unverändert; verwaltete Dateien/Datensätze bleiben bestehen, Freigaben geschlossen. Nach bestätigter erneuter Ordnerzuordnung dieselben Ordner-/Datei-IDs.
6. Öffentliche HTTP-Seiten DE/EN/NL: richtige Zutaten und übersetzte Überschriften; kein neuer Session-Cookie durch die e-Label-Route, `no-store`, CSP und weitere Schutzheader.
7. Tatsächliche HTTP-Entwurfsänderung: öffentliche Seite zeigt weiterhin die alte Freigabe, nicht den Entwurf. Neue Freigabe verwendet denselben Token. Eingeschleuste `<script>`-Texte werden escaped.
8. Archiviertes freigegebenes Produkt bleibt per gedrucktem Token erreichbar; ausdrückliche Deaktivierung liefert beim nächsten Abruf 404 mit `no-store`.
9. **12 direkte HTTP-Downloadprüfungen**: PDF und SVG jeweils über native Dokumente- und Anhangsroute, mit berechtigtem Bearbeiter, unbeteiligtem internen Dokumentebenutzer und anonymem Client. Berechtigt jeweils 200 mit korrektem Dateityp; unberechtigt jeweils 404.
10. Echte PDFs auf Deutsch, Englisch und Niederländisch erzeugt und mit PDF-Textparser geprüft; deutsche Ausgabe mit lokalisierten Dezimalzahlen. Echte QR-SVGs mit ReportLab erzeugt. Keine ausschließlich gemockte PDF-Abnahme.
11. Reale Browserprüfung der Produkt-/E-Label- und Dokumenteliste. Dabei ermittelter nativer PDF-Thumbnail-Schreibzugriff wird gezielt erlaubt, ohne Labeldatei oder Freigabe zu verändern; dazu eigener Regressionstest. Kein pauschales Aufweichen der Dateisperre.

## Review und Grenzen

Qwen3-Coder und GPT-OSS wurden nacheinander lokal ohne Secrets eingesetzt. Der erste Dokumente-Entwurf wurde wegen falscher Odoo-APIs, Gruppen-/Feldreferenzen und unzureichender Rechte-/Transaktionsbehandlung **nicht übernommen**. Die Implementierung wurde anhand der tatsächlich installierten nativen Quellen erstellt und von Hermes geprüft.

Der zweite Review wurde technisch erfolgreich ausgeführt, lieferte aber überwiegend nicht zutreffende Annahmen (unter anderem vermeintliche Schlüsselwort-Syntaxfehler sowie unzutreffende Schema-/Constraint-/Bereinigungsbehauptungen). Diese wurden anhand von Quellcode, Datenbankschema und Laufzeittests abgeglichen. Er zählt **nicht** als unabhängige fachliche Freigabe oder Sicherheitszertifizierung.

Fachliche Richtigkeit, Vollständigkeit der Zutaten/Allergene, rechtliche Pflichtangaben, Messquellen, Übersetzungen und physisches Etikett müssen vom Betreiber geprüft werden. Prüfbestätigungen und Rollenworkflow ersetzen diese Verantwortung nicht. Vier-Augen-Trennung zwischen verschiedenen Personen wird nicht erzwungen.

Eine dauerhafte öffentliche HTTPS-Domain samt Erhalt alter Domainweiterleitungen ist Betriebsaufgabe. Lokale HTTP-Ausnahmen dienen ausschließlich dem Testbetrieb. Bereits früher ausgelieferte Cacheantworten können bis zu ihrem alten Ablauf weiterbestehen. Reverse-Proxy-/CDN-Verhalten außerhalb dieser Odoo-Instanz ist nicht Teil dieser Abnahme.

GitHub CI validiert Syntax, XML, Manifeste, Abhängigkeitsgrenzen und ACL-Dateien mit Python 3.11/3.12; lizenzpflichtige Enterprise-Runtime-Tests liefen separat auf dem Testserver.
