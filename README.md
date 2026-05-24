# Wine e-Label für Odoo 19 CE

Dieses Modul erweitert Produkte um ein öffentlich abrufbares Wein-e-Label mit Zutatenliste, Allergenhinweis und Nährwertdeklaration pro 100 ml.

## Ziel

Das Modul ergänzt `product.template` um Felder für gesetzlich relevante e-Label-Daten und veröffentlicht diese Informationen über eine tokenbasierte, lesende Website-Route:

`/wine/e-label/<token>`

Die öffentliche Seite ist für Endkunden ohne Anmeldung erreichbar, solange das e-Label am Produkt aktiviert ist.

## Funktionsumfang

- Aktivierung je Produkt über das Feld `Wine e-Label`
- Automatische Vergabe eines eindeutigen Tokens für aktive e-Labels
- Öffentliche e-Label-URL und QR-Code-URL im Produktformular
- Zutatenliste mit übersetzbarem Inhalt
- Allergenhinweis für das physische Etikett, standardmäßig `Enthält Sulfite`
- Weitere Inhaltsstoffe oder Angaben zur Zusammensetzung
- Nährwerttabelle pro 100 ml:
  - Energie in kJ und kcal
  - Fett
  - davon gesättigte Fettsäuren
  - Kohlenhydrate
  - davon Zucker
  - Eiweiß
  - Salz
- Optionale Nährwertanmerkung
- Validierung gegen negative Nährwerte
- Öffentliche Webansicht und PDF-Ausgabe mit demselben QWeb-Baustein
- QR-Code als SVG und e-Label als PDF in den Produktanhängen
- Website-Shop-Integration mit Button `View e-Label` auf der Produktseite

## Bedienung im Produkt

Im Produktformular steht der Reiter `Wine e-Label` zur Verfügung. Nach Aktivierung des e-Labels werden die Eingabefelder und Aktionen angezeigt.

- `Generate e-Label` erzeugt oder aktualisiert QR-SVG und PDF und bleibt danach auf der Produktansicht.
- `Regenerate QR SVG + PDF` baut beide Dokumente erneut auf.
- `Disable e-Label` deaktiviert das öffentliche e-Label für das Produkt.
- `Public e-Label URL` öffnet die öffentliche e-Label-Seite in einem neuen Tab.
- `QR Code URL` öffnet den über die Odoo-Barcode-Route generierten QR-Code.

Die erzeugten Dateien werden am `product.template` als Anhänge gespeichert und sind über den Odoo-Dokumenten-Smartbutton sichtbar.

## Öffentliche Ausgabe

Die öffentliche e-Label-Seite zeigt die Informationen in dieser Reihenfolge:

1. Produktname
2. Nährwertdeklaration
3. Zutaten
4. Allergene
5. Weitere Inhaltsstoffe

Die Seite setzt `Cache-Control: public, max-age=300` sowie `Vary: Accept-Language, Cookie`, damit Sprachvarianten sauber ausgeliefert werden können.

## Sprachverhalten

Die öffentliche Seite bestimmt die Sprache in dieser Reihenfolge:

1. URL-Parameter `?lang=`
2. Website-Sprach-Cookie `frontend_lang`
3. aktueller Odoo-Kontext
4. Browser-Sprache aus `Accept-Language`
5. Sprache des öffentlichen Benutzers
6. Fallback auf `en_US` oder die erste verfügbare Odoo-Sprache

PDF-Erzeugung verwendet einen expliziten Odoo-Sprachkontext. QWeb-Überschriften und Python-Texte werden über Übersetzungen aufgelöst, damit Webansicht und PDF konsistente Texte verwenden.

Deutsche Übersetzungen liegen in `i18n/de.po` und `i18n/de_DE.po` und verwenden echte Umlaute sowie ß.

## Technische Hinweise

- Zielversion: Odoo 19 Community
- Modulversion: `19.0.1.3.3`
- Lizenz: AGPL-3
- Abhängigkeiten: `product`, `website`, `website_sale`
- Erweiterte Modelle: `product.template`
- Öffentliche Route: `/wine/e-label/<token>`
- Report: `odoo_elabel.action_report_wine_elabel_pdf`
- QR-Code-Erzeugung: ReportLab, über Odoos bestehende Python-Umgebung
- Keine zusätzlichen Frontend-Frameworks

## Installation

1. Modul in einen Odoo-Addons-Pfad legen.
2. App-Liste aktualisieren.
3. Modul `Wine e-Label` installieren oder aktualisieren.
4. Im Produktformular den Reiter `Wine e-Label` pflegen.
5. Bei bestehenden Installationen das Modul aktualisieren, damit Übersetzungen, Views und Reportdefinitionen neu geladen werden.

Beispiel für ein lokales Modulupdate:

```bash
python3 /home/alex/odoo-dev/odoo/odoo-bin \
  -c /home/alex/odoo-dev/config/odoo-dev.conf \
  --addons-path="$(python3 /home/alex/odoo-dev/scripts/generate-addons-path.py)" \
  -d odoo_dev \
  -u odoo_elabel \
  --stop-after-init
```

## Rechtlicher Hinweis

Das Modul bildet typische technische Anforderungen für EU-Wein-e-Labels ab. Es ersetzt keine rechtliche Prüfung für den konkreten Betrieb, das konkrete Produkt oder den jeweiligen Zielmarkt.
