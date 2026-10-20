#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Configuration management for ComicInfo Writer Calibre plugin.
"""

import copy

try:
    from calibre.utils.config import JSONConfig
except ImportError:
    # Standalone mock for testing outside Calibre environment
    class JSONConfig(dict):
        def __init__(self, name):
            super().__init__()
            self.name = name

        def commit(self):
            pass

try:
    from calibre_plugins.comicinfo_writer.comicinfo_constants import COMICINFO_TAG_DEFS
except ImportError:
    try:
        from comicinfo_constants import COMICINFO_TAG_DEFS
    except ImportError:
        from kavita_constants import COMICINFO_TAG_DEFS


CONFIG_FILE_NAME = "plugins/comicinfo_writer"

# Build default tag mappings from definitions
DEFAULT_TAG_MAPPINGS = {
    tag_name: default_field or ""
    for tag_name, _type, default_field, _desc, _schema_desc in COMICINFO_TAG_DEFS
}

DEFAULT_CONFIG = {
    # Option: format series index as integer when whole (e.g. 1 instead of 1.0)
    "series_index_as_int": True,
    # Option: merge with existing ComicInfo.xml inside the archive (preserves <Pages> etc.)
    "merge_existing_comicinfo": True,
    # Option: strip HTML tags from summary/comments
    "strip_html_comments": True,
    # Option: convert CBR (RAR archive) to CBZ (ZIP archive) if only CBR is present
    "convert_cbr_to_cbz": False,
    # Tag to Calibre field mappings: tag_name -> calibre_field_name (e.g. '#writer', 'title', etc.)
    "tag_mappings": copy.deepcopy(DEFAULT_TAG_MAPPINGS),
}

# Persistent config store
plugin_prefs = JSONConfig(CONFIG_FILE_NAME)

# Set defaults if not present
for key, val in DEFAULT_CONFIG.items():
    if key not in plugin_prefs:
        plugin_prefs[key] = copy.deepcopy(val)
    elif key == "tag_mappings":
        # Ensure any newly added ComicInfo tags are present in saved configuration
        current_mappings = plugin_prefs["tag_mappings"]
        for t_name, default_field in DEFAULT_TAG_MAPPINGS.items():
            if t_name not in current_mappings:
                current_mappings[t_name] = default_field
        plugin_prefs["tag_mappings"] = current_mappings


def get_pref(key, default=None):
    """Retrieve a preference value."""
    return plugin_prefs.get(key, default if default is not None else DEFAULT_CONFIG.get(key))


def set_pref(key, val):
    """Set and commit a preference value."""
    plugin_prefs[key] = val
    plugin_prefs.commit()


def get_tag_mappings():
    """Retrieve all tag-to-field mappings with defaults filled."""
    mappings = copy.deepcopy(DEFAULT_TAG_MAPPINGS)
    user_mappings = plugin_prefs.get("tag_mappings", {})
    mappings.update(user_mappings)
    return mappings


def set_tag_mappings(mappings):
    """Save all tag-to-field mappings."""
    plugin_prefs["tag_mappings"] = copy.deepcopy(mappings)
    plugin_prefs.commit()


def reset_to_defaults():
    """Reset configuration back to factory defaults."""
    for key, val in DEFAULT_CONFIG.items():
        plugin_prefs[key] = copy.deepcopy(val)
    plugin_prefs.commit()
