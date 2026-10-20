# ComicInfo Writer (Kavita & ComicInfo v2.1) - Calibre Plugin

A powerful, customizable Calibre plugin to write and embed `ComicInfo.xml` metadata directly into comic archives (`.cbz` and `.cbr`) according to [Kavita's Comic Metadata Specification](https://wiki.kavitareader.com/guides/metadata/comics/) and the [Anansi Project ComicInfo v2.1 Draft Schema](https://anansi-project.github.io/docs/comicinfo/schemas/v2.1).

---

## Features

- **Full Custom Column Mapping**: Map any Calibre standard field or custom column (`#...`) to **every single ComicInfo tag** (e.g. `#writer`, `#penciller`, `#manga`, `#volume`, `#count`, `#age_rating`, `#series_group`, `#story_arc`).
- **Series Index Toggle**: Option to **omit** the series index number (`<Number>`) from `ComicInfo.xml` when desired, or format whole numbers cleanly (e.g. `1` instead of `1.0`).
- **Calibre Unset Date Filter**: Automatically recognizes Calibre's default unset publication date (`0101-01-01` / Year 101, Month 1, Day 1) and omits `<Year>`, `<Month>`, and `<Day>` rather than writing invalid historical dates.
- **Kavita Extensions Support**: Full support for Kavita-specific tags:
  - `<LocalizedSeries>`: Search and group alternate language series together in Kavita.
  - `<SeriesSort>`: Override series name sorting in Kavita.
  - `<SeriesGroup>`: Automatically populate Collections in Kavita.
  - `<Count>`: Automatic publication status in Kavita (`Ended` or `Completed`).
  - `<Format>`: Special format recognition (`TPB`, `Annual`, `Anthology`, `One Shot`, `Graphic Novel`, etc.).
  - `<AgeRating>`: Full rating hierarchy from `Early Childhood` to `X18+`.
- **Parse Existing ComicInfo.xml**: Parses existing `ComicInfo.xml` files inside comics (even those nested in subdirectories) to preserve `<Pages>` layout and unmapped metadata, or import tags directly into Calibre!
- **Always Delete Old ComicInfo**: Automatically detects and deletes all existing `ComicInfo.xml` files anywhere in the archive (root and nested subdirectories) before writing the new clean `ComicInfo.xml` strictly at the archive root.
- **Remove ComicInfo.xml Tool**: Dedicated option to completely strip all `ComicInfo.xml` files (root and nested) from selected comic books without writing a new one.
- **Import Metadata from ComicInfo.xml**: Reads existing `ComicInfo.xml` from comic archives into Calibre's book fields and custom columns.
- **Safe Atomic Archive Embedding**: Atomically replaces archives using temporary files to prevent comic corruption.
- **Metadata Merging**: Preserves existing tags and comic reader page information (`<Pages><Page Image="0" .../></Pages>`) inside the archive while updating metadata.
- **CBR Conversion (Optional)**: Can automatically unpack proprietary RAR-based `.cbr` archives using Calibre's unrar utility and convert them to standard `.cbz` archives with embedded metadata.
- **Batch Processing**: Write metadata into multiple selected comic books with a progress bar and summary report.

---

## Installation

### Method 1: Via Calibre GUI (Recommended)
1. In Calibre, go to **Preferences** -> **Plugins** (under *Advanced*).
2. Click **Load plugin from file** at the bottom right.
3. Select `ComicInfoWriter.zip` downloaded from the [Releases](https://github.com/Saetron/calibre-comicinfo-writer/releases) page (or built from source).
4. Click **Yes** to confirm installing the plugin.
5. Restart Calibre when prompted.
6. The **ComicInfo Writer** button will appear on your Calibre toolbar and in the right-click context menu.

### Method 2: Via Command Line
Run:
```bash
calibre-customize -a ComicInfoWriter.zip
```
Restart Calibre.

---

## Configuration & Custom Column Mapping

To open the configuration dialog:
- Click the arrow next to the **ComicInfo Writer** toolbar button and select **Configure Plugin & Field Mappings...**, or
- Go to **Preferences** -> **Plugins** -> select **ComicInfo Writer** -> click **Customize plugin**.

### 1. General Options
- **Write Series Index into `<Number>` tag**:
  - **Uncheck this** if you do not want Calibre's series index number written into `ComicInfo.xml`. When unchecked, the `<Number>` tag is completely omitted.
- **Format whole Series Index numbers as integers**:
  - Formats numbers like `1.0` as `1`.
- **Merge with existing ComicInfo.xml inside the archive**:
  - Preserves `<Pages>` layouts and any unmapped tags already present in the file.
- **Strip HTML tags from Summary / Comments**:
  - Converts HTML comments in Calibre to clean, unescaped plain text for `<Summary>`.
- **Convert CBR (RAR archives) to CBZ format**:
  - Automatically converts `.cbr` files into `.cbz` archives and adds them to your Calibre library.

### 2. Field Mappings Tab
Allows mapping each ComicInfo tag to:
- Any Calibre standard field: `title`, `series`, `authors`, `publisher`, `pubdate`, `tags`, `rating`, `comments`, `identifiers`, etc.
- Any custom column in your Calibre library: `#writer`, `#artist`, `#volume`, `#manga`, `#age_rating`, `#series_group`, etc.
- `(None)` to omit the tag.

**Helpful Buttons:**
- **Auto-detect Matching Columns**: Automatically scans your Calibre library's custom columns and pairs columns like `#writer`, `#volume`, `#manga`, `#age_rating`, `#series_group` to their corresponding ComicInfo tags.
- **Reset to Defaults**: Restores factory tag mappings.

---

## Supported ComicInfo Tags & Kavita Conversion

| ComicInfo Tag | Data Type | Default Calibre Field | Kavita Equivalent / Behavior |
|---|---|---|---|
| `Title` | String | `title` | Chapter / Issue Title |
| `Series` | String | `series` | Series Name |
| `SeriesSort` | String | `series_sort` | Series Sort Title (preferred over `Series` by Kavita) |
| `LocalizedSeries` | String | `(None)` | Localized Series Name (groups and enables alternate search in Kavita) |
| `Number` | String | `series_index` | Issue / Chapter Number (can be omitted via checkbox) |
| `Count` | Integer | `(None)` | Publication Status (sets *Ended* or *Completed* in Kavita) |
| `Volume` | Integer | `(None)` | Volume Number |
| `Summary` | String | `comments` | Series / Chapter Summary |
| `Publisher` | String | `publisher` | Publisher |
| `Imprint` | String | `(None)` | Publisher Imprint |
| `Year` | Integer | `pubdate:year` | Release Year (minimum year used for series in Kavita) |
| `Month` | Integer | `pubdate:month` | Release Month |
| `Day` | Integer | `pubdate:day` | Release Day |
| `Writer` | String | `authors` | Writer |
| `Penciller` | String | `(None)` | Penciller |
| `Inker` | String | `(None)` | Inker |
| `Colorist` | String | `(None)` | Colorist |
| `Letterer` | String | `(None)` | Letterer |
| `CoverArtist` | String | `(None)` | Cover Artist |
| `Editor` | String | `(None)` | Editor |
| `Translator` | String | `(None)` | Translator |
| `Genre` | String | `tags` | Genres |
| `Tags` | String | `tags` | Tags |
| `Web` | String | `(None)` | Web URL / Comic link |
| `LanguageISO` | String | `languages` | Language code (ISO 639-1) |
| `Format` | String | `(None)` | Format (`TPB`, `Annual`, `One Shot`, etc.) |
| `AgeRating` | String | `(None)` | Age Rating (`Rating Pending`, `Teen`, `Mature 17+`, etc.) |
| `Manga` | String | `(None)` | Manga reading direction (`YesAndRightToLeft`, etc.) |
| `SeriesGroup` | String | `(None)` | Story Arc / Collection Group (maps to Collections in Kavita) |
| `StoryArc` | String | `(None)` | Story Arc |
| `Characters` | String | `(None)` | Characters list |
| `Teams` | String | `(None)` | Teams list |
| `Locations` | String | `(None)` | Locations list |
| `ScanInformation` | String | `(None)` | Scanner / Digitizer info |
| `Notes` | String | `(None)` | Extra notes |

---

## How to Use

1. In Calibre, select one or more comic books in your library.
2. Click the **ComicInfo Writer** toolbar button or open its dropdown menu:
   - **Write ComicInfo.xml into Selected Books**: Deletes any existing `ComicInfo.xml` (root or subfolder), generates clean metadata from Calibre, and writes `ComicInfo.xml` to the root of each archive.
   - **Import Metadata from ComicInfo.xml into Calibre**: Finds existing `ComicInfo.xml` (root or nested), parses the tags, and updates Calibre's fields and custom columns.
   - **Remove ComicInfo.xml from Selected Books**: Completely removes all `ComicInfo.xml` files (including any nested in subdirectories) from the selected comics.
3. A completion dialog will display the summary report.

---

## Building from Source

To package the plugin into a `.zip` file for distribution:
```bash
python3 build_plugin.py
```
This generates `ComicInfoWriter.zip`.
