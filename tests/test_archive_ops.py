#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Unit tests for archive operations (CBZ read/write, embedding, merging).
"""

import sys
import os
import tempfile
import zipfile
import unittest
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from comic_processor import (
    embed_into_cbz,
    generate_comicinfo_xml,
)


class TestArchiveOps(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="cbz_test_")
        self.cbz_path = os.path.join(self.temp_dir, "test_comic.cbz")

        # Create a mock CBZ file containing 3 fake image files and an existing ComicInfo.xml
        with zipfile.ZipFile(self.cbz_path, "w") as zf:
            zf.writestr("001.jpg", b"fake image 1 content")
            zf.writestr("002.jpg", b"fake image 2 content")
            zf.writestr("003.jpg", b"fake image 3 content")
            initial_xml = b"""<?xml version="1.0" encoding="utf-8"?>
<ComicInfo xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema">
  <Title>Chapter 1</Title>
  <Series>Initial Series</Series>
  <Pages>
    <Page Image="0" Type="FrontCover" />
    <Page Image="1" Type="Story" />
    <Page Image="2" Type="Story" />
  </Pages>
</ComicInfo>
"""
            zf.writestr("ComicInfo.xml", initial_xml)

    def tearDown(self):
        if os.path.exists(self.cbz_path):
            os.remove(self.cbz_path)
        if os.path.exists(self.temp_dir):
            os.rmdir(self.temp_dir)

    def test_embed_cbz_preserves_images_and_merges_pages(self):
        # Generate new metadata to embed
        new_data = {
            "Title": "Updated Chapter 1",
            "Series": "Batman Reborn",
            "Writer": "Grant Morrison",
            "AgeRating": "Teen",
            "LocalizedSeries": "Batman: Shinsei",
        }
        xml_bytes = generate_comicinfo_xml(new_data)

        # Embed with merge=True
        success = embed_into_cbz(self.cbz_path, xml_bytes, merge=True)
        self.assertTrue(success)

        # Verify archive contents
        with zipfile.ZipFile(self.cbz_path, "r") as zf:
            file_names = zf.namelist()
            # Verify images are preserved
            self.assertIn("001.jpg", file_names)
            self.assertIn("002.jpg", file_names)
            self.assertIn("003.jpg", file_names)
            self.assertEqual(zf.read("001.jpg"), b"fake image 1 content")

            # Verify ComicInfo.xml is at root
            self.assertIn("ComicInfo.xml", file_names)
            content = zf.read("ComicInfo.xml")
            root = ET.fromstring(content)

            # Updated and new fields
            self.assertEqual(root.find("Title").text, "Updated Chapter 1")
            self.assertEqual(root.find("Series").text, "Batman Reborn")
            self.assertEqual(root.find("Writer").text, "Grant Morrison")
            self.assertEqual(root.find("AgeRating").text, "Teen")
            self.assertEqual(root.find("LocalizedSeries").text, "Batman: Shinsei")

            # Pages preserved from original archive!
            pages = root.find("Pages")
            self.assertIsNotNone(pages)
            page_list = pages.findall("Page")
            self.assertEqual(len(page_list), 3)

    def test_embed_into_archive_without_existing_comicinfo(self):
        # Create CBZ with images only (no ComicInfo.xml)
        clean_cbz = os.path.join(self.temp_dir, "no_metadata.cbz")
        with zipfile.ZipFile(clean_cbz, "w") as zf:
            zf.writestr("p1.jpg", b"page 1")

        data = {
            "Title": "One Shot",
            "Series": "Special Edition",
            "Format": "One Shot",
        }
        xml_bytes = generate_comicinfo_xml(data)
        success = embed_into_cbz(clean_cbz, xml_bytes, merge=True)
        self.assertTrue(success)

        with zipfile.ZipFile(clean_cbz, "r") as zf:
            self.assertIn("ComicInfo.xml", zf.namelist())
            root = ET.fromstring(zf.read("ComicInfo.xml"))
            self.assertEqual(root.find("Title").text, "One Shot")
            self.assertEqual(root.find("Format").text, "One Shot")

        os.remove(clean_cbz)

    def test_find_and_parse_nested_comicinfo(self):
        from comic_processor import find_comicinfo_in_cbz, parse_comicinfo_xml

        nested_cbz = os.path.join(self.temp_dir, "nested.cbz")
        with zipfile.ZipFile(nested_cbz, "w") as zf:
            zf.writestr("page1.jpg", b"image data")
            zf.writestr(
                "nested/folder/ComicInfo.xml",
                b"""<?xml version="1.0" encoding="utf-8"?>
<ComicInfo>
  <Title>Nested Chapter</Title>
  <Series>Nested Series</Series>
  <Number>42</Number>
  <Writer>Eiichiro Oda</Writer>
  <Pages>
    <Page Image="0" Type="FrontCover" />
  </Pages>
</ComicInfo>
""",
            )

        # 1. Find nested ComicInfo.xml
        xml_bytes, found_path = find_comicinfo_in_cbz(nested_cbz)
        self.assertIsNotNone(xml_bytes)
        self.assertEqual(found_path, "nested/folder/ComicInfo.xml")

        # 2. Parse existing ComicInfo.xml
        parsed = parse_comicinfo_xml(xml_bytes)
        self.assertEqual(parsed.get("Title"), "Nested Chapter")
        self.assertEqual(parsed.get("Series"), "Nested Series")
        self.assertEqual(parsed.get("Number"), "42")
        self.assertEqual(parsed.get("Writer"), "Eiichiro Oda")
        self.assertEqual(len(parsed.get("Pages", [])), 1)

        os.remove(nested_cbz)

    def test_embed_deletes_old_comicinfo_including_nested(self):
        # Archive with ComicInfo at root AND in a subfolder
        multi_cbz = os.path.join(self.temp_dir, "multi_comicinfo.cbz")
        with zipfile.ZipFile(multi_cbz, "w") as zf:
            zf.writestr("001.png", b"image data")
            zf.writestr("ComicInfo.xml", b"<ComicInfo><Title>Old Root</Title></ComicInfo>")
            zf.writestr("subfolder/comicinfo.xml", b"<ComicInfo><Title>Old Nested</Title></ComicInfo>")

        new_data = {"Title": "Brand New Clean Title", "Series": "New Series"}
        xml_bytes = generate_comicinfo_xml(new_data)

        # Embed into multi_cbz
        embed_into_cbz(multi_cbz, xml_bytes, merge=False)

        # Verify: ONLY 1 ComicInfo.xml exists and it is at the root
        with zipfile.ZipFile(multi_cbz, "r") as zf:
            all_files = zf.namelist()
            self.assertIn("001.png", all_files)
            self.assertIn("ComicInfo.xml", all_files)
            self.assertNotIn("subfolder/comicinfo.xml", all_files)

            # Ensure only 1 comicinfo file exists across the entire archive
            comicinfo_count = sum(
                1 for f in all_files if os.path.basename(f).lower() == "comicinfo.xml"
            )
            self.assertEqual(comicinfo_count, 1)

            root = ET.fromstring(zf.read("ComicInfo.xml"))
            self.assertEqual(root.find("Title").text, "Brand New Clean Title")

        os.remove(multi_cbz)

    def test_remove_comicinfo_from_cbz(self):
        from comic_processor import remove_comicinfo_from_cbz

        cbz_to_clean = os.path.join(self.temp_dir, "clean_me.cbz")
        with zipfile.ZipFile(cbz_to_clean, "w") as zf:
            zf.writestr("001.jpg", b"image data")
            zf.writestr("ComicInfo.xml", b"<ComicInfo><Title>Delete Me</Title></ComicInfo>")
            zf.writestr("inner/folder/comicinfo.xml", b"<ComicInfo><Title>Also Delete Me</Title></ComicInfo>")

        success, removed_count = remove_comicinfo_from_cbz(cbz_to_clean)
        self.assertTrue(success)
        self.assertEqual(removed_count, 2)

        with zipfile.ZipFile(cbz_to_clean, "r") as zf:
            all_files = zf.namelist()
            self.assertIn("001.jpg", all_files)
            self.assertNotIn("ComicInfo.xml", all_files)
            self.assertNotIn("inner/folder/comicinfo.xml", all_files)
            self.assertEqual(len(all_files), 1)

        os.remove(cbz_to_clean)

    def test_apply_comicinfo_to_calibre_metadata(self):
        from comic_processor import apply_comicinfo_to_calibre_metadata

        class FakeCalibreMetadata:
            def __init__(self):
                self.title = ""
                self.series = ""
                self.series_index = 1.0
                self.authors = []
                self.comments = ""
                self.publisher = ""
                self.tags = []
                self.rating = 0.0
                self.languages = []
                self.user_metadata = {
                    "#writer": {"datatype": "text"},
                    "#manga": {"datatype": "text"},
                    "#volume": {"datatype": "int"},
                }
                self.custom = {}
                self.identifiers = {}

            def set(self, key, val):
                self.custom[key] = val

            def set_identifier(self, id_type, val):
                self.identifiers[id_type] = val

        mi = FakeCalibreMetadata()
        parsed_tags = {
            "Title": "Romance Dawn",
            "Series": "One Piece",
            "Number": "1",
            "Volume": "1",
            "Writer": "Eiichiro Oda",
            "Manga": "YesAndRightToLeft",
            "Summary": "Luffy starts his journey.",
            "Publisher": "Shueisha",
            "Tags": "Pirates, Shonen",
            "Rating": "5.0",
            "LanguageISO": "ja",
            "GTIN": "9781569319017",
            "Year": "1997",
            "Month": "7",
            "Day": "22",
        }
        mappings = {
            "Title": "title",
            "Series": "series",
            "Number": "series_index",
            "Volume": "#volume",
            "Writer": "#writer",
            "Manga": "#manga",
            "Summary": "comments",
            "Publisher": "publisher",
            "Tags": "tags",
            "Rating": "rating",
            "LanguageISO": "languages",
            "GTIN": "identifier:isbn",
            "Year": "pubdate:year",
        }

        apply_comicinfo_to_calibre_metadata(mi, parsed_tags, mappings)

        self.assertEqual(mi.title, "Romance Dawn")
        self.assertEqual(mi.series, "One Piece")
        self.assertEqual(mi.series_index, 1.0)
        self.assertEqual(mi.publisher, "Shueisha")
        self.assertEqual(mi.tags, ["Pirates", "Shonen"])
        self.assertEqual(mi.rating, 5.0)
        self.assertEqual(mi.languages, ["jpn"])
        self.assertEqual(mi.identifiers.get("isbn"), "9781569319017")
        self.assertEqual(mi.custom.get("#writer"), "Eiichiro Oda")
        self.assertEqual(mi.custom.get("#volume"), 1)
        self.assertEqual(mi.custom.get("#manga"), "YesAndRightToLeft")
        self.assertIsNotNone(mi.pubdate)
        self.assertEqual(mi.pubdate.year, 1997)


if __name__ == "__main__":
    unittest.main()
