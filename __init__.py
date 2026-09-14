#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Embed ComicInfo.xml Plugin for Calibre
Embeds schema-compliant ComicInfo.xml metadata into comic books (CBZ/CBR)
according to Kavita and ComicInfo v2.1 specifications.
"""

from calibre.customize import InterfaceActionBase


class EmbedComicInfoPlugin(InterfaceActionBase):
    name = "Embed ComicInfo.xml"
    description = (
        "Embeds ComicInfo.xml metadata into comic books (CBZ/CBR) according to "
        "Kavita and ComicInfo v2.1 specifications. Supports custom field mapping "
        "and option to omit series index numbers."
    )
    supported_platforms = ["windows", "osx", "linux"]
    author = "Kavita Plugin Contributor"
    version = (1, 0, 0)
    minimum_calibre_version = (6, 0, 0)

    # Entry point for the interface action
    actual_plugin = "calibre_plugins.embed_comicinfo.ui:EmbedComicInfoAction"

    def is_customizable(self):
        return True

    def config_widget(self):
        """
        Return the configuration widget to display in Calibre Preferences -> Plugins.
        """
        from calibre_plugins.embed_comicinfo.config_dialog import ConfigWidget

        return ConfigWidget()

    def save_settings(self, config_widget):
        """
        Save settings from the configuration widget.
        """
        config_widget.save_settings()
