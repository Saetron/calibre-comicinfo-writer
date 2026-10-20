#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Configuration dialog and widget for the ComicInfo Writer plugin.
Provides user options for Series Index omission, archive handling,
and full mapping of custom Calibre fields to ComicInfo v2.1/Kavita tags.
"""

import copy

try:
    from qt.core import (
        QDialog,
        QWidget,
        QVBoxLayout,
        QHBoxLayout,
        QTabWidget,
        QCheckBox,
        QLabel,
        QComboBox,
        QTableWidget,
        QTableWidgetItem,
        QPushButton,
        QHeaderView,
        QMessageBox,
        QGroupBox,
        QLineEdit,
        QTextBrowser,
        Qt,
    )
except ImportError:
    from PyQt6.QtWidgets import (
        QDialog,
        QWidget,
        QVBoxLayout,
        QHBoxLayout,
        QTabWidget,
        QCheckBox,
        QLabel,
        QComboBox,
        QTableWidget,
        QTableWidgetItem,
        QPushButton,
        QHeaderView,
        QMessageBox,
        QGroupBox,
        QLineEdit,
        QTextBrowser,
    )
    from PyQt6.QtCore import Qt

try:
    from calibre_plugins.comicinfo_writer.kavita_constants import (
        COMICINFO_TAG_DEFS,
        CALIBRE_STANDARD_FIELDS,
    )
    from calibre_plugins.comicinfo_writer.config import (
        get_pref,
        set_pref,
        get_tag_mappings,
        set_tag_mappings,
        reset_to_defaults,
        DEFAULT_CONFIG,
    )
except ImportError:
    from kavita_constants import (
        COMICINFO_TAG_DEFS,
        CALIBRE_STANDARD_FIELDS,
    )
    from config import (
        get_pref,
        set_pref,
        get_tag_mappings,
        set_tag_mappings,
        reset_to_defaults,
        DEFAULT_CONFIG,
    )


def get_available_fields_from_db(db=None):
    """
    Retrieve list of (Display Name, field_key) available for mapping.
    Includes all Calibre standard fields plus all custom columns (#...).
    """
    fields = list(CALIBRE_STANDARD_FIELDS)

    # If db is not provided, attempt to get active Calibre GUI library db
    if db is None:
        try:
            from calibre.gui2.ui import get_gui
            gui = get_gui()
            if gui and hasattr(gui, "current_db"):
                db = gui.current_db
        except Exception:
            pass

    custom_fields = []
    if db is not None:
        try:
            # Calibre custom column mapping
            if hasattr(db, "field_metadata"):
                custom_meta = db.field_metadata.custom_field_metadata()
                for key, meta in sorted(custom_meta.items(), key=lambda x: x[1].get("name", x[0])):
                    name = meta.get("name", key)
                    datatype = meta.get("datatype", "text")
                    custom_fields.append((f"{name} ({key}) [{datatype}]", key))
            elif hasattr(db, "custom_column_label_map"):
                for label, info in sorted(db.custom_column_label_map.items()):
                    key = f"#{label}"
                    name = info[0] if info else label
                    datatype = info[1] if len(info) > 1 else "text"
                    custom_fields.append((f"{name} ({key}) [{datatype}]", key))
        except Exception:
            pass

    # If no custom fields found from DB, check if existing config has custom fields
    if not custom_fields:
        existing_mappings = get_tag_mappings()
        known_standard = {f[1] for f in CALIBRE_STANDARD_FIELDS}
        for field_key in existing_mappings.values():
            if field_key and field_key.startswith("#") and field_key not in known_standard:
                custom_fields.append((f"Custom Column ({field_key})", field_key))

    return fields + custom_fields


class ConfigWidget(QWidget):
    """
    Main configuration widget embedded in Calibre Preferences or standalone dialog.
    """

    def __init__(self, parent=None, db=None):
        super().__init__(parent)
        self.db = db
        self.available_fields = get_available_fields_from_db(self.db)
        self.combo_widgets = {}  # tag_name -> QComboBox

        self.init_ui()
        self.load_settings()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        self.tabs = QTabWidget(self)
        main_layout.addWidget(self.tabs)

        # Tab 1: General Options
        tab_general = QWidget()
        self.init_general_tab(tab_general)
        self.tabs.addTab(tab_general, "General Options")

        # Tab 2: Tag & Custom Field Mappings
        tab_mappings = QWidget()
        self.init_mappings_tab(tab_mappings)
        self.tabs.addTab(tab_mappings, "Field Mappings (Calibre → ComicInfo)")

        # Tab 3: Kavita Guide & Reference
        tab_kavita = QWidget()
        self.init_kavita_tab(tab_kavita)
        self.tabs.addTab(tab_kavita, "Kavita Guide")

    def init_general_tab(self, parent_widget):
        layout = QVBoxLayout(parent_widget)

        # Group: Series Index / Number
        gb_series = QGroupBox("Series Index (<Number> tag)", parent_widget)
        series_layout = QVBoxLayout(gb_series)

        info_lbl = QLabel(
            "Note: To omit writing the issue number (<Number>), map the 'Number' tag to (None) in the Field Mappings tab.",
            gb_series,
        )
        info_lbl.setWordWrap(True)
        info_lbl.setStyleSheet("color: #666; font-style: italic;")
        series_layout.addWidget(info_lbl)

        self.cb_series_index_as_int = QCheckBox(
            "Format whole Series Index numbers as integers (e.g. 1 instead of 1.0)",
            gb_series,
        )
        self.cb_series_index_as_int.setToolTip(
            "Removes trailing .0 from series numbers so issue 1.0 appears as 1."
        )
        series_layout.addWidget(self.cb_series_index_as_int)

        layout.addWidget(gb_series)

        # Group: Comic Archive & Merging
        gb_archive = QGroupBox("Comic Archive Handling", parent_widget)
        archive_layout = QVBoxLayout(gb_archive)

        self.cb_merge_existing = QCheckBox(
            "Merge with existing ComicInfo.xml inside the archive", gb_archive
        )
        self.cb_merge_existing.setToolTip(
            "If the CBZ already has a ComicInfo.xml, preserves existing tags\n"
            "such as page layout information (<Pages>) and unmapped metadata."
        )
        archive_layout.addWidget(self.cb_merge_existing)

        self.cb_strip_html = QCheckBox(
            "Strip HTML tags from Summary / Comments", gb_archive
        )
        self.cb_strip_html.setToolTip(
            "Converts Calibre HTML comments into clean plain text for <Summary>."
        )
        archive_layout.addWidget(self.cb_strip_html)

        self.cb_convert_cbr = QCheckBox(
            "Convert CBR (RAR archives) to CBZ format when embedding", gb_archive
        )
        self.cb_convert_cbr.setToolTip(
            "CBR archives cannot be modified in-place because RAR compression is proprietary.\n"
            "Checking this will unpack the CBR and re-package it as a CBZ with ComicInfo.xml."
        )
        archive_layout.addWidget(self.cb_convert_cbr)

        layout.addWidget(gb_archive)
        layout.addStretch(1)

    def init_mappings_tab(self, parent_widget):
        layout = QVBoxLayout(parent_widget)

        # Top Bar: Filter & Quick Action Buttons
        top_bar = QHBoxLayout()
        top_bar.addWidget(QLabel("Filter Tags:", parent_widget))
        self.filter_edit = QLineEdit(parent_widget)
        self.filter_edit.setPlaceholderText("Type to filter tags (e.g. writer, manga, series)...")
        self.filter_edit.textChanged.connect(self.filter_tags_table)
        top_bar.addWidget(self.filter_edit)

        self.btn_autodetect = QPushButton("Auto-detect Matching Columns", parent_widget)
        self.btn_autodetect.setToolTip(
            "Automatically matches Calibre custom columns (e.g. #writer, #volume, #manga) to tags"
        )
        self.btn_autodetect.clicked.connect(self.autodetect_mappings)
        top_bar.addWidget(self.btn_autodetect)

        self.btn_reset_mappings = QPushButton("Reset to Defaults", parent_widget)
        self.btn_reset_mappings.clicked.connect(self.reset_mappings_to_defaults)
        top_bar.addWidget(self.btn_reset_mappings)

        layout.addLayout(top_bar)

        # Table of Mappings
        self.table = QTableWidget(parent_widget)
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels([
            "ComicInfo Tag",
            "Data Type",
            "Kavita Role / Specification",
            "Mapped Calibre Field / Custom Column",
        ])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.table.setRowCount(len(COMICINFO_TAG_DEFS))

        for row, (tag_name, tag_type, _default, _desc, kavita_desc) in enumerate(COMICINFO_TAG_DEFS):
            # Column 0: Tag Name
            item_tag = QTableWidgetItem(tag_name)
            item_tag.setFlags(item_tag.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 0, item_tag)

            # Column 1: Data Type
            item_type = QTableWidgetItem(tag_type)
            item_type.setFlags(item_type.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 1, item_type)

            # Column 2: Kavita / Description
            item_kavita = QTableWidgetItem(f"{kavita_desc} ({_desc})")
            item_kavita.setFlags(item_kavita.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 2, item_kavita)

            # Column 3: Calibre Field Dropdown
            combo = QComboBox(self.table)
            for disp_name, f_key in self.available_fields:
                combo.addItem(disp_name, f_key)

            self.combo_widgets[tag_name] = combo
            self.table.setCellWidget(row, 3, combo)

        layout.addWidget(self.table)

    def init_kavita_tab(self, parent_widget):
        layout = QVBoxLayout(parent_widget)
        browser = QTextBrowser(parent_widget)
        browser.setOpenExternalLinks(True)
        browser.setHtml("""
        <h3>Kavita Comic Metadata Reference</h3>
        <p>This plugin generates <code>ComicInfo.xml</code> files conforming to the
        <b>Anansi Project ComicInfo v2.1</b> draft specification and Kavita's conventions:</p>
        <ul>
          <li><b>Title:</b> Used by Kavita as the Chapter / Issue Title.</li>
          <li><b>Series & SeriesSort:</b> Kavita uses <code>&lt;SeriesSort&gt;</code> to sort the series, overriding <code>&lt;Series&gt;</code>.</li>
          <li><b>LocalizedSeries:</b> Kavita groups files with this name and the series name together, enabling searches by either name.</li>
          <li><b>Number:</b> Issue or chapter number. If disabled in General Options, this tag is omitted.</li>
          <li><b>Count:</b> Total number of issues/volumes. Kavita uses this to determine publication status (Ended if &gt;0, Completed if owned count matches).</li>
          <li><b>Volume:</b> Volume number for manga and collected comic trades.</li>
          <li><b>Format:</b> Formats like <i>Special, Annual, Anthology, TPB, Omnibus, Graphic Novel, One Shot</i> trigger Kavita's special issue handling.</li>
          <li><b>SeriesGroup:</b> Comma-separated names that automatically create/update Collections in Kavita.</li>
          <li><b>AgeRating:</b> The highest (most mature) rating among issues is applied to the Series in Kavita.</li>
          <li><b>GTIN:</b> Populates the book's ISBN in Kavita.</li>
        </ul>
        <p>For more details, see the <a href="https://wiki.kavitareader.com/guides/metadata/comics/">Kavita Comics Metadata Guide</a>.</p>
        """)
        layout.addWidget(browser)

    def filter_tags_table(self, query):
        """Filter rows in the mappings table by query string."""
        query = query.strip().lower()
        for row in range(self.table.rowCount()):
            if not query:
                self.table.setRowHidden(row, False)
                continue
            tag_name = self.table.item(row, 0).text().lower()
            tag_type = self.table.item(row, 1).text().lower()
            kavita_desc = self.table.item(row, 2).text().lower()
            match = query in tag_name or query in tag_type or query in kavita_desc
            self.table.setRowHidden(row, not match)

    def load_settings(self):
        """Load settings from persistent config into UI widgets."""
        self.cb_series_index_as_int.setChecked(get_pref("series_index_as_int", True))
        self.cb_merge_existing.setChecked(get_pref("merge_existing_comicinfo", True))
        self.cb_strip_html.setChecked(get_pref("strip_html_comments", True))
        self.cb_convert_cbr.setChecked(get_pref("convert_cbr_to_cbz", False))

        mappings = get_tag_mappings()
        for tag_name, combo in self.combo_widgets.items():
            mapped_field = mappings.get(tag_name, "")
            idx = combo.findData(mapped_field)
            if idx >= 0:
                combo.setCurrentIndex(idx)
            elif mapped_field:
                # Add custom field entry if not present in dropdown
                combo.addItem(f"Custom ({mapped_field})", mapped_field)
                combo.setCurrentIndex(combo.count() - 1)
            else:
                combo.setCurrentIndex(0)

    def save_settings(self):
        """Save UI settings to persistent config."""
        set_pref("series_index_as_int", self.cb_series_index_as_int.isChecked())
        set_pref("merge_existing_comicinfo", self.cb_merge_existing.isChecked())
        set_pref("strip_html_comments", self.cb_strip_html.isChecked())
        set_pref("convert_cbr_to_cbz", self.cb_convert_cbr.isChecked())

        mappings = {}
        for tag_name, combo in self.combo_widgets.items():
            mappings[tag_name] = combo.currentData() or ""

        set_tag_mappings(mappings)

    def autodetect_mappings(self):
        """Automatically match Calibre custom columns to ComicInfo tags."""
        matched = 0
        for tag_name, combo in self.combo_widgets.items():
            clean_tag = tag_name.lower().replace(" ", "").replace("_", "")
            for i in range(combo.count()):
                field_key = combo.itemData(i)
                if not field_key:
                    continue
                # Normalize field key (#my_field -> myfield)
                clean_field = field_key.lstrip("#").lower().replace("_", "").replace("-", "")
                if clean_field == clean_tag or clean_field in clean_tag or clean_tag in clean_field:
                    combo.setCurrentIndex(i)
                    matched += 1
                    break

        QMessageBox.information(
            self,
            "Auto-detect Complete",
            f"Auto-detection matched {matched} fields based on your library columns.",
        )

    def reset_mappings_to_defaults(self):
        """Reset field mappings to standard defaults."""
        confirm = QMessageBox.question(
            self,
            "Reset Mappings",
            "Are you sure you want to reset all field mappings to defaults?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if confirm == QMessageBox.StandardButton.Yes:
            from config import DEFAULT_TAG_MAPPINGS
            for tag_name, combo in self.combo_widgets.items():
                def_field = DEFAULT_TAG_MAPPINGS.get(tag_name, "")
                idx = combo.findData(def_field)
                if idx >= 0:
                    combo.setCurrentIndex(idx)
                else:
                    combo.setCurrentIndex(0)


class ConfigDialog(QDialog):
    """
    Standalone dialog wrapper for ConfigWidget.
    """

    def __init__(self, parent=None, db=None):
        super().__init__(parent)
        self.setWindowTitle("Configure ComicInfo Writer (Kavita)")
        self.resize(850, 600)

        layout = QVBoxLayout(self)
        self.config_widget = ConfigWidget(self, db=db)
        layout.addWidget(self.config_widget)

        btn_box = QHBoxLayout()
        btn_box.addStretch(1)

        self.btn_save = QPushButton("Save Settings", self)
        self.btn_save.setDefault(True)
        self.btn_save.clicked.connect(self.accept)
        btn_box.addWidget(self.btn_save)

        self.btn_cancel = QPushButton("Cancel", self)
        self.btn_cancel.clicked.connect(self.reject)
        btn_box.addWidget(self.btn_cancel)

        layout.addLayout(btn_box)

    def accept(self):
        self.config_widget.save_settings()
        super().accept()
