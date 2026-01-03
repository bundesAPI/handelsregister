# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Multilingual documentation (English and German)
- MkDocs Material theme with improved navigation
- API reference documentation with mkdocstrings
- Comprehensive examples section
- Reference tables for state codes, register types, and legal forms

### Changed
- Documentation restructured for better organization
- Improved code examples with more context

---

## [1.0.0] - 2024-01-15

### Added
- Initial release
- `search()` function for company searches
- `get_details()` function for detailed company information
- `HandelsRegister` class for low-level access
- `SearchCache` class for result caching
- Command-line interface (CLI)
- Data models: `Company`, `CompanyDetails`, `Address`, `Representative`, `Owner`
- Exception handling: `SearchError`, `RateLimitError`, `ConnectionError`, `ParseError`
- JSON output format for CLI
- State filtering support
- Register type filtering support

### Documentation
- README with usage examples
- Installation instructions
- API documentation

---

## Version History

| Version | Date | Description |
|---------|------|-------------|
| 1.0.0 | 2024-01-15 | Initial release |
| 0.9.0 | 2023-12-01 | Beta release |
| 0.1.0 | 2023-06-01 | Alpha release |

---

## Migration Guides

### Migrating from 0.x to 1.0

No breaking changes. The 1.0 release marks API stability.

---

## Roadmap

### Planned Features

- [ ] Async support (`async/await`)
- [ ] More detailed history parsing
- [ ] Document retrieval
- [ ] Webhook notifications for company changes
- [ ] Database export functionality

### Under Consideration

- GraphQL API wrapper
- Company monitoring service
- Historical data analysis tools

---

## Contributing

See [Contributing Guidelines](https://github.com/bundesAPI/handelsregister/blob/main/CONTRIBUTING.md) for how to contribute to this project.

### Reporting Issues

- Use [GitHub Issues](https://github.com/bundesAPI/handelsregister/issues) for bug reports
- Include Python version, OS, and steps to reproduce
- Check existing issues before creating new ones

