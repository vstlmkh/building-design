# Changelog

## [0.2.0] - 2026-11-23

### Added

- Dual Claude Code and Kimi Code project discovery and manual installation.
- Kimi Code frontmatter, `${KIMI_SKILL_DIR}` support, and a shared `$SKILL_DIR` path contract.
- Zero-dependency `npx building-design` installer for user-level and project-local installs.
- npm package metadata, repository validation, CI, and tag-driven release automation.

### Changed

- Script commands and generated handoff documentation now resolve utilities from the installed skill rather than the product repository.
- Eval instructions cover both Claude Code and Kimi Code.

### Fixed

- Ignore vendored JavaScript when checking prototype token usage.
