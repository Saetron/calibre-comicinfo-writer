#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Unit tests for field mapper and custom column resolution.
"""

import sys
import os
import unittest
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from comic_processor import (
    extract_field_value,
    convert_value_for_tag,
    extract_comicinfo_data,
    normalize_enum_value,
    normalize_iso_language,
)
try:
    from comicinfo_constants import AGE_RATINGS, MANGA_VALUES, YES_NO_VALUES
except ImportError:
    from kavita_constants import AGE_RATINGS, MANGA_VALUES, YES_NO_VALUES


class MockCalibreMetadata:
    def __init__(self):
        self.title = "One Piece"
        self.series = "One Piece"
        self.series_index = 100.0
        self.pubdate = datetime(1997, 7, 22)
        self.authors = ["Eiichiro Oda"]
        self.tags = ["Pirates", "Action", "Adventure"]
        self.rating = 4.8
        self.comments = "Monkey D. Luffy sets out to find the legendary treasure One Piece."
        self.languages = ["jpn"]
        self.identifiers = {"isbn": "9781569319017", "uri": "https://en.wikipedia.org/wiki/One_Piece"}
        self.user_metadata = {
            "#manga": {"#value#": "YesAndRightToLeft", "datatype": "enumeration"},
            "#volume": {"#value#": 100, "datatype": "int"},
            "#count": {"#value#": 105, "datatype": "int"},
            "#status": {"#value#": "Ongoing", "datatype": "text"},
            "#age_rating": {"#value#": "Teen", "datatype": "enumeration"},
            "#series_group": {"#value#": "Shonen Jump, Best of Manga", "datatype": "text"},
            "#story_arc": {"#value#": "Wano Country", "datatype": "text"},
            "#bw": {"#value#": True, "datatype": "bool"},
            "#page_count": {"#value#": 208, "datatype": "int"},
            "#format": {"#value#": "Tankobon", "datatype": "text"},
            "#localized_series": {"#value#": "ワンピース", "datatype": "text"},
            "#series_sort": {"#value#": "One Piece", "datatype": "text"},
        }

    def get(self, key):
        if key in self.user_metadata:
            return self.user_metadata[key]["#value#"]
        return getattr(self, key, None)

    def get_all_user_metadata(self, make_copy=False):
        return self.user_metadata

    def get_identifiers(self):
        return self.identifiers


class TestFieldMapper(unittest.TestCase):

    def setUp(self):
        self.mi = MockCalibreMetadata()

    def test_extract_date_parts(self):
        year = extract_field_value(self.mi, "pubdate:year")
        month = extract_field_value(self.mi, "pubdate:month")
        day = extract_field_value(self.mi, "pubdate:day")
        self.assertEqual(year, 1997)
        self.assertEqual(month, 7)
        self.assertEqual(day, 22)

    def test_extract_identifiers(self):
        isbn = extract_field_value(self.mi, "identifier:isbn")
        uri = extract_field_value(self.mi, "identifier:uri")
        self.assertEqual(isbn, "9781569319017")
        self.assertEqual(uri, "https://en.wikipedia.org/wiki/One_Piece")

    def test_extract_custom_columns(self):
        manga = extract_field_value(self.mi, "#manga")
        volume = extract_field_value(self.mi, "#volume")
        count = extract_field_value(self.mi, "#count")
        age = extract_field_value(self.mi, "#age_rating")
        group = extract_field_value(self.mi, "#series_group")
        arc = extract_field_value(self.mi, "#story_arc")
        bw = extract_field_value(self.mi, "#bw")
        pages = extract_field_value(self.mi, "#page_count")
        loc_series = extract_field_value(self.mi, "#localized_series")

        self.assertEqual(manga, "YesAndRightToLeft")
        self.assertEqual(volume, 100)
        self.assertEqual(count, 105)
        self.assertEqual(age, "Teen")
        self.assertEqual(group, "Shonen Jump, Best of Manga")
        self.assertEqual(arc, "Wano Country")
        self.assertEqual(bw, True)
        self.assertEqual(pages, 208)
        self.assertEqual(loc_series, "ワンピース")

    def test_conversions_and_enums(self):
        options = {"write_series_index": True, "series_index_as_int": True, "strip_html_comments": True}

        # AgeRating enum validation
        self.assertEqual(convert_value_for_tag("Teen", "AgeRating", "enum_agerating", options), "Teen")
        self.assertEqual(convert_value_for_tag("mature", "AgeRating", "enum_agerating", options), "Mature 17+")
        self.assertEqual(convert_value_for_tag("kids", "AgeRating", "enum_agerating", options), "Kids to Adults")

        # Manga enum validation
        self.assertEqual(convert_value_for_tag(True, "Manga", "enum_manga", options), "Yes")
        self.assertEqual(convert_value_for_tag("YesAndRightToLeft", "Manga", "enum_manga", options), "YesAndRightToLeft")

        # BlackAndWhite enum validation
        self.assertEqual(convert_value_for_tag(True, "BlackAndWhite", "enum_yesno", options), "Yes")
        self.assertEqual(convert_value_for_tag(False, "BlackAndWhite", "enum_yesno", options), "No")

        # CommunityRating 0-5 decimal
        self.assertEqual(convert_value_for_tag(4.75, "CommunityRating", "decimal", options), 4.8)
        self.assertEqual(convert_value_for_tag(9.0, "CommunityRating", "decimal", options), 4.5)  # 10 pt scale scaled down

        # LanguageISO: Calibre 3-letter / alias to ISO 639-1 (2-letter)
        self.assertEqual(convert_value_for_tag("eng", "LanguageISO", "string", options), "en")
        self.assertEqual(convert_value_for_tag("deu", "LanguageISO", "string", options), "de")
        self.assertEqual(convert_value_for_tag("jpn", "LanguageISO", "string", options), "ja")
        self.assertEqual(convert_value_for_tag("jp", "LanguageISO", "string", options), "ja")
        self.assertEqual(convert_value_for_tag("fra", "LanguageISO", "string", options), "fr")
        self.assertEqual(convert_value_for_tag("spa", "LanguageISO", "string", options), "es")
        self.assertEqual(convert_value_for_tag("en-US", "LanguageISO", "string", options), "en")
        self.assertEqual(convert_value_for_tag(["jpn"], "LanguageISO", "string", options), "ja")

    def test_normalize_iso_language(self):
        # 3-letter to 2-letter ISO 639-1
        self.assertEqual(normalize_iso_language("eng"), "en")
        self.assertEqual(normalize_iso_language("deu"), "de")
        self.assertEqual(normalize_iso_language("ger"), "de")
        self.assertEqual(normalize_iso_language("jpn"), "ja")
        self.assertEqual(normalize_iso_language("jp"), "ja")
        self.assertEqual(normalize_iso_language("fra"), "fr")
        self.assertEqual(normalize_iso_language("fre"), "fr")
        self.assertEqual(normalize_iso_language("spa"), "es")
        self.assertEqual(normalize_iso_language("ita"), "it")
        self.assertEqual(normalize_iso_language("zho"), "zh")
        self.assertEqual(normalize_iso_language("chi"), "zh")
        self.assertEqual(normalize_iso_language("kor"), "ko")
        self.assertEqual(normalize_iso_language("rus"), "ru")
        self.assertEqual(normalize_iso_language("por"), "pt")
        # With locales / regions
        self.assertEqual(normalize_iso_language("en-US"), "en")
        self.assertEqual(normalize_iso_language("en_GB"), "en")
        self.assertEqual(normalize_iso_language("de-DE"), "de")
        self.assertEqual(normalize_iso_language("ja-JP"), "ja")
        # Full English names
        self.assertEqual(normalize_iso_language("English"), "en")
        self.assertEqual(normalize_iso_language("German"), "de")
        self.assertEqual(normalize_iso_language("Japanese"), "ja")
        # None / empty
        self.assertEqual(normalize_iso_language(None), "")
        self.assertEqual(normalize_iso_language(""), "")

    def test_full_extraction_with_custom_mappings(self):
        custom_mappings = {
            "Title": "title",
            "Series": "series",
            "Number": "series_index",
            "LanguageISO": "languages",
            "Year": "pubdate:year",
            "Month": "pubdate:month",
            "Day": "pubdate:day",
            "Volume": "#volume",
            "Count": "#count",
            "Manga": "#manga",
            "BlackAndWhite": "#bw",
            "AgeRating": "#age_rating",
            "SeriesGroup": "#series_group",
            "StoryArc": "#story_arc",
            "PageCount": "#page_count",
            "GTIN": "identifier:isbn",
            "Web": "identifier:uri",
            "LocalizedSeries": "#localized_series",
            "SeriesSort": "#series_sort",
        }
        options = {"write_series_index": True, "series_index_as_int": True, "strip_html_comments": True}

        data = extract_comicinfo_data(self.mi, mappings=custom_mappings, options=options)

        self.assertEqual(data["Title"], "One Piece")
        self.assertEqual(data["Series"], "One Piece")
        self.assertEqual(data["Number"], "100")
        self.assertEqual(data["LanguageISO"], "ja")
        self.assertEqual(data["Volume"], "100")
        self.assertEqual(data["Count"], 105)
        self.assertEqual(data["Year"], 1997)
        self.assertEqual(data["Month"], 7)
        self.assertEqual(data["Day"], 22)
        self.assertEqual(data["Manga"], "YesAndRightToLeft")
        self.assertEqual(data["BlackAndWhite"], "Yes")
        self.assertEqual(data["AgeRating"], "Teen")
        self.assertEqual(data["SeriesGroup"], "Shonen Jump, Best of Manga")
        self.assertEqual(data["StoryArc"], "Wano Country")
        self.assertEqual(data["PageCount"], 208)
        self.assertEqual(data["GTIN"], "9781569319017")
        self.assertEqual(data["Web"], "https://en.wikipedia.org/wiki/One_Piece")
        self.assertEqual(data["LocalizedSeries"], "ワンピース")
        self.assertEqual(data["SeriesSort"], "One Piece")


if __name__ == "__main__":
    unittest.main()
