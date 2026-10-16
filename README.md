# Wine e-Label für Odoo 19

**Version 19.0.1.4.1 · IT-Service AHD · AGPL-3**

Zutaten-/Nährwertkennzeichnung mit geprüften Veröffentlichungsfassungen, dauerhaften QR-Kennungen und optionaler privater Ablage in Odoo Dokumente. Technische Kontrollen ersetzen weder die fachliche Prüfung der Messwerte noch Rechtsberatung.

## Module und Installation

Das Repository enthält jetzt drei eigenständige Addon-Verzeichnisse:

- `odoo_elabel`: Basismodul; benötigt `product` und `website`, **nicht** Dokumente oder den Shop.
- `odoo_elabel_documents`: optionale Enterprise-Anbindung; benötigt `documents_product`. Native Dokumente-Ordner und Originalanhänge werden verwendet; keine eigene Dokumentenverwaltung.
- `odoo_elabel_sale`: optionale, automatisch installierbare Shop-Brücke bei installiertem `website_sale` und Basismodul.

**Wichtig beim Update von 19.0.1.3.3:** Nicht mehr den Repository-Stamm als ein einzelnes Addon kopieren. Die drei genannten Verzeichnisse unmittelbar in einen konfigurierten `addons_path` legen. Der technische Name des Basismoduls und bestehende XML-IDs bleiben erhalten.

Vor dem Update Datenbank, Filestore, Addon-Code und Konfiguration sichern. Zuerst an einer neutralisierten Kopie prüfen. Nur die gewählte Datenbank aktualisieren, nicht pauschal `-u all`. Das Update stoppt bei Bestands-Tokenkollisionen einschließlich archivierter Produkte. Gedruckte Kennungen **nicht** automatisch ersetzen; Originalzuordnung anhand des Druck-/Produktbestands prüfen. Das Modul ändert keine bestehenden nichtleeren Tokens.

## Bedienung

1. Am Produkt im Reiter **E-Label** Zutaten, Allergene und Nährwerte erfassen.
2. Datenquelle und Prüfdatum eintragen. Nährwerte und Allergenprüfung ausdrücklich bestätigen. Numerische Null allein gilt nicht als bestätigter Messwert.
3. Freizugebende aktive Sprachen auswählen. Übersetzte Produktnamen und Texte über Odoo pflegen. Eine gesonderte Text-/Sprachprüfung oder Bestätigung ist nicht erforderlich.
4. **Zur Prüfung**: Pflichtangaben müssen vorhanden sein. Rechnerische Nährwertauffälligkeiten sind gelbe Hinweise und verhindern die Freigabe nicht. Dazu zählen Zucker über Kohlenhydraten, gesättigte Fettsäuren über Gesamtfett, Null-Energie und abweichende kJ-/kcal-Verhältnisse. Negative oder nicht endliche Zahlen bleiben technisch unzulässig.
5. Ein berechtigter Prüfer wählt **Freigeben**. Erst jetzt entsteht eine unveränderliche Fassung und erstmals eine öffentliche Kennung.
6. **PDF und QR speichern**: speichert die freigegebene Fassung in der aktuellen Odoo-Sprache, soweit diese freigegeben ist; ansonsten in der ersten freigegebenen Sprache. Für weitere Sprachfassungen mit der entsprechenden Odoo-Benutzersprache erzeugen. Die Sprache steht im Dateinamen und in Dokumente.
7. **Veröffentlichung öffnen** funktioniert auch ohne Produkt-Schreibrechte, sofern das Produkt gelesen werden darf. Es verändert keine Produktdaten.

Änderungen am Produkt setzen den Arbeitsstand zurück auf Entwurf. Die bisherige Freigabefassung bleibt öffentlich, bis eine neue Fassung freigegeben oder die öffentliche Ausgabe ausdrücklich deaktiviert wird. PDFs werden niemals aus ungeprüften Entwurfsdaten erzeugt. Neue Veröffentlichungen erhalten neue Historienfassungen und neue Dateipaare; Regeneration derselben Fassung/Sprache verwendet dieselben Anhangs-/Dokument-IDs. Artikelnummern sind keine Dateiidentität.

Das Archivieren eines Produkts widerruft seinen gedruckten Link **nicht**. Dafür gibt es **Öffentliche Ausgabe deaktivieren**. Der Token bleibt auch dann reserviert; Produkte mit vergebenem Token dürfen nicht gelöscht oder in ein anderes Unternehmen verschoben werden. Kopien erhalten weder Token noch Freigabe.

## Rollen

- **E-Label bearbeiten**: Label-Entwürfe und ausdrücklich angeforderte Dateierzeugung. Produkt-Schreibrechte werden zusätzlich geprüft und nicht automatisch vergeben.
- **E-Label prüfen und veröffentlichen**: zusätzlich Freigabe, Deaktivierung und kontrollierte Bestandszuordnung; enthält die Bearbeiterrolle.
- Technische Odoo-Administratoren sind für Administration freigeschaltet; Firmen-/Produktrechte bleiben bei normalen Benutzern maßgeblich.
- Für die native Dokumente-App bei Bedarf außerdem die reguläre Dokumente-Benutzerrolle vergeben. Niemand erhält pauschal neue interne Dokumentenrechte.

Das Verfahren ist rollenbasiert, **keine erzwungene personelle Vier-Augen-Trennung**: Ein Prüfer kann eigene Entwürfe freigeben. Eine solche organisatorische Trennung kann betrieblich vorgenommen werden.

## Odoo Dokumente

Nach Installation der Brücke existiert ein gemeinsamer Ordner namens exakt **E-Label**. Er gehört nicht exklusiv einem Unternehmen; jede Datei behält ihr Produktunternehmen. Geteilte Produkte und deren Dateien bleiben gemäß Odoo-Standard unternehmensübergreifend geteilt, aber nur für berechtigte e-Label-Rollen zugänglich.

- Native `documents.document`-Dateien verweisen auf die **vorhandenen** `ir.attachment`-Dateien. Kein Kopieren des Binärinhalts.
- Produkt, Veröffentlichung, Dateiart und Sprache sind dauerhaft verknüpft. Die Liste ist unter **E-Label → Dokumente** erreichbar.
- Kein öffentlicher Ordnerlink, kein öffentlicher Dateilink, keine automatisch übernommenen Freigabe-Mitglieder. Auch private Anhangs-Downloads sind zusätzlich rollen-/firmenbeschränkt.
- Native PDF-Vorschaubilder bleiben möglich; PDF-/SVG-Inhalte, Identität und Freigaben sind nicht frei im Dokumente-Editor überschreibbar. Historien-Dateien werden nicht durch normale Lösch-/Kopieraktionen entsorgt.
- Der normale Dokumentebestand außerhalb des e-Label-Bereichs bleibt unverändert.

Falls bereits ein nicht verwalteter gleichnamiger Hauptordner vorhanden ist, wird er **nicht blind übernommen** und kein zweiter angelegt. Technische Administratoren verwenden **E-Label → Ordner konfigurieren** mit ausdrücklicher Bestätigung. Zulässig sind leere Ordner oder Ordner, die ausschließlich anhand der Modulmetadaten nachweisbar verwaltete e-Label-Dateien enthalten. Beliebige Benutzerdateien werden abgewiesen. Nach Deinstallation bleiben Dokumente/Dateien bestehen, die e-Label-Freigaben werden geschlossen. Nach Neuinstallation lässt sich der erhaltene Ordner bewusst erneut zuordnen.

### Vorhandene Dateien und Migration

**E-Label → Bestandsdateien prüfen und zuordnen** zeigt Kandidaten am ausgewählten Produkt. Vor Bestätigung Datei öffnen, Produkt/Fassung/Sprache prüfen. Kein automatisches Verschieben anhand des Dateinamens. Es darf höchstens eine PDF und eine SVG je Fassung/Sprache zugeordnet werden; unklare Altduplikate bleiben unangetastet und müssen historisch eingeordnet werden. Wiederholte Bestätigung ändert weder die Zuordnung noch den Dateiinhalt und erzeugt keine Duplikate. Zuvor öffentliche Altdateien werden bei bestätigter Übernahme privat.

Die Software kann den Entstehungsstand alter Binärdateien nicht nachträglich beweisen. Übernommene Altdateien erhalten deshalb keinen bestätigten Quellenhash und bleiben als prüfbedürftig erkennbar. Keine automatische Löschung oder pauschale Token-/Dateierneuerung.

Vorhandene aktivierte 1.3.3-Labels werden als **prüfbedürftige Bestandsfassungen** übernommen, auch bei archivierten Produkten. Ihre bestehenden URLs und Inhalte bleiben zunächst erhalten. Neue Dateierzeugung erfordert zuerst eine fachliche Freigabe nach den neuen Regeln. Deaktivierte Altlabels bleiben deaktiviert.

## Öffentliche Seite, Sprachen und Domain

Die öffentliche Seite zeigt nur die aktuelle Freigabefassung, ohne Produktbearbeitung, Shop-Layout, Websitebesucher-Tracking oder neue Session-Cookies durch diese Route. Texte werden escaped. Antworten sind nicht cachebar (`no-store`), mit CSP, `nosniff`, Frame-Sperre, Referrer-/Robots-Policy. Unbekannte/deaktivierte Kennungen liefern 404; doppelte Treffer werden nicht nach dem Zufallsprinzip aufgelöst.

Sprache: ausdrückliches `?lang=de_DE` / `en_US` / `nl_NL`, dann `Accept-Language`, dann verfügbare Freigabesprache. Nur freigegebene Sprachen werden angeboten. Öffentliche Überschriften enthalten deutsche und niederländische Übersetzungen; Englisch ist die Basissprache. Die Dateien übernehmen die freigegebenen Textübersetzungen und lokalisierte Zahlen.

Unter **Unternehmen → Dauerhafte e-Label-Basis-URL (HTTPS)** eine langfristige Domain konfigurieren. Ohne Angabe gilt `web.base.url`; globale Produkte verwenden immer diese globale Basis statt der zufälligen Betrachterfirma. HTTP ist nur für lokale/private Testadressen erlaubt. Domainwechsel benötigen betriebliche Weiterleitungen für bereits gedruckte URLs; dieses Modul richtet weder DNS noch Reverse-Proxy-Weiterleitungen ein. Bestehende Proxy-/Browser-Caches aus Version 1.3.3 können erst nach Ablauf ihrer alten Gültigkeit verschwinden; neue Antworten sind `no-store`.

## Prüfungen

- `python3 scripts/checks.py`: Python-/XML-/Manifest-/ACL-/Abhängigkeitsprüfungen ohne Odoo.
- Native Tests liegen in beiden Addons unter `tests/`; siehe [Prüfbericht](docs/PRUEFBERICHT-19.0.1.4.0.md).
- GitHub CI prüft das Paket mit Python 3.11/3.12. Enterprise-Runtime-Tests benötigen berechtigten Enterprise-Code und laufen nicht auf einem öffentlichen GitHub-Runner.
- Energieplausibilität verwendet eine breite technische kJ/kcal-Toleranz und ersetzt keine lebensmittelrechtliche Berechnung. Quelle/Prüfbestätigungen werden durch Bediener verantwortet.
