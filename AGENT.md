# AGENTS.md

## Projektkontext

Dieses Repository enthält ein Odoo-Community-Modul oder mehrere Odoo-Community-Untermodule für Odoo 19.

Die Entwicklung erfolgt lokal unter WSL im Pfad:

/home/alex/odoo-dev/custom-addons

Odoo wird lokal über localhost getestet.

Die Versionierung soll wie folgt sein:
19.0.1.0.0
│    │ │ │
│    │ │ └─ kleine Korrektur
│    │ └─── funktionale Erweiterung
│    └───── Modulversion
└────────── Odoo-Version

Fasse in CHANGELOG.md alle Änderungen mit der jeweiligen Verionsnummer zusammen.

Bearbeite die Anwenderanleitung mit den neuen Änderungen. Sollten Features gelöscht werden, so passe die Anleitung ebenfalls an. 

## Odoo-Regeln

- Zielversion: Odoo 19 Community
- Verwende Odoo-Standardkonventionen.
- Ändere keine Odoo-Core-Dateien.
- Änderungen müssen updatefähig bleiben.
- Sichtbare Texte sollen auf Deutsch formuliert werden.
- Python-Code soll klar, wartbar und möglichst nah an Odoo-Konventionen sein.
- XML-Views müssen valide sein.
- Security-Dateien und Zugriffsrechte müssen bei neuen Modellen berücksichtigt werden.
- Keine unnötigen Abhängigkeiten einbauen.
- Keine sensiblen Daten, Tokens oder Passwörter in das Repository schreiben.

## Git-Regeln

- Arbeite nicht direkt auf main.
- Erstelle für jede Aufgabe einen eigenen Feature-Branch.
- Mache kleine, nachvollziehbare Commits.
- Vor einem Commit immer prüfen:
  - git status
  - git diff

## Testregeln

Nach Änderungen soll das betroffene Modul lokal aktualisiert und getestet werden.

Beispiel:

python3 /home/alex/odoo-dev/odoo/odoo-bin \
  -c /home/alex/odoo-dev/config/odoo-dev.conf \
  --addons-path="$(python3 /home/alex/odoo-dev/scripts/generate-addons-path.py)" \
  -d odoo_dev \
  -u MODULNAME \
  --stop-after-init

## Review guidelines

- Prüfe besonders auf Odoo-Konventionsfehler.
- Prüfe fehlerhafte XML-IDs.
- Prüfe fehlende security/ir.model.access.csv-Einträge.
- Prüfe fehlende Abhängigkeiten in __manifest__.py.
- Prüfe, ob Änderungen updatefähig sind.
- Prüfe, ob bestehende Datenmodelle unnötig verändert werden.
