#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
ComicInfo Writer Plugin for Calibre
Writes and embeds schema-compliant ComicInfo.xml metadata into comic books (CBZ/CBR)
according to Anansi Project ComicInfo v2.0 and v2.1 specifications.
"""

from calibre.customize import InterfaceActionBase


class ComicInfoWriterPlugin(InterfaceActionBase):
    name = "ComicInfo Writer"
    description = (
        "Writes and embeds ComicInfo.xml metadata into comic books (CBZ/CBR) according to "
        "Anansi Project ComicInfo schema specifications. Supports custom field mapping "
        "and option to omit series index numbers."
    )
    supported_platforms = ["windows", "osx", "linux"]
    author = "Saetron"
    version = (1, 0, 0)
    minimum_calibre_version = (6, 0, 0)

    # Entry point for the interface action
    actual_plugin = "calibre_plugins.comicinfo_writer.ui:ComicInfoWriterAction"

    def is_customizable(self):
        return True

    def config_widget(self):
        """
        Return the configuration widget to display in Calibre Preferences -> Plugins.
        """
        from calibre_plugins.comicinfo_writer.config_dialog import ConfigWidget

        return ConfigWidget()

    def save_settings(self, config_widget):
        """
        Save settings from the configuration widget.
        """
        config_widget.save_settings()
