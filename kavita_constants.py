#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Backward-compatibility alias module.
Redirects imports to comicinfo_constants.py.
"""

try:
    from calibre_plugins.comicinfo_writer.comicinfo_constants import *  # noqa: F401,F403
except ImportError:
    from comicinfo_constants import *  # noqa: F401,F403
