#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Core processing engine for extracting metadata from Calibre,
generating schema-compliant ComicInfo.xml (Anansi Project v2.0/v2.1),
and embedding it safely into comic archives (CBZ/CBR).
"""

import calendar
import os
import re
import html
import shutil
import tempfile
import zipfile
import xml.etree.ElementTree as ET
from datetime import datetime, date

try:
    from calibre_plugins.comicinfo_writer.comicinfo_constants import (
        COMICINFO_TAG_DEFS,
        COMICINFO_TAG_MAP,
        ORDERED_TAG_NAMES,
        ALL_KNOWN_TAGS,
        AGE_RATINGS,
        MANGA_VALUES,
        YES_NO_VALUES,
    )
    from calibre_plugins.comicinfo_writer.config import (
        get_pref,
        get_tag_mappings,
    )
except ImportError:
    try:
        from comicinfo_constants import (
            COMICINFO_TAG_DEFS,
            COMICINFO_TAG_MAP,
            ORDERED_TAG_NAMES,
            ALL_KNOWN_TAGS,
            AGE_RATINGS,
            MANGA_VALUES,
            YES_NO_VALUES,
        )
    except ImportError:
        from kavita_constants import (
            COMICINFO_TAG_DEFS,
            COMICINFO_TAG_MAP,
            ORDERED_TAG_NAMES,
            ALL_KNOWN_TAGS,
            AGE_RATINGS,
            MANGA_VALUES,
            YES_NO_VALUES,
        )
    from config import (
        get_pref,
        get_tag_mappings,
    )

# Pre-compiled regular expressions for HTML stripping and language parsing
_RE_BR = re.compile(r"(?i)<br\s*/?>")
_RE_BLOCK = re.compile(r"(?i)</?(p|div|li|blockquote)[^>]*>")
_RE_TAGS = re.compile(r"<[^>]+>")
_RE_MULTI_NEWLINE = re.compile(r"\n\s*\n")
_RE_LANG_SPLIT = re.compile(r"[-_]")


def strip_html_tags(text):
    """Cleanly strip HTML tags and unescape HTML entities."""
    if not text:
        return ""
    # Replace block level elements and linebreaks with newlines
    text = _RE_BR.sub("\n", text)
    text = _RE_BLOCK.sub("\n", text)
    # Strip remaining HTML tags
    clean = _RE_TAGS.sub("", text)
    # Unescape HTML entities (&amp;, &lt;, etc.)
    clean = html.unescape(clean)
    # Normalize multiple newlines and trim whitespace
    clean = _RE_MULTI_NEWLINE.sub("\n\n", clean)
    return clean.strip()


def format_series_index(val, as_int=True):
    """Format series index float or string into ComicInfo issue number."""
    if val is None:
        return ""
    try:
        f = float(val)
        if as_int and f.is_integer():
            return str(int(f))
        return f"{f:g}"
    except (ValueError, TypeError):
        return str(val).strip()


try:
    from calibre.utils.localization import canonicalize_lang, lang_as_iso639_1
except ImportError:
    canonicalize_lang = None
    lang_as_iso639_1 = None

# Common ISO 639-2/B (3-letter), full English names, and alias mappings to ISO 639-1 (2-letter)
FALLBACK_3TO2_LANG = {
    "eng": "en", "english": "en",
    "deu": "de", "ger": "de", "german": "de",
    "jpn": "ja", "jp": "ja", "japanese": "ja",
    "fra": "fr", "fre": "fr", "french": "fr",
    "spa": "es", "spanish": "es",
    "ita": "it", "italian": "it",
    "zho": "zh", "chi": "zh", "chinese": "zh",
    "kor": "ko", "korean": "ko",
    "rus": "ru", "russian": "ru",
    "por": "pt", "portuguese": "pt",
    "nld": "nl", "dut": "nl", "dutch": "nl",
    "pol": "pl", "polish": "pl",
    "swe": "sv", "swedish": "sv",
    "dan": "da", "danish": "da",
    "nor": "no", "norwegian": "no",
    "fin": "fi", "finnish": "fi",
    "tur": "tr", "turkish": "tr",
    "ces": "cs", "cze": "cs", "czech": "cs",
    "ron": "ro", "rum": "ro", "romanian": "ro",
    "hun": "hu", "hungarian": "hu",
    "gre": "el", "ell": "el", "greek": "el",
    "heb": "he", "hebrew": "he",
    "ara": "ar", "arabic": "ar",
    "hin": "hi", "hindi": "hi",
    "vie": "vi", "vietnamese": "vi",
    "tha": "th", "thai": "th",
    "ind": "id", "indonesian": "id",
    "ukr": "uk", "ukrainian": "uk",
    "cat": "ca", "catalan": "ca",
    "glg": "gl", "galician": "gl",
    "eus": "eu", "baq": "eu", "basque": "eu",
    "lat": "la", "latin": "la",
    "slk": "sk", "slo": "sk", "slovak": "sk",
    "bul": "bg", "bulgarian": "bg",
    "hrv": "hr", "croatian": "hr",
    "srp": "sr", "serbian": "sr",
    "bos": "bs", "bosnian": "bs",
    "slv": "sl", "slovenian": "sl",
    "est": "et", "estonian": "et",
    "lav": "lv", "latvian": "lv",
    "lit": "lt", "lithuanian": "lt",
    "fas": "fa", "per": "fa", "persian": "fa",
}

# Mapping 2-letter ISO 639-1 back to Calibre's preferred 3-letter ISO 639-2
FALLBACK_2TO3_LANG = {
    "en": "eng", "de": "deu", "ja": "jpn", "jp": "jpn", "fr": "fra",
    "es": "spa", "it": "ita", "zh": "zho", "ko": "kor", "ru": "rus",
    "pt": "por", "nl": "nld", "pl": "pol", "sv": "swe", "da": "dan",
    "no": "nor", "fi": "fin", "tr": "tur", "cs": "ces", "ro": "ron",
    "hu": "hun", "el": "ell", "he": "heb", "ar": "ara", "hi": "hin",
    "vi": "vie", "th": "tha", "id": "ind", "uk": "ukr", "ca": "cat",
    "gl": "glg", "eu": "eus", "la": "lat", "sk": "slk", "bg": "bul",
    "hr": "hrv", "sr": "srp", "bs": "bos", "sl": "slv", "et": "est",
    "lv": "lav", "lt": "lit", "fa": "fas",
}


def normalize_iso_language(lang):
    """
    Convert a language representation (e.g. 'eng', 'deu', 'jpn', 'en-US', 'Japanese')
    to an ISO 639-1 two-letter code (e.g. 'en', 'de', 'ja').
    """
    if not lang:
        return ""
    if isinstance(lang, (list, tuple)):
        lang = lang[0] if lang else ""
    lang_str = str(lang).strip().lower()
    if not lang_str:
        return ""

    # Suffixes like 'en-US' or 'en_GB' -> 'en'
    code = _RE_LANG_SPLIT.split(lang_str, maxsplit=1)[0].strip()

    # Direct alias: jp -> ja
    if code == "jp" or lang_str == "jp":
        return "ja"

    # Try Calibre localization utility if available
    if lang_as_iso639_1 is not None:
        try:
            canon = canonicalize_lang(code) if canonicalize_lang else None
            iso = lang_as_iso639_1(canon) if canon else lang_as_iso639_1(code)
            if iso:
                return iso
        except Exception:
            pass

    # Check fallback dictionary
    if code in FALLBACK_3TO2_LANG:
        return FALLBACK_3TO2_LANG[code]
    if lang_str in FALLBACK_3TO2_LANG:
        return FALLBACK_3TO2_LANG[lang_str]

    # If code is already a 2-letter alpha code, return it
    if len(code) == 2 and code.isalpha():
        return code

    return code


def normalize_enum_value(val, allowed_values):
    """Match a value case-insensitively to allowed enum values."""
    if val is None:
        return ""
    s = str(val).strip()
    if not s:
        return ""
    s_lower = s.lower()
    # Direct match
    for allowed in allowed_values:
        if s_lower == allowed.lower():
            return allowed
    # Partial match for common age ratings when validating AgeRating enum
    if allowed_values is AGE_RATINGS or "Teen" in allowed_values:
        if "teen" in s_lower:
            return "Teen"
        if "mature" in s_lower or "17+" in s_lower:
            return "Mature 17+"
        if "adult" in s_lower or "18+" in s_lower:
            return "Adults Only 18+"
        if "kid" in s_lower:
            return "Kids to Adults"
        if "everyone" in s_lower:
            if "10+" in s_lower:
                return "Everyone 10+"
            return "Everyone"
    return allowed_values[0]  # default to 'Unknown'


def extract_field_value(mi, field_name, custom_columns_dict=None):
    """
    Extract a raw value from Calibre Metadata object (mi) by field name.
    Supports standard fields, date subfields (pubdate:year),
    identifiers (identifier:isbn), and custom columns (#...).
    """
    if not field_name or not mi:
        return None

    field_name = field_name.strip()

    # Identifiers: identifier:<type> (e.g. identifier:isbn, identifier:url)
    if field_name.startswith("identifier:"):
        id_type = field_name.split(":", 1)[1].strip().lower()
        identifiers = getattr(mi, "identifiers", {})
        if callable(getattr(mi, "get_identifiers", None)):
            identifiers = mi.get_identifiers() or {}
        return identifiers.get(id_type)

    # Date subcomponents: pubdate:year, pubdate:month, pubdate:day
    if field_name.startswith("pubdate:"):
        part = field_name.split(":", 1)[1].strip().lower()
        pubdate = getattr(mi, "pubdate", None)
        if pubdate and isinstance(pubdate, (datetime, date)):
            # Calibre uses year 101 (0101-01-01) to represent undefined/unset dates
            if pubdate.year <= 101:
                return None
            if part == "year":
                return pubdate.year
            elif part == "month":
                return pubdate.month
            elif part == "day":
                return pubdate.day
        return None

    # Custom column: starts with '#'
    if field_name.startswith("#"):
        # Check in custom_columns_dict first if provided
        if custom_columns_dict and field_name in custom_columns_dict:
            return custom_columns_dict[field_name]
        # Check via mi.get() or mi.get_user_metadata()
        if hasattr(mi, "get"):
            val = mi.get(field_name)
            if val is not None:
                if isinstance(val, (datetime, date)) and val.year <= 101:
                    return None
                return val
        user_metadata = getattr(mi, "user_metadata", {})
        if callable(getattr(mi, "get_all_user_metadata", None)):
            user_metadata = mi.get_all_user_metadata(make_copy=False) or {}
        if field_name in user_metadata:
            meta = user_metadata[field_name]
            val = meta.get("#value#")
            if isinstance(val, (datetime, date)) and val.year <= 101:
                return None
            return val
        return None

    # Standard Calibre fields
    if hasattr(mi, field_name):
        val = getattr(mi, field_name)
        if field_name == "pubdate" and isinstance(val, (datetime, date)) and val.year <= 101:
            return None
        return val

    return None


def convert_value_for_tag(val, tag_name, tag_type, options):
    """
    Format and convert a raw Calibre value according to the ComicInfo tag specification.
    """
    if val is None:
        return None

    # Special handling for series index / Number
    if tag_name == "Number":
        return format_series_index(val, as_int=options.get("series_index_as_int", True))

    if tag_type == "int":
        try:
            int_val = int(round(float(val)))
            return int_val
        except (ValueError, TypeError):
            return None

    elif tag_type == "decimal":
        try:
            dec_val = float(val)
            # ComicInfo CommunityRating is 0.0 - 5.0
            if tag_name == "CommunityRating":
                if dec_val > 5.0:
                    dec_val = dec_val / 2.0  # handle 10-point scale
                dec_val = max(0.0, min(5.0, dec_val))
            return round(dec_val, 1)
        except (ValueError, TypeError):
            return None

    elif tag_type == "enum_agerating":
        return normalize_enum_value(val, AGE_RATINGS)

    elif tag_type == "enum_manga":
        if isinstance(val, bool):
            return "Yes" if val else "No"
        return normalize_enum_value(val, MANGA_VALUES)

    elif tag_type == "enum_yesno":
        if isinstance(val, bool):
            return "Yes" if val else "No"
        return normalize_enum_value(val, YES_NO_VALUES)

    else:
        # String types
        if isinstance(val, (list, tuple, set)):
            # Join authors, tags, etc.
            str_val = ", ".join(str(item).strip() for item in val if item)
        elif isinstance(val, (datetime, date)):
            str_val = val.strftime("%Y-%m-%d")
        else:
            str_val = str(val)

        if tag_name == "Summary" and options.get("strip_html_comments", True):
            str_val = strip_html_tags(str_val)
        else:
            str_val = str_val.strip()

        if tag_name == "LanguageISO":
            str_val = normalize_iso_language(str_val)

        return str_val if str_val else None


def extract_comicinfo_data(mi, mappings=None, options=None, custom_columns_dict=None):
    """
    Extract a dictionary of {tag_name: formatted_value} from Calibre Metadata
    based on the configured tag mappings and options.
    """
    if mappings is None:
        mappings = get_tag_mappings()
    if options is None:
        options = {
            "write_series_index": get_pref("write_series_index", True),
            "series_index_as_int": get_pref("series_index_as_int", True),
            "strip_html_comments": get_pref("strip_html_comments", True),
        }

    data = {}
    for tag_name, tag_type, _default, _desc, _schema_desc in COMICINFO_TAG_DEFS:
        field_name = mappings.get(tag_name)
        if not field_name:
            continue

        raw_val = extract_field_value(mi, field_name, custom_columns_dict)
        formatted_val = convert_value_for_tag(raw_val, tag_name, tag_type, options)

        if formatted_val is not None:
            data[tag_name] = formatted_val

    # Calibre unset date check:
    # If the date results in Year 101, Month 1, Day 1 (or Year <= 101),
    # it indicates that pubdate is not set in Calibre and must not be written.
    if data.get("Year") is not None and data["Year"] <= 101:
        data.pop("Year", None)
        if data.get("Month") == 1:
            data.pop("Month", None)
        if data.get("Day") == 1:
            data.pop("Day", None)

    return data


def generate_comicinfo_xml(data, existing_xml_content=None, merge=True, unmapped_tags=None):
    """
    Generate ComicInfo.xml UTF-8 bytes from metadata dictionary.
    If merge=True and existing_xml_content is provided, existing tags
    not present in `data` (such as <Pages>) are preserved, EXCEPT
    tags in `unmapped_tags` and `Number` if not present in `data`.
    """
    existing_tree = None
    preserved_elements = {}

    if merge and existing_xml_content:
        try:
            if isinstance(existing_xml_content, str):
                existing_xml_content = existing_xml_content.encode("utf-8")
            existing_tree = ET.fromstring(existing_xml_content)

            # Check if existing XML has unset Calibre date (Year == 101)
            existing_year_el = existing_tree.find("Year")
            has_unset_year = (
                existing_year_el is not None
                and existing_year_el.text
                and existing_year_el.text.strip() in ("101", "0101")
            )

            for child in existing_tree:
                tag = child.tag
                if has_unset_year and tag in ("Year", "Month", "Day"):
                    continue
                # Do not preserve tags that are explicitly unmapped / mapped to None
                if unmapped_tags and tag in unmapped_tags:
                    continue
                # If Number is not in data, never restore an old Number from the archive
                if tag == "Number" and "Number" not in data:
                    continue
                # Preserve child elements if not overwritten by new data
                if tag not in data:
                    preserved_elements[tag] = child
        except Exception:
            # If existing XML is corrupt or invalid, start fresh
            pass

    # Root element with XMLSchema namespaces
    root = ET.Element(
        "ComicInfo",
        {
            "xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
            "xmlns:xsd": "http://www.w3.org/2001/XMLSchema",
        },
    )

    # Output tags strictly following schema order
    for tag_name in ORDERED_TAG_NAMES:
        if tag_name in data:
            val = data[tag_name]
            elem = ET.SubElement(root, tag_name)
            elem.text = str(val)
        elif tag_name in preserved_elements:
            root.append(preserved_elements[tag_name])

    # Append any remaining preserved elements not in COMICINFO_TAG_DEFS (e.g. <Pages>)
    for tag_name, elem in preserved_elements.items():
        if tag_name not in ALL_KNOWN_TAGS:
            root.append(elem)

    # Format XML with 2-space indentation using stdlib ET.indent
    ET.indent(root, space="  ")
    return b'<?xml version="1.0" encoding="utf-8"?>\n' + ET.tostring(root, encoding="utf-8") + b"\n"


def is_comicinfo_path(path):
    """
    Return True if the archive entry is a ComicInfo.xml file,
    regardless of case, extension variation, or directory nesting.
    """
    if not path:
        return False
    clean = path.replace("\\", "/").rstrip("/")
    base = os.path.basename(clean).lower()
    return base in ("comicinfo.xml", "comicinfo")


def _find_comicinfo_entry(zf):
    """
    Locate the best ComicInfo.xml ZipInfo entry inside an open ZipFile.
    Searches root level first, then any nested subdirectory.
    """
    root_candidate = None
    nested_candidate = None
    for item in zf.infolist():
        clean = item.filename.replace("\\", "/").rstrip("/")
        if "__macosx" in clean.lower():
            continue
        if is_comicinfo_path(clean):
            if "/" not in clean:
                root_candidate = item
                break
            elif nested_candidate is None:
                nested_candidate = item
    return root_candidate or nested_candidate


def find_comicinfo_in_cbz(cbz_path):
    """
    Locate and read ComicInfo.xml from a CBZ archive.
    Searches root level first, then any nested subdirectory.
    Returns tuple: (xml_bytes, inner_filename) or (None, None).
    """
    if not os.path.exists(cbz_path):
        return None, None

    try:
        with zipfile.ZipFile(cbz_path, "r") as zf:
            chosen = _find_comicinfo_entry(zf)
            if chosen:
                return zf.read(chosen.filename), chosen.filename
    except Exception:
        pass

    return None, None


def parse_comicinfo_xml(xml_bytes):
    """
    Parse ComicInfo.xml bytes into a structured dictionary:
    {
        tag_name: string_value,
        ...
        'Pages': [ {attrib_key: val, ...}, ... ]  # if present
    }
    """
    if not xml_bytes:
        return {}

    if isinstance(xml_bytes, str):
        xml_bytes = xml_bytes.encode("utf-8")

    try:
        root = ET.fromstring(xml_bytes)
    except Exception:
        return {}

    result = {}
    for child in root:
        tag = child.tag
        if tag == "Pages":
            result["Pages"] = [dict(page_elem.attrib) for page_elem in child]
        else:
            text = child.text
            if text is not None:
                result[tag] = text.strip()

    return result


_DIRECT_STR_FIELDS = frozenset({
    "title",
    "title_sort",
    "series",
    "series_sort",
    "author_sort",
    "comments",
    "publisher",
})


def apply_comicinfo_to_calibre_metadata(mi, parsed_tags, mappings=None):
    """
    Apply parsed ComicInfo tag dictionary back to Calibre Metadata object (mi).
    Uses configured mappings (ComicInfo tag -> Calibre field) in reverse.
    """
    if not mi or not parsed_tags:
        return mi

    if mappings is None:
        mappings = get_tag_mappings()

    for tag_name, field_name in mappings.items():
        if not field_name or tag_name not in parsed_tags:
            continue

        val_str = parsed_tags[tag_name]
        if not val_str:
            continue

        # Standard string fields
        if field_name in _DIRECT_STR_FIELDS:
            setattr(mi, field_name, val_str)
        elif field_name == "series_index":
            try:
                mi.series_index = float(val_str)
            except (ValueError, TypeError):
                pass
        elif field_name == "authors":
            authors = [a.strip() for a in val_str.split(",") if a.strip()]
            if authors:
                mi.authors = authors
        elif field_name == "tags":
            tags = [t.strip() for t in val_str.split(",") if t.strip()]
            if tags:
                mi.tags = tags
        elif field_name == "rating":
            try:
                r = float(val_str)
                mi.rating = max(0.0, min(5.0, r))
            except (ValueError, TypeError):
                pass
        elif field_name == "languages":
            raw_lang = val_str.strip().lower()
            if raw_lang == "jp":
                raw_lang = "ja"
            canon = None
            if canonicalize_lang is not None:
                try:
                    canon = canonicalize_lang(raw_lang)
                except Exception:
                    pass
            if not canon and raw_lang in FALLBACK_2TO3_LANG:
                canon = FALLBACK_2TO3_LANG[raw_lang]
            mi.languages = [canon or raw_lang]
        elif field_name.startswith("identifier:"):
            id_type = field_name.split(":", 1)[1].strip().lower()
            mi.set_identifier(id_type, val_str)
        elif field_name.startswith("pubdate"):
            pass  # pubdate is reconstructed below

        # Custom column
        elif field_name.startswith("#"):
            datatype = "text"
            if hasattr(mi, "user_metadata"):
                col_meta = mi.user_metadata.get(field_name, {})
                datatype = col_meta.get("datatype", "text")

            converted_val = val_str
            if datatype in ("int", "integer"):
                try:
                    converted_val = int(round(float(val_str)))
                except (ValueError, TypeError):
                    converted_val = None
            elif datatype == "float":
                try:
                    converted_val = float(val_str)
                except (ValueError, TypeError):
                    converted_val = None
            elif datatype == "bool":
                converted_val = val_str.lower() in ("yes", "true", "1")
            elif datatype in ("comma_separated", "enumeration_list"):
                converted_val = [x.strip() for x in val_str.split(",") if x.strip()]

            if converted_val is not None:
                mi.set(field_name, converted_val)

    # Reconstruct pubdate from Year, Month, Day if available
    year_str = parsed_tags.get("Year")
    if year_str:
        try:
            year_int = int(year_str)
            if year_int > 101:  # Filter out Calibre unset date (101)
                month_int = 1
                day_int = 1
                if "Month" in parsed_tags:
                    try:
                        month_int = max(1, min(12, int(parsed_tags["Month"])))
                    except (ValueError, TypeError):
                        pass
                if "Day" in parsed_tags:
                    try:
                        max_day = calendar.monthrange(year_int, month_int)[1]
                        day_int = max(1, min(max_day, int(parsed_tags["Day"])))
                    except (ValueError, TypeError):
                        pass
                mi.pubdate = datetime(year_int, month_int, day_int)
        except (ValueError, TypeError):
            pass

    return mi


def _merge_xml_bytes(comicinfo_xml_bytes, existing_xml, unmapped_tags=None):
    """Merge newly generated ComicInfo XML bytes with existing XML bytes."""
    if not existing_xml:
        return comicinfo_xml_bytes
    try:
        in_tree = ET.fromstring(comicinfo_xml_bytes)
        in_data = {child.tag: child.text for child in in_tree if child.text}
        return generate_comicinfo_xml(
            in_data, existing_xml, merge=True, unmapped_tags=unmapped_tags
        )
    except Exception:
        return comicinfo_xml_bytes


def remove_comicinfo_from_cbz(cbz_path):
    """
    Remove ALL ComicInfo.xml files from a CBZ archive,
    including any nested inside subdirectories.
    Returns tuple: (bool_success, count_removed).
    """
    if not os.path.exists(cbz_path):
        raise FileNotFoundError(f"CBZ file not found: {cbz_path}")

    with zipfile.ZipFile(cbz_path, "r") as zf_in:
        items_to_remove = [
            item.filename for item in zf_in.infolist() if is_comicinfo_path(item.filename)
        ]
        if not items_to_remove:
            return False, 0

        dir_name = os.path.dirname(os.path.abspath(cbz_path))
        fd, temp_path = tempfile.mkstemp(suffix=".cbz.tmp", dir=dir_name)
        os.close(fd)

        try:
            with zipfile.ZipFile(temp_path, "w", compression=zipfile.ZIP_DEFLATED) as zf_out:
                for item in zf_in.infolist():
                    if is_comicinfo_path(item.filename):
                        continue
                    zf_out.writestr(item, zf_in.read(item.filename))

            os.replace(temp_path, cbz_path)
            return True, len(items_to_remove)
        finally:
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except OSError:
                    pass


def embed_into_cbz(cbz_path, comicinfo_xml_bytes, merge=True, unmapped_tags=None):
    """
    Safely embed ComicInfo.xml into a CBZ file.
    Always deletes any old ComicInfo.xml (at root or in any subdirectory)
    before adding the new ComicInfo.xml at the root of the archive.
    If merge=True, parses existing metadata and merges before writing,
    omitting any tags in unmapped_tags or Number if not in new data.
    """
    if not os.path.exists(cbz_path):
        raise FileNotFoundError(f"CBZ file not found: {cbz_path}")

    dir_name = os.path.dirname(os.path.abspath(cbz_path))
    fd, temp_path = tempfile.mkstemp(suffix=".cbz.tmp", dir=dir_name)
    os.close(fd)

    try:
        with zipfile.ZipFile(cbz_path, "r") as zf_in:
            final_xml_bytes = comicinfo_xml_bytes
            if merge:
                chosen = _find_comicinfo_entry(zf_in)
                if chosen is not None:
                    try:
                        existing_xml = zf_in.read(chosen.filename)
                        final_xml_bytes = _merge_xml_bytes(
                            comicinfo_xml_bytes, existing_xml, unmapped_tags=unmapped_tags
                        )
                    except Exception:
                        pass

            with zipfile.ZipFile(temp_path, "w", compression=zipfile.ZIP_DEFLATED) as zf_out:
                # Copy all existing files EXCEPT any old ComicInfo.xml (root or nested)
                for item in zf_in.infolist():
                    if is_comicinfo_path(item.filename):
                        continue
                    zf_out.writestr(item, zf_in.read(item.filename))

                # Add the new ComicInfo.xml strictly at the root of the archive
                zf_out.writestr("ComicInfo.xml", final_xml_bytes)

        # Atomically replace the original file
        os.replace(temp_path, cbz_path)
    finally:
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except OSError:
                pass

    return True


def convert_cbr_to_cbz(cbr_path, comicinfo_xml_bytes, merge=True, unmapped_tags=None):
    """
    Convert a CBR archive to CBZ format and embed ComicInfo.xml.
    Requires Calibre or system RAR extractor.
    Returns path to the newly created CBZ file.
    """
    if not os.path.exists(cbr_path):
        raise FileNotFoundError(f"CBR file not found: {cbr_path}")

    # Temporary directory for extracted files
    temp_dir = tempfile.mkdtemp(prefix="calibre_cbr_extract_")
    cbz_path = os.path.splitext(cbr_path)[0] + ".cbz"
    dir_name = os.path.dirname(os.path.abspath(cbz_path))
    temp_cbz_path = None

    try:
        # Try Calibre unrar
        try:
            from calibre.utils.unrar import extract
            extract(cbr_path, temp_dir)
        except Exception as exc:
            raise RuntimeError(
                "Cannot extract CBR archive: Calibre unrar utility is not available."
            ) from exc

        # Check if existing ComicInfo.xml exists anywhere in extracted directory
        existing_xml = None
        if merge:
            for root_dir, _dirs, files in os.walk(temp_dir):
                for f in files:
                    if is_comicinfo_path(f):
                        full_path = os.path.join(root_dir, f)
                        try:
                            with open(full_path, "rb") as xf:
                                existing_xml = xf.read()
                        except Exception:
                            pass
                        break
                if existing_xml:
                    break

        final_xml_bytes = (
            _merge_xml_bytes(comicinfo_xml_bytes, existing_xml, unmapped_tags=unmapped_tags)
            if merge and existing_xml
            else comicinfo_xml_bytes
        )

        # Write to a temporary zip file first, then atomically replace target CBZ
        fd, temp_cbz_path = tempfile.mkstemp(suffix=".cbz.tmp", dir=dir_name)
        os.close(fd)

        with zipfile.ZipFile(temp_cbz_path, "w", compression=zipfile.ZIP_DEFLATED) as zf_out:
            zf_out.writestr("ComicInfo.xml", final_xml_bytes)

            # Add all other extracted image/content files (skipping any old comicinfo.xml)
            for root_dir, _dirs, files in os.walk(temp_dir):
                for f in files:
                    if is_comicinfo_path(f):
                        continue
                    full_path = os.path.join(root_dir, f)
                    arcname = os.path.relpath(full_path, temp_dir)
                    zf_out.write(full_path, arcname)

        os.replace(temp_cbz_path, cbz_path)
        return cbz_path
    finally:
        if temp_cbz_path and os.path.exists(temp_cbz_path):
            try:
                os.remove(temp_cbz_path)
            except OSError:
                pass
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir, ignore_errors=True)
