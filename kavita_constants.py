#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Constants and metadata definitions for ComicInfo.xml v2.1 (draft)
and Kavita extensions (https://wiki.kavitareader.com/guides/metadata/comics/).
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

# Formats recognized by Kavita to mark an issue or volume as a "Special"
KAVITA_SPECIAL_FORMATS = [
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

# Standard ComicInfo v2.1 tags in strict schema sequence order
# Tag structure:
# (tag_name, data_type, default_calibre_field, description, kavita_mapping)
# data_type: 'string', 'int', 'decimal', 'enum_agerating', 'enum_manga', 'enum_yesno'
COMICINFO_TAG_DEFS = [
    # Schema Sequence Order
    ("Title", "string", "title", "Chapter/Book Title", "Chapter Title"),
    ("Series", "string", "series", "Series name", "Series Name"),
    ("Number", "string", "series_index", "Issue/Chapter number (optionally omitted)", "Issue/Chapter number"),
    ("Count", "int", None, "Total number of issues/volumes in series", "Publication Status (Ended/Completed if >0)"),
    ("Volume", "string", None, "Volume number or name (e.g. 1, Omnibus 1)", "Volume"),
    ("AlternateSeries", "string", None, "Alternate series name", "Reading Lists"),
    ("AlternateNumber", "string", None, "Alternate issue/chapter number", "Reading Lists"),
    ("AlternateCount", "int", None, "Total number of issues in alternate series", "Reading Lists"),
    ("Summary", "string", "comments", "Book/chapter summary or synopsis", "Series & Chapter Summary"),
    ("Notes", "string", None, "Free-form notes about the book", "Notes"),
    ("Year", "int", "pubdate:year", "Release year", "Release Date / Series Release Year"),
    ("Month", "int", "pubdate:month", "Release month (1-12)", "Release Date"),
    ("Day", "int", "pubdate:day", "Release day (1-31)", "Release Date"),
    ("Writer", "string", "authors", "Writer(s) (comma-separated)", "Writer"),
    ("Penciller", "string", None, "Penciller(s) (comma-separated)", "Penciller"),
    ("Inker", "string", None, "Inker(s) (comma-separated)", "Inker"),
    ("Colorist", "string", None, "Colorist(s) (comma-separated)", "Colorist"),
    ("Letterer", "string", None, "Letterer(s) (comma-separated)", "Letterer"),
    ("CoverArtist", "string", None, "Cover Artist(s) (comma-separated)", "Cover Artist"),
    ("Editor", "string", None, "Editor(s) (comma-separated)", "Editor"),
    ("Translator", "string", None, "Translator(s) (comma-separated)", "Translator"),
    ("Publisher", "string", "publisher", "Publisher name", "Publisher"),
    ("Imprint", "string", None, "Publisher imprint", "Imprint"),
    ("Genre", "string", None, "Genre(s) (comma-separated)", "Genres"),
    ("Tags", "string", "tags", "Tags / Keywords (comma-separated)", "Tags"),
    ("Web", "string", "identifier:url", "Web link or URL", "Web Links / CBL Matching"),
    ("PageCount", "int", None, "Total page count", "Length (aggregated on series)"),
    ("LanguageISO", "string", "languages", "ISO language code (e.g. en, ja, fr)", "Language"),
    ("Format", "string", None, "Format (e.g. TPB, Annual, Special)", "Special (triggers Special behavior)"),
    ("BlackAndWhite", "enum_yesno", None, "Black & White (Yes, No, Unknown)", "Black and White flag"),
    ("Manga", "enum_manga", None, "Manga reading order (Yes, YesAndRightToLeft, No)", "Manga reading mode"),
    ("Characters", "string", None, "Characters present (comma-separated)", "Characters"),
    ("Teams", "string", None, "Teams present (comma-separated)", "Teams"),
    ("Locations", "string", None, "Locations present (comma-separated)", "Locations"),
    ("ScanInformation", "string", None, "Scan / digitizer information", "Scan Information"),
    ("StoryArc", "string", None, "Story Arc name", "Reading Lists"),
    ("StoryArcNumber", "string", None, "Story Arc issue number", "Reading Lists"),
    ("SeriesGroup", "string", None, "Series Group / Collections (comma-separated)", "Collections"),
    ("AgeRating", "enum_agerating", None, "Age Rating", "Age Rating (highest used for series)"),
    ("CommunityRating", "decimal", "rating", "Community Rating (0.0 - 5.0)", "User/Community Rating"),
    ("MainCharacterOrTeam", "string", None, "Main Character or Team", "Main Character/Team"),
    ("Review", "string", None, "Review or commentary", "Review"),
    ("GTIN", "string", "identifier:isbn", "GTIN / ISBN / Barcode", "ISBN"),
    # Kavita-specific extensions
    ("LocalizedSeries", "string", None, "Localized series name", "Localized Name (searching/grouping)"),
    ("SeriesSort", "string", "series_sort", "Sort title for series", "Name sorting (preferred over Series)"),
]

# Quick lookup by tag name
COMICINFO_TAG_MAP = {tag[0]: tag for tag in COMICINFO_TAG_DEFS}

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
