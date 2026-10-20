# AGENTS.md

This document serves as a guide for AI agents and developers working on the **ComicInfo Writer** Calibre plugin codebase.

---

## 1. Project Overview

**ComicInfo Writer** is a Calibre plugin designed to write and embed schema-compliant `ComicInfo.xml` metadata into digital comic archives (`.cbz` and `.cbr`). The metadata follows the [Anansi Project ComicInfo v2.0 and v2.1 Draft Schemas](https://anansi-project.github.io/docs/comicinfo/schemas/v2.1), universally supported by modern comic readers, media servers, and organizers.

### Core Capabilities
- Mapping Calibre standard and custom columns to ComicInfo metadata tags.
- Parsing and merging existing `ComicInfo.xml` files inside comic archives (preserving `<Pages>` layouts).
- Clean removal of legacy or nested `ComicInfo.xml` files.
- Atomic file replacement for safe archive writing without corruption risk.
- Optional CBR (RAR) to CBZ (ZIP) conversion.
- Full UI integration with Calibre toolbars, context menus, and configuration dialogs.

---

## 2. Repository Structure

```
├── .github/
│   ├── dependabot.yml           # Automated monthly checks for GitHub Actions
│   └── workflows/
│       └── release.yml          # Manual GitHub workflow for version bumps and releases
├── images/
│   └── icon.png                 # Plugin icon (displayed in Calibre UI)
├── tests/
│   ├── test_archive_ops.py      # Unit tests for CBZ archive manipulation and atomic updates
│   ├── test_field_mapper.py     # Unit tests for tag mappings and data conversions
│   └── test_xml_generator.py    # Unit tests for ComicInfo XML generation and parsing
├── .gitignore                   # Ignores build artifacts, __pycache__, and *.zip files
├── __init__.py                  # Calibre plugin entry point and metadata definition (version tuple)
├── build_plugin.py              # Script packaging the plugin into ComicInfoWriter.zip
├── CHANGELOG.md                 # Project changelog following Keep a Changelog standard
├── comic_processor.py           # Core logic: XML generation, archive inspection, atomic file ops
├── comicinfo_constants.py       # Anansi Project ComicInfo schema constants, tags, and enum values
├── config.py                    # Calibre JSONConfig storage and preference management
├── config_dialog.py             # Qt GUI configuration dialog for settings and column mappings
├── kavita_constants.py          # Backward-compatibility alias redirecting to comicinfo_constants.py
├── plugin-import-name-comicinfo_writer.txt  # Calibre plugin import namespace declaration
├── LICENSE                      # EUPL v1.2 License
└── README.md                    # User-facing documentation and installation guide
```

---

## 3. Calibre Plugin Conventions

### Versioning
- The plugin version is maintained in [`__init__.py`](file:///Users/jbudz/Documents/calibre%20comicinfo/__init__.py) as an integer tuple:
  ```python
  version = (1, 0, 0)
  ```
- Always ensure version bumps update this tuple accurately.

### Calibre Import Namespaces
Inside Calibre's runtime, plugins are imported using the namespace specified in [`plugin-import-name-comicinfo_writer.txt`](file:///Users/jbudz/Documents/calibre%20comicinfo/plugin-import-name-comicinfo_writer.txt):
```python
try:
    from calibre_plugins.comicinfo_writer.config import get_pref
except ImportError:
    from config import get_pref
```
Always maintain fallback imports so that standalone scripts and unit tests can run outside the full Calibre GUI environment.

### Distribution Archives
- `ComicInfoWriter.zip` is **not** tracked in git (ignored in `.gitignore`).
- Distribution zips are built on demand via [`build_plugin.py`](file:///Users/jbudz/Documents/calibre%20comicinfo/build_plugin.py) and published to GitHub Releases.

---

## 4. Development & Build Commands

### Building the Plugin ZIP
To package the plugin into `ComicInfoWriter.zip`:
```bash
python3 build_plugin.py
```
This packages all required source files into the distributable archive.

### Running Unit Tests
To run the automated test suite:
```bash
python3 -m unittest discover tests
```

### Installing into Calibre (Local Testing)
To install the built plugin directly into a local Calibre installation via CLI:
```bash
calibre-customize -a ComicInfoWriter.zip
```
To run Calibre with debug console output:
```bash
calibre-debug -g
```

---

## 5. Changelog Maintenance

The project maintains a [`CHANGELOG.md`](file:///Users/jbudz/Documents/calibre%20comicinfo/CHANGELOG.md) adhering to the [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) standard and [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

### Guidelines for Developers and Agents
- **Document All Notable Changes**: Whenever adding features, fixing bugs, refactoring architecture, or modifying schema handling, add corresponding bullet points to the `## [Unreleased]` section of [`CHANGELOG.md`](file:///Users/jbudz/Documents/calibre%20comicinfo/CHANGELOG.md).
- **Use Standard Category Headings**:
  - `### Added`: New user-facing features, tools, or configuration options.
  - `### Changed`: Changes in existing functionality, optimizations, or refactoring.
  - `### Deprecated`: Features planned for removal in future versions.
  - `### Removed`: Features or code paths removed in this version.
  - `### Fixed`: Bug fixes, edge case resolutions, or regression fixes.
  - `### Security`: Vulnerability fixes or security improvements.
- **Preparing Releases**:
  - When releasing a new version, promote the entries under `## [Unreleased]` to a version section header:
    ```markdown
    ## [X.Y.Z] - YYYY-MM-DD
    ```
  - Re-add an empty `## [Unreleased]` block at the top for upcoming changes.
  - Ensure the version matches the tuple in [`__init__.py`](file:///Users/jbudz/Documents/calibre%20comicinfo/__init__.py).

---

## 6. Release Workflow

Releases are managed via GitHub Actions:
- **Workflow File**: [`.github/workflows/release.yml`](file:///Users/jbudz/Documents/calibre%20comicinfo/.github/workflows/release.yml)
- **Repository**: `https://github.com/Saetron/calibre-comicinfo-writer`
- **Trigger**: Manual dispatch (`workflow_dispatch`).
- **Inputs**:
  - `version` *(required)*: Target version string (e.g. `1.0.1` or `v1.0.1`).
  - `prerelease` *(optional)*: Mark as pre-release.
  - `draft` *(optional)*: Create as draft.
- **Pre-Release Checklist**:
  1. Ensure all tests pass (`python3 -m unittest discover tests`).
  2. Verify [`CHANGELOG.md`](file:///Users/jbudz/Documents/calibre%20comicinfo/CHANGELOG.md) has an entry for the target version with current date.
- **Workflow Process**:
  1. Validates and parses the version string into integers.
  2. Updates `version = (X, Y, Z)` in [`__init__.py`](file:///Users/jbudz/Documents/calibre%20comicinfo/__init__.py).
  3. Executes [`build_plugin.py`](file:///Users/jbudz/Documents/calibre%20comicinfo/build_plugin.py) to package `ComicInfoWriter.zip`.
  4. Commits the updated [`__init__.py`](file:///Users/jbudz/Documents/calibre%20comicinfo/__init__.py), tags the commit (`vX.Y.Z`), and pushes to GitHub.
  5. Creates a GitHub Release with auto-generated release notes and attaches `ComicInfoWriter.zip`.

---

## 7. Coding Standards & Agent Guidelines

- **Python Compatibility**: Target Python 3.10+ (Calibre 6+ uses Python 3).
- **Atomic File Operations**: Always write modified archives to temporary files first before replacing original files to prevent data loss.
- **Schema Compliance**: Maintain strict adherence to ComicInfo v2.0/v2.1 specifications when modifying XML elements in [`comic_processor.py`](file:///Users/jbudz/Documents/calibre%20comicinfo/comic_processor.py) and [`comicinfo_constants.py`](file:///Users/jbudz/Documents/calibre%20comicinfo/comicinfo_constants.py).
- **Changelog Updates**: Update [`CHANGELOG.md`](file:///Users/jbudz/Documents/calibre%20comicinfo/CHANGELOG.md) under `[Unreleased]` for any non-trivial changes, fixes, or optimizations.
- **Preserve Comments & Docstrings**: Keep existing docstrings and explanatory comments intact when modifying existing files.

