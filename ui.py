#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
UI InterfaceAction for the ComicInfo Writer plugin.
Adds toolbar button, context menu item, batch processing progress dialog,
and configuration launcher.
"""

import traceback

from calibre.gui2 import info_dialog, error_dialog, question_dialog
from calibre.gui2.actions import InterfaceAction

try:
    from qt.core import (
        QMenu,
        QAction,
        QProgressDialog,
        QCoreApplication,
        Qt,
        QIcon,
        QPixmap,
        QPainter,
        QColor,
        QFont,
    )
except ImportError:
    from PyQt6.QtWidgets import (
        QMenu,
        QProgressDialog,
    )
    from PyQt6.QtGui import (
        QAction,
        QIcon,
        QPixmap,
        QPainter,
        QColor,
        QFont,
    )
    from PyQt6.QtCore import (
        QCoreApplication,
        Qt,
    )

try:
    from calibre_plugins.comicinfo_writer.config import (
        get_pref,
        get_tag_mappings,
    )
    from calibre_plugins.comicinfo_writer.comic_processor import (
        extract_comicinfo_data,
        generate_comicinfo_xml,
        embed_into_cbz,
        convert_cbr_to_cbz,
        find_comicinfo_in_cbz,
        parse_comicinfo_xml,
        apply_comicinfo_to_calibre_metadata,
        remove_comicinfo_from_cbz,
    )
    from calibre_plugins.comicinfo_writer.config_dialog import ConfigDialog
except ImportError:
    from config import (
        get_pref,
        get_tag_mappings,
    )
    from comic_processor import (
        extract_comicinfo_data,
        generate_comicinfo_xml,
        embed_into_cbz,
        convert_cbr_to_cbz,
        find_comicinfo_in_cbz,
        parse_comicinfo_xml,
        apply_comicinfo_to_calibre_metadata,
        remove_comicinfo_from_cbz,
    )
    from config_dialog import ConfigDialog


def create_fallback_icon():
    """Create a high-contrast comic-book icon pixmap if no image is bundled."""
    pixmap = QPixmap(64, 64)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    # Draw comic book cover background
    painter.setBrush(QColor("#2b5c8f"))
    painter.setPen(QColor("#1a3c61"))
    painter.drawRoundedRect(8, 6, 48, 52, 4, 4)

    # Draw comic spine
    painter.setBrush(QColor("#e67e22"))
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawRect(8, 6, 8, 52)

    # Draw comic info label
    painter.setPen(QColor("#ffffff"))
    font = QFont("Helvetica", 9, QFont.Weight.Bold)
    painter.setFont(font)
    painter.drawText(20, 24, "XML")

    painter.setBrush(QColor("#27ae60"))
    painter.drawRoundedRect(18, 32, 34, 18, 2, 2)
    font_small = QFont("Helvetica", 7, QFont.Weight.Bold)
    painter.setFont(font_small)
    painter.setPen(QColor("#ffffff"))
    painter.drawText(20, 45, "COMIC")

    painter.end()
    return QIcon(pixmap)


class ComicInfoWriterAction(InterfaceAction):
    name = "ComicInfo Writer"
    action_spec = (
        "ComicInfo Writer",
        None,
        "Write ComicInfo.xml metadata into selected comic books (CBZ/CBR)",
        None,
    )
    action_type = "current"

    def genesis(self):
        # Set icon
        icon = None
        try:
            icon = get_icons("images/icon.png")
        except Exception:
            pass
        if not icon or icon.isNull():
            icon = create_fallback_icon()
        self.qaction.setIcon(icon)

        # Main action triggered
        self.qaction.triggered.connect(self.write_comicinfo_selected)

        # Dropdown / sub-actions menu
        self.menu = QMenu(self.gui)
        self.qaction.setMenu(self.menu)

        act_write = self.menu.addAction("Write ComicInfo.xml into Selected Books")
        act_write.setIcon(icon)
        act_write.triggered.connect(self.write_comicinfo_selected)

        act_import = self.menu.addAction("Import Metadata from ComicInfo.xml into Calibre")
        act_import.triggered.connect(self.import_comicinfo_selected)

        act_remove = self.menu.addAction("Remove ComicInfo.xml from Selected Books")
        act_remove.triggered.connect(self.remove_comicinfo_selected)

        self.menu.addSeparator()

        act_config = self.menu.addAction("Configure Plugin & Field Mappings...")
        act_config.triggered.connect(self.show_configuration)

    def gui_layout_complete(self):
        # Enable / disable action based on book selection
        pass

    def show_configuration(self):
        """Open the plugin settings dialog."""
        db = getattr(self.gui, "current_db", None)
        dlg = ConfigDialog(self.gui, db=db)
        dlg.exec()

    def _get_selected_book_ids(self):
        """Return selected book IDs or show an info dialog if none are selected."""
        rows = self.gui.library_view.selectionModel().selectedRows()
        if not rows:
            info_dialog(
                self.gui,
                "No Books Selected",
                "Please select at least one comic book in your library.",
                show=True,
            )
            return []
        return self.gui.library_view.get_selected_ids() or []

    def _create_progress_dialog(self, title, initial_label, total_books):
        """Create and initialize a modal QProgressDialog for batch operations."""
        progress = QProgressDialog(
            initial_label,
            "Cancel",
            0,
            total_books,
            self.gui,
        )
        progress.setWindowTitle(title)
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.setMinimumDuration(0)
        progress.setValue(0)
        return progress

    def _show_summary_dialog(self, title_ok, title_err, header_lines, skipped, errors):
        """Format a batch operation report and display an info or error dialog."""
        report = list(header_lines)
        if skipped:
            report.append(f"\nSkipped ({len(skipped)}):")
            report.extend(skipped[:10])
            if len(skipped) > 10:
                report.append(f"... and {len(skipped) - 10} more.")
        if errors:
            report.append(f"\nErrors ({len(errors)}):")
            report.extend(errors[:5])

        dialog_fn = error_dialog if errors else info_dialog
        dialog_title = title_err if errors else title_ok
        dialog_fn(self.gui, dialog_title, "\n".join(report), show=True)

    def write_comicinfo_selected(self):
        """Process all selected books in the active library."""
        book_ids = self._get_selected_book_ids()
        total_books = len(book_ids)
        if total_books == 0:
            return

        db = self.gui.current_db
        mappings = get_tag_mappings()
        unmapped_tags = {tag for tag, fld in mappings.items() if not fld}
        options = {
            "series_index_as_int": get_pref("series_index_as_int", True),
            "merge_existing_comicinfo": get_pref("merge_existing_comicinfo", True),
            "strip_html_comments": get_pref("strip_html_comments", True),
            "convert_cbr_to_cbz": get_pref("convert_cbr_to_cbz", False),
        }

        progress = self._create_progress_dialog(
            "ComicInfo Writer", "Writing ComicInfo.xml...", total_books
        )

        success_count = 0
        converted_count = 0
        skipped_no_comic = []
        errors = []

        for i, book_id in enumerate(book_ids):
            if progress.wasCanceled():
                break

            book_title = f"Book ID {book_id}"
            try:
                mi = db.new_api.get_metadata(book_id)
                book_title = mi.title or book_title
                progress.setLabelText(f"Processing ({i+1}/{total_books}): {book_title}")
                QCoreApplication.processEvents()

                has_cbz = db.has_format(book_id, "CBZ", index_is_id=True)
                has_cbr = db.has_format(book_id, "CBR", index_is_id=True)

                if not has_cbz and not has_cbr:
                    skipped_no_comic.append(f"• {book_title} (no CBZ or CBR format)")
                    progress.setValue(i + 1)
                    continue

                # Extract metadata according to mappings
                data = extract_comicinfo_data(mi, mappings=mappings, options=options)
                xml_bytes = generate_comicinfo_xml(data, unmapped_tags=unmapped_tags)

                if has_cbz:
                    cbz_path = db.format_abspath(book_id, "CBZ", index_is_id=True)
                    embed_into_cbz(
                        cbz_path,
                        xml_bytes,
                        merge=options.get("merge_existing_comicinfo", True),
                        unmapped_tags=unmapped_tags,
                    )
                    success_count += 1

                elif has_cbr:
                    if options.get("convert_cbr_to_cbz", False):
                        cbr_path = db.format_abspath(book_id, "CBR", index_is_id=True)
                        new_cbz_path = convert_cbr_to_cbz(
                            cbr_path,
                            xml_bytes,
                            merge=options.get("merge_existing_comicinfo", True),
                            unmapped_tags=unmapped_tags,
                        )
                        # Add newly created CBZ to Calibre database
                        with open(new_cbz_path, "rb") as f_cbz:
                            db.new_api.add_format(
                                book_id, "CBZ", f_cbz, run_hooks=False
                            )
                        success_count += 1
                        converted_count += 1
                    else:
                        skipped_no_comic.append(
                            f"• {book_title} (CBR format: enable CBR-to-CBZ conversion in settings to embed)"
                        )

            except Exception as e:
                errors.append(f"{book_title}: {e}")
                traceback.print_exc()

            progress.setValue(i + 1)

        progress.close()

        header_lines = [f"Successfully updated: {success_count} book(s)"]
        if converted_count > 0:
            header_lines.append(f"Converted from CBR to CBZ: {converted_count} book(s)")

        self._show_summary_dialog(
            "ComicInfo Writing Complete",
            "Writing Finished with Warnings",
            header_lines,
            skipped_no_comic,
            errors,
        )

    # Backward compatibility alias
    embed_comicinfo_selected = write_comicinfo_selected

    def import_comicinfo_selected(self):
        """Read ComicInfo.xml from selected books (root or nested) and update Calibre metadata."""
        book_ids = self._get_selected_book_ids()
        total_books = len(book_ids)
        if total_books == 0:
            return

        db = self.gui.current_db
        mappings = get_tag_mappings()

        progress = self._create_progress_dialog(
            "Import ComicInfo.xml Metadata",
            "Reading ComicInfo.xml metadata...",
            total_books,
        )

        success_count = 0
        updated_ids = []
        skipped = []
        errors = []

        for i, book_id in enumerate(book_ids):
            if progress.wasCanceled():
                break

            book_title = f"Book ID {book_id}"
            try:
                mi = db.new_api.get_metadata(book_id)
                book_title = mi.title or book_title
                progress.setLabelText(f"Reading ({i+1}/{total_books}): {book_title}")
                QCoreApplication.processEvents()

                if not db.has_format(book_id, "CBZ", index_is_id=True):
                    skipped.append(f"• {book_title} (no CBZ format)")
                    progress.setValue(i + 1)
                    continue

                cbz_path = db.format_abspath(book_id, "CBZ", index_is_id=True)
                xml_bytes, _found_path = find_comicinfo_in_cbz(cbz_path)
                if not xml_bytes:
                    skipped.append(f"• {book_title} (no ComicInfo.xml found)")
                    progress.setValue(i + 1)
                    continue

                parsed_tags = parse_comicinfo_xml(xml_bytes)
                if not parsed_tags:
                    skipped.append(f"• {book_title} (empty or invalid ComicInfo.xml)")
                    progress.setValue(i + 1)
                    continue

                # Apply tags to Calibre metadata
                apply_comicinfo_to_calibre_metadata(mi, parsed_tags, mappings=mappings)
                db.new_api.set_metadata(book_id, mi)
                updated_ids.append(book_id)
                success_count += 1

            except Exception as e:
                errors.append(f"{book_title}: {e}")
                traceback.print_exc()

            progress.setValue(i + 1)

        progress.close()

        if updated_ids:
            self.gui.library_view.model().refresh_ids(updated_ids)

        self._show_summary_dialog(
            "Import Complete",
            "Import Finished with Warnings",
            [f"Successfully updated metadata for {success_count} book(s)."],
            skipped,
            errors,
        )

    def remove_comicinfo_selected(self):
        """Remove all ComicInfo.xml files (root and nested) from selected books' archives."""
        book_ids = self._get_selected_book_ids()
        total_books = len(book_ids)
        if total_books == 0:
            return

        if not question_dialog(
            self.gui,
            "Remove ComicInfo.xml",
            f"Are you sure you want to remove all ComicInfo.xml files (including any nested in subdirectories) from the {total_books} selected book(s)?",
        ):
            return

        db = self.gui.current_db
        progress = self._create_progress_dialog(
            "Remove ComicInfo.xml", "Removing ComicInfo.xml...", total_books
        )

        success_count = 0
        total_removed_files = 0
        skipped = []
        errors = []

        for i, book_id in enumerate(book_ids):
            if progress.wasCanceled():
                break

            book_title = f"Book ID {book_id}"
            try:
                mi = db.new_api.get_metadata(book_id)
                book_title = mi.title or book_title
                progress.setLabelText(f"Cleaning ({i+1}/{total_books}): {book_title}")
                QCoreApplication.processEvents()

                if not db.has_format(book_id, "CBZ", index_is_id=True):
                    skipped.append(f"• {book_title} (no CBZ format)")
                    progress.setValue(i + 1)
                    continue

                cbz_path = db.format_abspath(book_id, "CBZ", index_is_id=True)
                removed, count = remove_comicinfo_from_cbz(cbz_path)
                if removed:
                    success_count += 1
                    total_removed_files += count
                else:
                    skipped.append(f"• {book_title} (no ComicInfo.xml to remove)")

            except Exception as e:
                errors.append(f"{book_title}: {e}")
                traceback.print_exc()

            progress.setValue(i + 1)

        progress.close()

        self._show_summary_dialog(
            "Removal Complete",
            "Removal Finished with Warnings",
            [f"Cleaned {success_count} book(s) (removed {total_removed_files} ComicInfo.xml file(s))."],
            skipped,
            errors,
        )


# Backward compatibility alias
EmbedComicInfoAction = ComicInfoWriterAction

