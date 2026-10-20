#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Build script to package the ComicInfo Writer Calibre plugin into a distributable .zip file.
"""

import os
import zipfile

OUTPUT_ZIP = "ComicInfoWriter.zip"

FILES_TO_INCLUDE = [
    ("__init__.py", "__init__.py"),
    ("ui.py", "ui.py"),
    ("config.py", "config.py"),
    ("config_dialog.py", "config_dialog.py"),
    ("comic_processor.py", "comic_processor.py"),
    ("comicinfo_constants.py", "comicinfo_constants.py"),
    ("kavita_constants.py", "kavita_constants.py"),
    ("plugin-import-name-comicinfo_writer.txt", "plugin-import-name-comicinfo_writer.txt"),
    ("images/icon.png", "images/icon.png"),
]


def build_plugin(output_path=OUTPUT_ZIP):
    """Package the plugin into a zip archive."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    zip_full_path = os.path.join(base_dir, output_path)

    print(f"Building Calibre plugin: {output_path}...")
    with zipfile.ZipFile(zip_full_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for src_rel, arc_rel in FILES_TO_INCLUDE:
            src_full = os.path.join(base_dir, src_rel)
            if os.path.exists(src_full):
                zf.write(src_full, arc_rel)
                print(f"  + Added {arc_rel}")
            else:
                print(f"  ! Warning: {src_rel} not found!")

    size_bytes = os.path.getsize(zip_full_path)
    print(f"\nPlugin package created successfully: {zip_full_path} ({size_bytes:,} bytes)")
    return zip_full_path


if __name__ == "__main__":
    build_plugin()
