# parto/localization/formatting.py
"""
Parto Localization Subsystem — Interpolation & Pluralization Engine
Safe string templating and locale-aware grammatical rules without code execution.
Author & Maintainer: Ali Kamrani (علی کامرانی)
"""

from __future__ import annotations
import re
from typing import Dict, Any, Union, Optional, Tuple, Set


# Regex matching {identifier} named placeholders without evaluating Python expressions
PLACEHOLDER_REGEX = re.compile(r"\{([a-zA-Z_][a-zA-Z0-9_]*)\}")


def extract_placeholders(template: str) -> Set[str]:
    """Return all named parameter placeholders present in template string."""
    return set(PLACEHOLDER_REGEX.findall(template))


def validate_placeholder_syntax(template: str) -> Tuple[bool, Optional[str]]:
    """
    Validate that curly brackets in a template string form valid named placeholders.
    Returns (is_valid, error_message).
    Detects unclosed '{', unopened '}', empty '{}', or invalid identifier characters.
    """
    if not isinstance(template, str):
        return False, f"Template must be a string, got {type(template).__name__}"

    in_brace = False
    start_pos = -1
    for i, ch in enumerate(template):
        if ch == "{":
            if in_brace:
                return False, f"Nested or unclosed placeholder bracket at position {i}"
            in_brace = True
            start_pos = i
        elif ch == "}":
            if not in_brace:
                return False, f"Unmatched closing bracket at position {i}"
            content = template[start_pos + 1 : i]
            if not content:
                return False, f"Empty placeholder '{{}}' at position {start_pos}"
            if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", content):
                return False, f"Invalid placeholder identifier '{{{content}}}' at position {start_pos}"
            in_brace = False

    if in_brace:
        return False, f"Unclosed placeholder bracket at position {start_pos}"

    return True, None


def safe_interpolate(
    template: str,
    params: Dict[str, Any],
    locale_id: str = "en",
) -> Tuple[str, Set[str]]:
    """
    Safely interpolate named placeholders into a template string.
    
    Guarantees:
    - Never evaluates catalog strings as Python code or expressions.
    - Missing parameters are retained in diagnostic format `{missing_param}` rather than crashing.
    - Extra parameters are safely ignored.
    - Returns (result_string, missing_parameters_set).
    """
    if not params or not template:
        return template, set()

    missing_params: Set[str] = set()

    def _replace(match: re.Match) -> str:
        param_name = match.group(1)
        if param_name in params:
            val = params[param_name]
            return str(val)
        missing_params.add(param_name)
        return match.group(0)

    result = PLACEHOLDER_REGEX.sub(_replace, template)
    return result, missing_params


VALID_PLURAL_CATEGORIES = {"zero", "one", "two", "few", "many", "other"}


def _coerce_numeric_count(count: Any) -> Optional[Union[int, float]]:
    """Safely coerce int, float, Decimal, or numeric string to numeric value."""
    if isinstance(count, (int, float)):
        import math
        if math.isnan(count) or math.isinf(count):
            return None
        return count
    if isinstance(count, str):
        cleaned = count.strip()
        try:
            if "." in cleaned:
                return float(cleaned)
            return int(cleaned)
        except (ValueError, TypeError):
            return None
    try:
        from decimal import Decimal
        if isinstance(count, Decimal):
            return float(count) if count % 1 else int(count)
    except Exception:
        pass
    return None


def get_plural_category(count: Any, locale_id: str = "en") -> str:
    """
    Determine Unicode CLDR plural category for a count in a given locale.
    Supported categories: 'zero', 'one', 'two', 'few', 'many', 'other'.
    
    Standard:
    - Primary engine: Unicode CLDR plural rules via Babel.
    - Handles integers, floats, decimals, and numeric strings.
    - Normalizes and canonicalizes locale tags before evaluation.
    - Resilient fallback for unsupported locales, unknown tags, and missing Babel.
    - Invalid or non-numeric counts safely return 'other'.
    """
    numeric_val = _coerce_numeric_count(count)
    if numeric_val is None:
        return "other"

    from .models import is_valid_locale_id, canonicalize_locale_id

    # Canonicalize and normalize locale identifier
    norm_locale = "en"
    if locale_id and isinstance(locale_id, str):
        clean_id = locale_id.strip()
        if is_valid_locale_id(clean_id):
            norm_locale = canonicalize_locale_id(clean_id)
        else:
            norm_locale = clean_id.lower().replace("_", "-")

    # 1. Primary standards-based resolution: Babel CLDR Engine
    try:
        from babel import Locale as BabelLocale
        sep = "_" if "_" in norm_locale else "-"
        try:
            b_loc = BabelLocale.parse(norm_locale, sep=sep)
        except Exception:
            # Fall back to primary language code (e.g. 'en-US' -> 'en')
            primary_tag = norm_locale.split("-")[0].split("_")[0]
            b_loc = BabelLocale.parse(primary_tag)

        cat = b_loc.plural_form(numeric_val)
        if cat in VALID_PLURAL_CATEGORIES:
            return cat
    except Exception:
        pass

    # 2. Documented CLDR Fallback Engine (when Babel is unavailable or locale unknown)
    lang = norm_locale.lower().split("-")[0].split("_")[0]

    if lang in ("fa", "persian"):
        # Persian CLDR rule: n in 0..1 -> 'one', else 'other'
        if numeric_val in (0, 1) or numeric_val in (0.0, 1.0):
            return "one"
        return "other"

    if lang in ("fr", "french"):
        # French CLDR rule: 0 <= n < 2 -> 'one', else 'other'
        if 0 <= numeric_val < 2:
            return "one"
        return "other"

    if lang in ("en", "de", "nl", "es", "it", "pt"):
        # Germanic/Romance standard: n == 1 -> 'one', else 'other'
        if numeric_val == 1:
            return "one"
        return "other"

    if lang in ("ru", "uk", "be"):
        # Slavic 4-category rule (Russian, Ukrainian, Belarusian)
        if isinstance(numeric_val, float) and not numeric_val.is_integer():
            return "other"
        int_val = abs(int(numeric_val))
        mod10 = int_val % 10
        mod100 = int_val % 100
        if mod10 == 1 and mod100 != 11:
            return "one"
        if 2 <= mod10 <= 4 and not (12 <= mod100 <= 14):
            return "few"
        if mod10 == 0 or (5 <= mod10 <= 9) or (11 <= mod100 <= 14):
            return "many"
        return "other"

    if lang in ("pl", "polish"):
        # Polish rule
        if isinstance(numeric_val, float) and not numeric_val.is_integer():
            return "other"
        int_val = abs(int(numeric_val))
        if int_val == 1:
            return "one"
        mod10 = int_val % 10
        mod100 = int_val % 100
        if 2 <= mod10 <= 4 and not (12 <= mod100 <= 14):
            return "few"
        return "many"

    if lang in ("ar", "arabic"):
        # Arabic 6-category plural rule
        if isinstance(numeric_val, float) and not numeric_val.is_integer():
            return "other"
        int_val = abs(int(numeric_val))
        if int_val == 0:
            return "zero"
        if int_val == 1:
            return "one"
        if int_val == 2:
            return "two"
        mod100 = int_val % 100
        if 3 <= mod100 <= 10:
            return "few"
        if 11 <= mod100 <= 99:
            return "many"
        return "other"

    # Default CLDR cardinal fallback for general languages
    if numeric_val == 1:
        return "one"
    return "other"


def resolve_translation_entry(
    entry: Union[str, Dict[str, str]],
    count: Optional[Any] = None,
    locale_id: str = "en",
) -> str:
    """
    Resolve an entry that may either be a plain string or a plural dictionary.
    
    Example plural dict:
    {
        "one": "{count} Layer",
        "other": "{count} Layers"
    }
    """
    if isinstance(entry, str):
        return entry

    if isinstance(entry, dict):
        if count is None:
            # Fallback to 'other' or first available entry
            return entry.get("other", entry.get("one", next(iter(entry.values()), "")))

        category = get_plural_category(count, locale_id)
        if category in entry:
            return entry[category]
        if "other" in entry:
            return entry["other"]
        if "one" in entry:
            return entry["one"]
        return next(iter(entry.values()), "")

    return str(entry)

