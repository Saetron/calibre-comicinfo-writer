#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Constants and metadata definitions for ComicInfo.xml v2.1 (draft)
following the Anansi Project ComicInfo schema specification
(https://anansi-project.github.io/docs/comicinfo/schemas/v2.1).
"""

# Valid enum values according to ComicInfo v2.1 schema
AGE_RATINGS = [
    "Unknown",
    "Adults Only 18+",
    "Early Childhood",
    "Everyone",
    "Everyone 10+",
    "G",
    "Kids to Adults",
    "M",
    "MA15+",
    "Mature 17+",
    "PG",
    "R18+",
    "Rating Pending",
    "Teen",
    "X18+",
]

MANGA_VALUES = [
    "Unknown",
    "No",
    "Yes",
    "YesAndRightToLeft",
]

YES_NO_VALUES = [
    "Unknown",
    "No",
    "Yes",
]

# Common publication formats recognized across ComicInfo readers
COMICINFO_FORMAT_VALUES = [
    "Special",
    "Reference",
    "Director's Cut",
    "Box Set",
    "Box-Set",
    "Annual",
    "Anthology",
    "Epilogue",
    "One Shot",
    "One-Shot",
    "Prologue",
    "TPB",
    "Trade Paper Back",
    "Omnibus",
    "Compendium",
    "Absolute",
    "Graphic Novel",
    "GN",
    "FCBD",
    "Giant Size",
]
SPECIAL_FORMATS = COMICINFO_FORMAT_VALUES
KAVITA_SPECIAL_FORMATS = COMICINFO_FORMAT_VALUES  # Backward compatibility alias

# Standard ComicInfo v2.1 tags in strict schema sequence order
# Tag structure:
# (tag_name, data_type, default_calibre_field, description, schema_notes)
# data_type: 'string', 'int', 'decimal', 'enum_agerating', 'enum_manga', 'enum_yesno'
COMICINFO_TAG_DEFS = [
    # Schema Sequence Order
    ("Title", "string", "title", "Chapter/Book Title", "Chapter or Book Title"),
    ("Series", "string", "series", "Series name", "Series Name"),
    ("Number", "string", "series_index", "Issue/Chapter number (optionally omitted)", "Issue or Chapter Number"),
    ("Count", "int", None, "Total number of issues/volumes in series", "Total Count of Issues/Volumes"),
    ("Volume", "string", None, "Volume number or name (e.g. 1, Omnibus 1)", "Volume Number or Name"),
    ("AlternateSeries", "string", None, "Alternate series name", "Alternate Series Name"),
    ("AlternateNumber", "string", None, "Alternate issue/chapter number", "Alternate Issue Number"),
    ("AlternateCount", "int", None, "Total number of issues in alternate series", "Alternate Series Total Count"),
    ("Summary", "string", "comments", "Book/chapter summary or synopsis", "Summary or Synopsis"),
    ("Notes", "string", None, "Free-form notes about the book", "Notes"),
    ("Year", "int", "pubdate:year", "Release year", "Release Year"),
    ("Month", "int", "pubdate:month", "Release month (1-12)", "Release Month (1-12)"),
    ("Day", "int", "pubdate:day", "Release day (1-31)", "Release Day (1-31)"),
    ("Writer", "string", "authors", "Writer(s) (comma-separated)", "Writer(s)"),
    ("Penciller", "string", None, "Penciller(s) (comma-separated)", "Penciller(s)"),
    ("Inker", "string", None, "Inker(s) (comma-separated)", "Inker(s)"),
    ("Colorist", "string", None, "Colorist(s) (comma-separated)", "Colorist(s)"),
    ("Letterer", "string", None, "Letterer(s) (comma-separated)", "Letterer(s)"),
    ("CoverArtist", "string", None, "Cover Artist(s) (comma-separated)", "Cover Artist(s)"),
    ("Editor", "string", None, "Editor(s) (comma-separated)", "Editor(s)"),
    ("Translator", "string", None, "Translator(s) (comma-separated)", "Translator(s)"),
    ("Publisher", "string", "publisher", "Publisher name", "Publisher"),
    ("Imprint", "string", None, "Publisher imprint", "Publisher Imprint"),
    ("Genre", "string", None, "Genre(s) (comma-separated)", "Genres"),
    ("Tags", "string", "tags", "Tags / Keywords (comma-separated)", "Tags / Keywords"),
    ("Web", "string", "identifier:url", "Web link or URL", "Web URL"),
    ("PageCount", "int", None, "Total page count", "Total Page Count"),
    ("LanguageISO", "string", "languages", "ISO language code (e.g. en, ja, fr)", "ISO 639-1 Language Code"),
    ("Format", "string", None, "Format (e.g. TPB, Annual, Special)", "Publication Format"),
    ("BlackAndWhite", "enum_yesno", None, "Black & White (Yes, No, Unknown)", "Black and White Flag"),
    ("Manga", "enum_manga", None, "Manga reading order (Yes, YesAndRightToLeft, No)", "Manga Reading Direction"),
    ("Characters", "string", None, "Characters present (comma-separated)", "Characters"),
    ("Teams", "string", None, "Teams present (comma-separated)", "Teams"),
    ("Locations", "string", None, "Locations present (comma-separated)", "Locations"),
    ("ScanInformation", "string", None, "Scan / digitizer information", "Scan / Digitizer Information"),
    ("StoryArc", "string", None, "Story Arc name", "Story Arc Name"),
    ("StoryArcNumber", "string", None, "Story Arc issue number", "Story Arc Number"),
    ("SeriesGroup", "string", None, "Series Group / Collections (comma-separated)", "Series Group / Collection"),
    ("AgeRating", "enum_agerating", None, "Age Rating", "Age / Content Rating"),
    ("CommunityRating", "decimal", "rating", "Community Rating (0.0 - 5.0)", "Community Rating (0.0 - 5.0)"),
    ("MainCharacterOrTeam", "string", None, "Main Character or Team", "Main Character or Team"),
    ("Review", "string", None, "Review or commentary", "Review"),
    ("GTIN", "string", "identifier:isbn", "GTIN / ISBN / Barcode", "GTIN / ISBN Barcode"),
    ("LocalizedSeries", "string", None, "Localized series name", "Localized Series Name"),
    ("SeriesSort", "string", "series_sort", "Sort title for series", "Series Sort Title"),
]

# Quick lookup by tag name and ordered tag sequence
COMICINFO_TAG_MAP = {tag[0]: tag for tag in COMICINFO_TAG_DEFS}
ORDERED_TAG_NAMES = tuple(tag[0] for tag in COMICINFO_TAG_DEFS)
ALL_KNOWN_TAGS = frozenset(ORDERED_TAG_NAMES)

# Standard Calibre fields available for mapping
CALIBRE_STANDARD_FIELDS = [
    ("(None)", ""),
    ("Title", "title"),
    ("Title Sort", "title_sort"),
    ("Authors", "authors"),
    ("Author Sort", "author_sort"),
    ("Series", "series"),
    ("Series Index (Issue)", "series_index"),
    ("Series Sort", "series_sort"),
    ("Summary / Comments", "comments"),
    ("Publisher", "publisher"),
    ("Publication Date (Full)", "pubdate"),
    ("Publication Year", "pubdate:year"),
    ("Publication Month", "pubdate:month"),
    ("Publication Day", "pubdate:day"),
    ("Tags", "tags"),
    ("Rating (0-5)", "rating"),
    ("Languages", "languages"),
    ("ISBN Identifier", "identifier:isbn"),
    ("URL Identifier", "identifier:url"),
    ("URI Identifier", "identifier:uri"),
    ("Goodreads Identifier", "identifier:goodreads"),
    ("ComicVine Identifier", "identifier:comicvine"),
]
