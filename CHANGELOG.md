# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-02-13

### Added
- Multi-language support (English/German) for both PDF and Web formats
- Automated build system (`build.py`) with selective build flags
- JSON Resume integration with vendored `stackoverflow` theme
- Single-file SPA resume with embedded images (Base64) for email portability
- Smart language routing with browser detection
- Dynamic output filenames based on user configuration
- Proper i18n date formatting via moment.js locale support
- Custom render script (`render_cv.js`) for reliable HTML generation

### Changed
- Refactored project structure with proper separation of concerns
- Moved theme to vendored directory for full control
- Replaced hardcoded translations with locale-based formatting
- Updated build process to use custom renderer instead of resume-cli

### Security
- All personal information (PII) stored in gitignored `config/` directory
- Example configuration files provided for reference

## [0.1.0] - Initial Development

### Added
- Basic LaTeX CV templates (1-page and 2-page variants)
- Initial JSON Resume support
- Basic build automation

[1.0.0]: https://github.com/utkarshq/cv/releases/tag/v1.0.0
[0.1.0]: https://github.com/utkarshq/cv/releases/tag/v0.1.0
