# Weinanalytik und Nullwerte im Shop

Optionales Zusatzmodul `odoo_elabel_wine_analysis` (19.0.1.0.0): Felder unter Produkt → E-Label → Weinanalytik – Shop und Website.
Säuregehalt und Restsüße in g/l, Alkoholgehalt in %. Nicht aus Zucker (g/100 ml) ableiten.
Neue/geänderte Werte müssen erneut freigegeben werden; die Shop-Anzeige liest ausschließlich die unveränderliche Fassung.
Alte Fassungen haben keine Analytik und bleiben unverändert; Standard-Nullwerte ändern deren Inhalts-Hash nicht.

Die Shop-Brücke 19.0.1.4.6 blendet sämtliche auf 0,00 gerundeten numerischen Werte aus, auch einzelne Energiekomponenten.
Ist kein Nährwert übrig, entfallen Tabelle und Überschrift pro 100 ml. Zutaten und Allergene bleiben sichtbar.
Separate QR-/e-Label-Seite und PDFs behalten alle Nährwertzeilen einschließlich Nullwerten; dort keine zusätzlichen Analytik-Zeilen.

Der Core 19.0.1.4.3 ergänzt lediglich einen feldlosen Erweiterungshook für die bestehende Rollen-/Entwurfslogik.
Neue gespeicherte Spalten gehören ausschließlich zum opt-in Analytik-Modul. Es wird nur in der freigegebenen Testdatenbank installiert,
damit andere Datenbanken am selben Python-Dienst keine neuen Produktspalten benötigen. Documents bleibt 19.0.1.4.2.
Keine automatische Übernahme in alte Revisionen, kein Publizieren/Ändern realer Artikeldaten, keine automatische PDF-Neuerzeugung.
