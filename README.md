# odoo_elabel (Odoo 19 CE)
E-Label fuer Wein mit Zutatenliste und Naehrwertdeklaration pro 100 ml.

## Ziel
Dieses Addon erweitert `product.template` um Felder fuer die gesetzlich relevanten e-Label-Daten und stellt eine oeffentliche Seite unter:

`/wine/e-label/<token>`

bereit.

## Umfang
- Aktivierung je Produkt (`Wine e-Label`)
- Deaktivierung ueber Button `Disable e-Label`
- Token werden erst fuer aktive e-Labels vergeben und bei Bedarf automatisch eindeutig erneuert
- Zutatenliste
- Allergiehinweis (zur Abstimmung mit dem physischen Etikett)
- Weitere Inhaltsstoffe / Zusatzinformationen
- Naehrwerttabelle pro 100 ml:
  - Energie (kJ/kcal)
  - Fett, davon gesaettigte Fettsaeuren
  - Kohlenhydrate, davon Zucker
  - Eiweiss
  - Salz
- Oeffentliche URL + QR-Code-Link (basierend auf Odoo Standard-Barcode-Route)
- Validierung gegen negative Naehrwerte
- Button `Generate e-Label` im Produkt:
  - erzeugt/aktualisiert automatisch QR-Code als `.svg`
  - erzeugt/aktualisiert automatisch e-Label als `.pdf`
  - speichert beide Dateien als Anhaenge am `product.template` (sichtbar im Smarttab `Documents`)
  - bleibt danach auf der aktuellen Produktansicht
- Die Link-Beschriftungen `Public e-Label URL` und `QR Code URL` oeffnen die jeweilige URL direkt, ohne die URL als langen Text anzuzeigen
- Optionaler Button `Regenerate QR SVG + PDF` fuer manuelles Neuaufbauen der Dateien
- Oeffentliche e-Label-Ausgabe in der Reihenfolge: Name, Naehrwertdeklaration, Zutaten, Allergene, weitere Inhaltsstoffe
- Oeffentliche e-Label-Seite nutzt die Website-Sprache, den Sprach-Cookie, `?lang=` oder die Browser-Sprache fuer die Ausgabe
- PDF-Erzeugung nutzt einen expliziten Odoo-Sprachkontext, damit uebersetzte QWeb- und Python-Texte im PDF ankommen
- Website-Shop-Integration (`website`, `website_sale`):
  - Auf der Produktseite wird im Bereich `Add to cart` ein Button `View e-Label` angezeigt
  - Der Button oeffnet die e-Label-Seite in einem neuen Browser-Tab/Fenster

## Technische Hinweise
- Abhaengigkeiten: `product`, `website`, `website_sale`
- Kein zusaetzliches Frontend-Framework, reine Odoo-QWeb-Ausgabe
- Route ist oeffentlich und nur lesend
- Oeffentliche e-Label-Seiten setzen `Vary: Accept-Language, Cookie`, damit Sprachvarianten sauber gecacht werden
- Webansicht und PDF nutzen denselben QWeb-Baustein fuer Naehrwerte, Zutaten, Allergene und weitere Inhaltsstoffe
- Uebersetzungen liegen in `i18n/de.po` und `i18n/de_DE.po`
- Sprache wird anhand des Odoo-Benutzerkontexts genutzt; auf der oeffentlichen e-Label-Seite zusaetzlich ueber Website-Sprach-Cookie, Browser-Sprache bzw. `?lang=` aufloesbar
- Odoo-Manifest-Version muss zwischen 2 und 5 Stellen haben.
- Verwendetes Schema im Manifest: `19.0.1.3.1` (`odoo_version.odoo_release.modul_version.release.patch`)

## Installation
1. Modul in den Addons-Pfad legen.
2. App-Liste aktualisieren.
3. Modul `Wine e-Label` installieren.
4. Im Produktformular den Reiter `Wine e-Label` pflegen.

## Rechtlicher Hinweis
Das Modul bildet die typischen EU-e-Label-Anforderungen technisch ab, ersetzt aber keine juristische Pruefung fuer deinen konkreten Betrieb, Wein-Typ und Zielmarkt.
