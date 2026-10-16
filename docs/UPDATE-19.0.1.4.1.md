# 19.0.1.4.1 – Hinweise statt Nährwertsperren

Auf ausdrücklichen Betreiberwunsch ist keine Text-/Sprachprüfung erforderlich. Das bisherige Bestätigungsfeld bleibt aus Kompatibilitätsgründen gespeichert, ist aber nicht mehr in der Produktansicht enthalten und wird bei der Freigabe nicht ausgewertet.

Zucker/Kohlenhydrate, gesättigte Fettsäuren/Gesamtfett und Energieauffälligkeiten einschließlich bestätigter Nullwerte sind nicht blockierende gelbe Hinweise im Backend. Es erfolgt keine automatische Änderung oder fachliche Zertifizierung der Werte. Negative Zahlen und NaN/Infinity bleiben technische Eingabefehler.

Der Freigabeablauf, Rollen, bestehende Pflichtangaben zu Nährwert-/Allergenbestätigung, Quelle, Prüfdatum und Sprache sowie HTTPS-Prüfung bleiben unverändert. Vorhandene veröffentlichte Fassungen und Dateien werden durch das Update nicht verändert oder neu freigegeben.

Native Abnahme: frische isolierte Datenbank, Odoo 19.0+e-20260323, Python 3.12.3; **46 Tests, 0 Fehler**. Ergänzt wurden insbesondere mehrere Sprachen ohne Bestätigung, Freigabe trotz Zucker-/Fett-/Energiehinweisen, Warnungsrücknahme nach Korrektur und unveränderte Übernahme auffälliger Zahlen in die Veröffentlichung.
