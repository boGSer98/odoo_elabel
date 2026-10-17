# e-Label als Website-Builder-Baustein

Shop-Anbindung: `odoo_elabel_sale 19.0.1.4.5`; e-Label-Core und Documents bleiben unverändert.

## Verwendung

Website öffnen → Bearbeiten → Bausteine → Inhalt oder Innere Inhalte → **e-Label – Zutaten und Nährwerte**.
Den Block einfügen, unter **Stil → e-Label-Produkt** ein Produkt mit aktivem, freigegebenem e-Label auswählen und speichern.
Auf Produktseiten kann **Aktuelles Produkt verwenden** die Zuordnung aus dem normalen Produktformular übernehmen.
Mehrere Blöcke können unabhängig unterschiedlichen Produkten zugeordnet werden.
Die bestehende automatische Box unter der Kaufenbox und der separate e-Label-Button bleiben erhalten.

## Daten und Schutz

Die Anzeige lädt dieselbe unveränderliche, freigegebene Revision wie die bestehende Shopbox.
Gespeichert wird nur die Produktzuordnung, nicht der geladene Zutaten-/Nährwertinhalt.
Ohne geeignete Freigabe bleibt der öffentliche Block verborgen; im Editor erscheint ein Konfigurationshinweis.
Die öffentliche Fragmentroute verwendet normale Produktleserechte und explizite Website-/Unternehmensgrenzen.
Es gibt keine freie Modell-/Template-Auswahl, keine Draft-/Quellmetadaten und keine Snapshot-Änderung.
Die Antwort ist nicht zwischenspeicherbar (`Cache-Control: no-store`).

## Abnahmegrenze

Im neutralisierten Prüfklon erfolgreich: natives Einfügen, Produktauswahl und Wechsel, automatischer Modus-Schalter,
Duplizieren mit unabhängigen Produkten, Speichern und anonyme Anzeige. Zurückgelesene Seitenarchitektur enthält
nur die Bindung, keine Zutaten-/Nährwertkopie.
Die Platzierung innerhalb bestehender Spalten ist noch nicht abschließend abgenommen: verfügbare Einfügezonen
werden erkannt, der automatisierte Zieh-Test positionierte bislang vor/nach dem umgebenden Abschnitt.
Dieser Teststand wird nicht als vollständige Freigabe aller Spalten-/Builderpositionen dargestellt.

## Dauerhafte Label-Anzeige unabhängig vom Artikelstatus

Freigegebene, aktivierte Labels bleiben sichtbar und auswählbar, auch wenn das Produkt ausverkauft,
nicht mehr verkäuflich, unveröffentlicht oder archiviert ist. Nur die explizite e-Label-Deaktivierung
unterbindet die Anzeige. Es wird weiterhin nur die unveränderliche freigegebene Revision dargestellt.
Website-/Unternehmensgrenzen bleiben erhalten; interne Produktdaten und Entwurfswerte werden nicht veröffentlicht.
Die Produkt-Shopseite selbst wird dadurch weder veröffentlicht noch kaufbar gemacht; bei unveröffentlichten
oder archivierten Produkten kann sie weiterhin 404 liefern. Label-URL/QR und separat platzierter Snippet
bleiben zugänglich. Der e-Label-Button auf erreichbaren Produktseiten liegt außerhalb des kaufabhängigen
`add_to_cart_wrap`, damit das Ausblenden von Kaufaktionen den Label-Link nicht entfernt.
