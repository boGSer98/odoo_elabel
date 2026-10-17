# Weinanalytik und Nullwerte im Shop

Optionales Zusatzmodul `odoo_elabel_wine_analysis` (19.0.1.0.2): Felder unter Produkt → E-Label → Weinanalytik – Shop und Website.
Säuregehalt und Restsüße in g/l, Alkoholgehalt in %. Nicht aus Zucker (g/100 ml) ableiten.
Neue/geänderte Werte müssen erneut freigegeben werden; die Shop-Anzeige liest ausschließlich die unveränderliche Fassung.
Alte Fassungen haben keine Analytik und bleiben unverändert; Standard-Nullwerte ändern deren Inhalts-Hash nicht.

Die Shop-Brücke 19.0.1.4.6 blendet sämtliche auf 0,00 gerundeten numerischen Werte aus, auch einzelne Energiekomponenten.
Ist kein Nährwert übrig, entfallen Tabelle und Überschrift pro 100 ml. Zutaten und Allergene bleiben sichtbar.
Separate QR-/e-Label-Seite und PDFs behalten alle Nährwertzeilen einschließlich Nullwerten. Die separate Webseite bleibt ohne zusätzliche Analytikzeilen; die PDF zeigt seit Analytik-Version 19.0.1.0.1 die freigegebenen Analytikangaben. Die Darstellung wird bei vorhandener Analytik kompakt gehalten.

Der Core 19.0.1.4.3 ergänzt lediglich einen feldlosen Erweiterungshook für die bestehende Rollen-/Entwurfslogik.
Neue gespeicherte Spalten gehören ausschließlich zum opt-in Analytik-Modul. Es wird nur in der freigegebenen Testdatenbank installiert,
damit andere Datenbanken am selben Python-Dienst keine neuen Produktspalten benötigen. Documents bleibt 19.0.1.4.2.
Keine automatische Übernahme in alte Revisionen, kein Publizieren/Ändern realer Artikeldaten, keine automatische PDF-Neuerzeugung.

## PDF mit Weinanalytik

Die PDF zeigt freigegebene Analytikwerte in einer eigenen zweispaltigen Tabelle vor der Nährwertdeklaration. Die Anzeige verwendet die Freigabesprache bzw. deren bestehenden Fallback. Entwurfsänderungen gelangen weder über den Druckbericht noch über PDF/QR-Erzeugung in das Dokument. Ohne Analytik in der freigegebenen Revision wird keine Analytiktabelle erfunden; der Shopfilter für Nullwerte gilt weiterhin nur für Shop/Snippet, nicht für die PDF.

Die Erweiterung erfolgt ausschließlich über ein geerbtes PDF-Template im optionalen Analytik-Modul. Die separate e-Label-Webseite und das gemeinsame Shop-Template bleiben unverändert. Bereits gespeicherte PDF-Dateien werden bei der Modulaktualisierung nicht automatisch überschrieben. Für aktuelle Dateien die bestehende Aktion **PDF/QR erzeugen** verwenden; vorher gespeicherte Dokumente stammen weiterhin aus ihrer damaligen Erzeugung. Kein automatisches erneutes Freigeben und keine Massenregeneration.

## PDF-Abschnitte einheitlich eingerückt

Seit Analytik 19.0.1.0.2 stehen die untergeordneten Tabellen und Textinhalte mittig unter den Überschriften: 86 % Breite und beidseits 7 % Einzug. Analytik und Nährwerte teilen dieselbe Spaltenaufteilung, Bezeichnungen links und Werte rechts. Dezente Trennlinien und alternierende Zeilen erleichtern das Lesen. Nur das PDF-Template wird gestaltet; Werte, Freigaben, Shop, Standalone-Seite und vorhandene Dateien bleiben unverändert.
