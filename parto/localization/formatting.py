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


def get_plural_category(count: int, locale_id: str) -> str:
    """
    Determine CLDR plural category for a count in a given locale.
    Supported categories: 'zero', 'one', 'two', 'few', 'many', 'other'.
    """
    lang = locale_id.lower().split("-")[0].split("_")[0]

    if lang in ("fa", "fa_ir", "persian"):
        # CLDR rule for Persian (fa): n in 0..1 -> 'one', else 'other'
        if count in (0, 1):
            return "one"
        return "other"

    if lang in ("en", "de", "nl", "es", "it", "pt"):
        # Germanic/Romance standard: n == 1 -> 'one', else 'other'
        if count == 1:
            return "one"
        return "other"

    if lang in ("ar", "arabic"):
        # Arabic 6-form plural
        if count == 0:
            return "zero"
        if count == 1:
            return "one"
        if count == 2:
            return "two"
        mod100 = count % 100
        if 3 <= mod100 <= 10:
            return "few"
        if 11 <= mod100 <= 99:
            return "many"
        return "other"

    # Default fallback
    if count == 1:
        return "one"
    return "other"


def resolve_translation_entry(
    entry: Union[str, Dict[str, str]],
    count: Optional[int] = None,
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
            return entry.get("other", next(iter(entry.values()), ""))

        category = get_plural_category(count, locale_id)
        if category in entry:
            return entry[category]
        if "other" in entry:
            return entry["other"]
        if "one" in entry:
            return entry["one"]
        return next(iter(entry.values()), "")

    return str(entry)
