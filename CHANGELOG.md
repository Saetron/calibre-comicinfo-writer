# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Full language name resolution in ISO 639-1 normalization (supporting natural names like "English", "Japanese", "French", "German", "Spanish", etc.).
- Automated GitHub Actions release workflow (`release.yml`) supporting manual version dispatch, tag creation, and asset packaging.
- Dependabot configuration for monthly GitHub Actions workflow dependency updates.
- EUPL v1.2 software license (`LICENSE`).
- Comprehensive developer and AI agent guide (`AGENTS.md`).
- Project changelog (`CHANGELOG.md`).

### Changed
- Standardized plugin identity to **ComicInfo Writer** following Anansi Project ComicInfo v2.0 and v2.1 draft schemas.
- Generalized metadata conventions beyond Kavita to support all standard comic readers and servers (e.g. Panels, Chunky, YACReader, Komga, Ubooquity).
- Maintained `kavita_constants.py` as a backward-compatibility alias forwarding to `comicinfo_constants.py`.
- Optimized ComicInfo XML serialization using native `xml.etree.ElementTree.indent` on modern Python versions (3.9+).
- Streamlined CBZ archive writing using single-pass inspection and atomic temporary file replacement.
- Deduplicated batch UI operation helpers and progress feedback in `ui.py`.
- Improved column auto-detection and import resilience in configuration dialog (`config_dialog.py`).

### Fixed
- Precompiled regular expressions at module level for language normalization and XML tag cleanup to improve processing throughput.
- Enforced clean root-level placement of `ComicInfo.xml` while ensuring legacy nested files in subdirectories are safely removed.

## [1.0.0] - 2026-09-14

### Added
- Initial release of ComicInfo Writer (formerly Embed ComicInfo.xml) Calibre plugin.
- Direct embedding and writing of schema-compliant `ComicInfo.xml` metadata into `.cbz` and `.cbr` archives.
- Configurable field mapping between standard Calibre metadata fields, custom columns (`#...`), and ComicInfo tags.
- Support for Anansi Project ComicInfo v2.0 and v2.1 tags (including `LocalizedSeries`, `SeriesSort`, `SeriesGroup`, `AgeRating`, `Manga`, `Format`, etc.).
- Option to omit or format series index numbers (`<Number>`).
- Calibre unset date filtering (ignoring default `0101-01-01` dates).
- Metadata merging support to preserve comic reader `<Pages>` layouts and unmapped existing metadata.
- Import metadata tool to extract tags from existing `ComicInfo.xml` files into Calibre book records.
- Dedicated tool to remove existing `ComicInfo.xml` files from comic archives.
- Automatic conversion of `.cbr` (RAR) archives to `.cbz` (ZIP) format using Calibre's unrar utility.
- Calibre GUI integration: toolbar action, dropdown menus, context menus, and configuration dialog.
