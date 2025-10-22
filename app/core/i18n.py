"""Message catalog and helpers for localized UI strings."""
from __future__ import annotations

from copy import deepcopy
from functools import lru_cache
from importlib import resources
from typing import Any, Dict, Iterable

import yaml

DEFAULT_LOCALE = "en"
_LOCALES_PACKAGE = "app.i18n.locales"
_SUPPORTED_SUFFIXES = (".yml", ".yaml")


def _normalize_locale(locale: str | None) -> str:
    """Normalize locale strings (language-region -> language)."""
    if not locale:
        return DEFAULT_LOCALE
    normalized = locale.replace("_", "-").lower()
    return normalized.split("-", 1)[0]


def _iter_locale_files() -> Iterable[str]:
    """Yield available locale names discovered under the locales package."""
    try:
        files = resources.files(_LOCALES_PACKAGE)
    except ModuleNotFoundError:
        return ()

    locales: list[str] = []
    for entry in files.iterdir():
        if entry.is_file() and entry.suffix.lower() in _SUPPORTED_SUFFIXES:
            locales.append(entry.stem)
    locales.sort()
    return tuple(locales)


SUPPORTED_LOCALES = _iter_locale_files() or (DEFAULT_LOCALE,)


@lru_cache(maxsize=None)
def _load_locale(locale: str) -> Dict[str, Any]:
    """Load and cache a locale file, returning the parsed mapping."""
    files = resources.files(_LOCALES_PACKAGE)
    for suffix in _SUPPORTED_SUFFIXES:
        candidate = files.joinpath(f"{locale}{suffix}")
        if candidate.is_file():
            with candidate.open("r", encoding="utf-8") as handle:
                data = yaml.safe_load(handle) or {}
            if not isinstance(data, dict):
                raise ValueError(f"Locale file '{candidate.name}' must define a mapping at the top level.")
            return data
    raise FileNotFoundError(f"Locale '{locale}' not found.")


def get_messages(locale: str | None = None) -> Dict[str, Any]:
    """Return the message catalog for the requested locale with fallback."""
    normalized = _normalize_locale(locale)
    try:
        catalog = _load_locale(normalized)
    except (FileNotFoundError, ModuleNotFoundError):
        catalog = _load_locale(DEFAULT_LOCALE)
    return deepcopy(catalog)


__all__ = ["DEFAULT_LOCALE", "SUPPORTED_LOCALES", "get_messages"]
