# Changelog

Alle wichtigen Änderungen an diesem Projekt werden in dieser Datei dokumentiert.

Das Format basiert auf [Keep a Changelog](https://keepachangelog.com/de/1.0.0/),
und dieses Projekt folgt [Semantic Versioning](https://semver.org/lang/de/spec/v2.0.0.html).

## [Unreleased]

### Hinzugefügt
- Mehrsprachige Dokumentation (Englisch und Deutsch)
- MkDocs Material Theme mit verbesserter Navigation
- API-Referenz-Dokumentation mit mkdocstrings
- Umfangreicher Beispielabschnitt
- Referenztabellen für Bundesländer-Codes, Registerarten und Rechtsformen

### Geändert
- Dokumentation für bessere Organisation umstrukturiert
- Verbesserte Code-Beispiele mit mehr Kontext

---

## [1.0.0] - 2024-01-15

### Hinzugefügt
- Erstveröffentlichung
- `search()`-Funktion für Unternehmenssuche
- `get_details()`-Funktion für detaillierte Unternehmensinformationen
- `HandelsRegister`-Klasse für Low-Level-Zugriff
- `SearchCache`-Klasse für Ergebnis-Caching
- Kommandozeilen-Interface (CLI)
- Datenmodelle: `Company`, `CompanyDetails`, `Address`, `Representative`, `Owner`
- Fehlerbehandlung: `SearchError`, `RateLimitError`, `ConnectionError`, `ParseError`
- JSON-Ausgabeformat für CLI
- Unterstützung für Bundesland-Filterung
- Unterstützung für Registerart-Filterung

### Dokumentation
- README mit Verwendungsbeispielen
- Installationsanleitung
- API-Dokumentation

---

## Versionshistorie

| Version | Datum | Beschreibung |
|---------|-------|--------------|
| 1.0.0 | 2024-01-15 | Erstveröffentlichung |
| 0.9.0 | 2023-12-01 | Beta-Release |
| 0.1.0 | 2023-06-01 | Alpha-Release |

---

## Migrationsanleitungen

### Migration von 0.x auf 1.0

Keine Breaking Changes. Das 1.0-Release markiert API-Stabilität.

---

## Roadmap

### Geplante Features

- [ ] Async-Unterstützung (`async/await`)
- [ ] Detaillierteres Historie-Parsing
- [ ] Dokumentenabruf
- [ ] Webhook-Benachrichtigungen für Unternehmensänderungen
- [ ] Datenbank-Export-Funktionalität

### In Überlegung

- GraphQL-API-Wrapper
- Unternehmensüberwachungsdienst
- Tools für historische Datenanalyse

---

## Beitragen

Siehe [Beitragsrichtlinien](https://github.com/bundesAPI/handelsregister/blob/main/CONTRIBUTING.md) für Informationen zum Beitragen zu diesem Projekt.

### Probleme melden

- Verwenden Sie [GitHub Issues](https://github.com/bundesAPI/handelsregister/issues) für Fehlermeldungen
- Geben Sie Python-Version, Betriebssystem und Schritte zur Reproduktion an
- Prüfen Sie bestehende Issues, bevor Sie neue erstellen

