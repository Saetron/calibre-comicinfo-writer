#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Unit tests for XML generation, schema compliance, and series index toggles.
"""

import sys
import os
import unittest
import xml.etree.ElementTree as ET

# Ensure parent directory is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from comic_processor import (
    generate_comicinfo_xml,
    extract_comicinfo_data,
    strip_html_tags,
    format_series_index,
)
from kavita_constants import COMICINFO_TAG_DEFS


class MockMetadata:
    """Mock Calibre Metadata object for testing."""
    def __init__(self, title="Batman: Year One", authors=["Frank Miller", "David Mazzucchelli"]):
        self.title = title
        self.title_sort = "Batman: Year One"
        self.authors = authors
        self.author_sort = "Miller, Frank"
        self.series = "Batman"
        self.series_index = 1.0
        self.series_sort = "Batman"
        self.comments = "<p>A dark and gritty origin story of <b>The Dark Knight</b>.</p>"
        self.publisher = "DC Comics"
        self.tags = ["Superhero", "Detective", "Noir"]
        self.rating = 5.0
        self.languages = ["eng"]
        self.identifiers = {"isbn": "9780446394864", "url": "https://comicvine.gamespot.com/batman/4000-12345/"}
        self.custom_fields = {}

    def get(self, key):
        return self.custom_fields.get(key)

    def get_identifiers(self):
        return self.identifiers


class TestXMLGenerator(unittest.TestCase):

    def test_strip_html_tags(self):
        raw = "<p>First line.</p><br><div>Second line with &amp; entity.</div>"
        cleaned = strip_html_tags(raw)
        self.assertIn("First line.", cleaned)
        self.assertIn("Second line with & entity.", cleaned)
        self.assertNotIn("<p>", cleaned)
        self.assertNotIn("<div>", cleaned)
        self.assertNotIn("&amp;", cleaned)

    def test_format_series_index(self):
        self.assertEqual(format_series_index(1.0, as_int=True), "1")
        self.assertEqual(format_series_index(1.0, as_int=False), "1")
        self.assertEqual(format_series_index(1.5, as_int=True), "1.5")
        self.assertEqual(format_series_index("1-5", as_int=True), "1-5")
        self.assertEqual(format_series_index("TPB1", as_int=True), "TPB1")

    def test_series_index_omitted_when_mapped_to_none(self):
        mi = MockMetadata()
        custom_mappings = {"Title": "title", "Series": "series", "Number": ""}
        data = extract_comicinfo_data(mi, mappings=custom_mappings)
        self.assertNotIn("Number", data)

        # Even when merging with an archive that contains <Number>1</Number>,
        # unmapped Number must NOT be preserved!
        existing_xml = b"<ComicInfo><Title>Old Title</Title><Number>1</Number></ComicInfo>"
        xml_bytes = generate_comicinfo_xml(data, existing_xml_content=existing_xml, merge=True, unmapped_tags={"Number"})
        root = ET.fromstring(xml_bytes)
        self.assertIsNone(root.find("Number"))

    def test_series_index_included_when_mapped(self):
        mi = MockMetadata()
        custom_mappings = {"Title": "title", "Number": "series_index"}
        data = extract_comicinfo_data(mi, mappings=custom_mappings)
        self.assertIn("Number", data)
        self.assertEqual(data["Number"], "1")

        xml_bytes = generate_comicinfo_xml(data)
        root = ET.fromstring(xml_bytes)
        number_elem = root.find("Number")
        self.assertIsNotNone(number_elem)
        self.assertEqual(number_elem.text, "1")

    def test_volume_as_string_for_omnis(self):
        mi = MockMetadata()
        mi.custom_fields["#volume"] = "Omnibus 1"
        custom_mappings = {"Title": "title", "Volume": "#volume"}
        data = extract_comicinfo_data(mi, mappings=custom_mappings)
        self.assertEqual(data["Volume"], "Omnibus 1")

        xml_bytes = generate_comicinfo_xml(data)
        root = ET.fromstring(xml_bytes)
        self.assertEqual(root.find("Volume").text, "Omnibus 1")

    def test_custom_fields_mapping(self):
        mi = MockMetadata()
        mi.custom_fields["#writer"] = "Frank Miller"
        mi.custom_fields["#penciller"] = "David Mazzucchelli"
        mi.custom_fields["#volume"] = "Omnibus 2"
        mi.custom_fields["#manga"] = "No"
        mi.custom_fields["#age_rating"] = "Mature 17+"
        mi.custom_fields["#series_group"] = "Batman Essentials, Millerverse"
        mi.custom_fields["#localized_series"] = "Batman (JP)"

        custom_mappings = {
            "Title": "title",
            "Series": "series",
            "Number": "series_index",
            "Writer": "#writer",
            "Penciller": "#penciller",
            "Volume": "#volume",
            "Manga": "#manga",
            "AgeRating": "#age_rating",
            "SeriesGroup": "#series_group",
            "LocalizedSeries": "#localized_series",
            "GTIN": "identifier:isbn",
        }

        data = extract_comicinfo_data(mi, mappings=custom_mappings)
        self.assertEqual(data["Writer"], "Frank Miller")
        self.assertEqual(data["Penciller"], "David Mazzucchelli")
        self.assertEqual(data["Volume"], "Omnibus 2")
        self.assertEqual(data["Manga"], "No")
        self.assertEqual(data["AgeRating"], "Mature 17+")
        self.assertEqual(data["SeriesGroup"], "Batman Essentials, Millerverse")
        self.assertEqual(data["LocalizedSeries"], "Batman (JP)")
        self.assertEqual(data["GTIN"], "9780446394864")

        xml_bytes = generate_comicinfo_xml(data)
        root = ET.fromstring(xml_bytes)
        self.assertEqual(root.find("Writer").text, "Frank Miller")
        self.assertEqual(root.find("Penciller").text, "David Mazzucchelli")
        self.assertEqual(root.find("Volume").text, "Omnibus 2")
        self.assertEqual(root.find("AgeRating").text, "Mature 17+")
        self.assertEqual(root.find("LocalizedSeries").text, "Batman (JP)")

    def test_merge_preserves_pages_and_existing_tags(self):
        existing_xml = b"""<?xml version="1.0" encoding="utf-8"?>
<ComicInfo xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema">
  <Title>Old Title</Title>
  <ScanInformation>Scanned by GroupX</ScanInformation>
  <Pages>
    <Page Image="0" Type="FrontCover" DoublePage="false" ImageSize="102400" />
    <Page Image="1" Type="Story" DoublePage="false" ImageSize="204800" />
    <Page Image="2" Type="BackCover" DoublePage="false" ImageSize="90000" />
  </Pages>
</ComicInfo>
"""
        new_data = {
            "Title": "New Title",
            "Series": "Batman",
        }
        merged_bytes = generate_comicinfo_xml(new_data, existing_xml_content=existing_xml, merge=True)
        root = ET.fromstring(merged_bytes)

        # Title should be updated to "New Title"
        self.assertEqual(root.find("Title").text, "New Title")
        # Series should be added
        self.assertEqual(root.find("Series").text, "Batman")
        # ScanInformation should be preserved
        self.assertEqual(root.find("ScanInformation").text, "Scanned by GroupX")
        # Pages element should be preserved intact!
        pages = root.find("Pages")
        self.assertIsNotNone(pages)
        page_list = pages.findall("Page")
        self.assertEqual(len(page_list), 3)
        self.assertEqual(page_list[0].attrib.get("Type"), "FrontCover")

    def test_calibre_unset_date_is_not_written(self):
        from datetime import datetime
        mi = MockMetadata()
        # In Calibre, unset pubdate defaults to 0101-01-01 (Year 101, Month 1, Day 1)
        mi.pubdate = datetime(101, 1, 1)

        data = extract_comicinfo_data(mi)
        self.assertNotIn("Year", data)
        self.assertNotIn("Month", data)
        self.assertNotIn("Day", data)

        xml_bytes = generate_comicinfo_xml(data)
        root = ET.fromstring(xml_bytes)
        self.assertIsNone(root.find("Year"))
        self.assertIsNone(root.find("Month"))
        self.assertIsNone(root.find("Day"))

    def test_calibre_valid_date_is_written(self):
        from datetime import datetime
        mi = MockMetadata()
        mi.pubdate = datetime(2023, 7, 15)

        data = extract_comicinfo_data(mi)
        self.assertEqual(data.get("Year"), 2023)
        self.assertEqual(data.get("Month"), 7)
        self.assertEqual(data.get("Day"), 15)

        xml_bytes = generate_comicinfo_xml(data)
        root = ET.fromstring(xml_bytes)
        self.assertEqual(root.find("Year").text, "2023")
        self.assertEqual(root.find("Month").text, "7")
        self.assertEqual(root.find("Day").text, "15")

    def test_merge_drops_unset_date_tags(self):
        existing_xml = b"""<?xml version="1.0" encoding="utf-8"?>
<ComicInfo xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema">
  <Title>Old Title</Title>
  <Year>101</Year>
  <Month>1</Month>
  <Day>1</Day>
  <Pages>
    <Page Image="0" Type="FrontCover" />
  </Pages>
</ComicInfo>
"""
        new_data = {
            "Title": "Updated Title",
        }
        merged_bytes = generate_comicinfo_xml(new_data, existing_xml_content=existing_xml, merge=True)
        root = ET.fromstring(merged_bytes)

        # Unset date 101 must be cleaned up / dropped during merge
        self.assertIsNone(root.find("Year"))
        self.assertIsNone(root.find("Month"))
        self.assertIsNone(root.find("Day"))
        # Pages still preserved
        self.assertIsNotNone(root.find("Pages"))


if __name__ == "__main__":
    unittest.main()

