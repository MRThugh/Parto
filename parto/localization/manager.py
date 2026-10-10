# parto/localization/manager.py
"""
Parto Localization Subsystem — Central Localization Manager
Central application service coordinating locale switching, catalog registry,
translation fallback chains, and layout direction synchronization.
Author & Maintainer: Ali Kamrani (علی Kamrani)
"""

from __future__ import annotations
import os
import sys
import logging
from typing import Dict, List, Optional, Set, Callable, Any

try:
    from PySide6.QtCore import QObject, Signal, Qt
    from PySide6.QtWidgets import QApplication
    _QT_AVAILABLE = True
except ImportError:
    _QT_AVAILABLE = False

from .models import (
    LocaleMetadata,
    TextDirection,
    DiagnosticRecord,
    is_valid_locale_id,
    canonicalize_locale_id,
    DuplicateCatalogError,
)
from .catalog import TranslationCatalog
from .loader import LanguageCatalogLoader
from .formatting import (
    safe_interpolate,
    resolve_translation_entry,
)
from .persistence import LocalePreferences

logger = logging.getLogger("parto.localization.manager")


if _QT_AVAILABLE:
    class _BaseEmitter(QObject):
        locale_changed = Signal(str)
        language_changed = Signal(str)
else:
    class _BaseEmitter:
        def __init__(self, parent=None):
            self._listeners: List[Callable[[str], None]] = []

        class _DummySignal:
            def __init__(self, owner):
                self._owner = owner
            def emit(self, val):
                for l in list(self._owner._listeners):
                    try:
                        l(val)
                    except Exception:
                        pass
            def connect(self, callback):
                if callback not in self._owner._listeners:
                    self._owner._listeners.append(callback)
            def disconnect(self, callback):
                if callback in self._owner._listeners:
                    self._owner._listeners.remove(callback)

        @property
        def locale_changed(self):
            if not hasattr(self, "_loc_sig"):
                self._loc_sig = self._DummySignal(self)
            return self._loc_sig

        @property
        def language_changed(self):
            return self.locale_changed


class LocalizationManager(_BaseEmitter):
    """
    Central service for application localization and internationalization.
    Thread-safe, observable, and fully decoupled from UI widgets.
    """
    _instance: Optional[LocalizationManager] = None

    def __init__(self, parent: Optional[Any] = None):
        super().__init__(parent)
        self._catalogs: Dict[str, TranslationCatalog] = {}
        self._discovery_directories: List[str] = []
        self._current_locale: str = "en"
        self._fallback_locale: str = "en"
        self._preferences = LocalePreferences()
        self._diagnostics: List[DiagnosticRecord] = []
        self._missing_keys: Set[str] = set()
        self._headless_listeners: List[Callable[[str], None]] = []
        self._is_switching: bool = False
        self._last_persistence_succeeded: bool = True
        self._last_persistence_error: Optional[str] = None
        self._last_listener_failures: List[Dict[str, Any]] = []
        self._last_refresh_completed: bool = True

        # Connect duplicate signal alias
        if _QT_AVAILABLE:
            self.locale_changed.connect(lambda l: self.language_changed.emit(l))

        # Auto-discover bundled catalogs
        self._init_bundled_catalogs()

        # Load persisted locale preference
        preferred = self._preferences.get_preferred_locale(default="en")
        if preferred in self._catalogs:
            self._current_locale = preferred

    @classmethod
    def instance(cls) -> LocalizationManager:
        if cls._instance is None:
            cls._instance = LocalizationManager()
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        """Reset singleton for clean unit test isolation."""
        cls._instance = None

    def _init_bundled_catalogs(self) -> None:
        """Locate and register factory catalogs from parto/resources/locales/."""
        here = os.path.dirname(os.path.abspath(__file__))
        parto_root = os.path.dirname(here)
        bundled_locales_dir = os.path.join(parto_root, "resources", "locales")
        self.add_catalog_directory(bundled_locales_dir)

    def add_catalog_directory(self, directory: str) -> None:
        """Register an additional directory for automatic catalog discovery."""
        if directory and os.path.isdir(directory):
            abs_dir = os.path.abspath(directory)
            if abs_dir not in self._discovery_directories:
                self._discovery_directories.append(abs_dir)
            self.discover_locales(abs_dir)

    # -------------------------------------------------------------------------
    # Properties & Metadata
    # -------------------------------------------------------------------------

    @property
    def current_locale(self) -> str:
        """Active language identifier (e.g. 'en', 'fa')."""
        return self._current_locale

    @property
    def current_language(self) -> str:
        """Alias for active language identifier."""
        return self._current_locale

    @property
    def fallback_locale(self) -> str:
        """Configured fallback language identifier."""
        return self._fallback_locale

    @fallback_locale.setter
    def fallback_locale(self, locale_id: str) -> None:
        self._fallback_locale = locale_id

    @property
    def current_metadata(self) -> LocaleMetadata:
        """Metadata for active language."""
        cat = self._catalogs.get(self._current_locale)
        if cat:
            return cat.metadata
        # Default placeholder metadata
        return LocaleMetadata(
            id=self._current_locale,
            name="English" if self._current_locale == "en" else self._current_locale,
            native_name="English" if self._current_locale == "en" else self._current_locale,
            direction=TextDirection.LTR,
        )

    @property
    def direction(self) -> TextDirection:
        """Text direction of active language."""
        return self.current_metadata.direction

    @property
    def is_rtl(self) -> bool:
        """True if active language is Right-to-Left (e.g. Persian)."""
        return self.direction == TextDirection.RTL

    @property
    def last_persistence_succeeded(self) -> bool:
        """True if the most recent requested persistence operation completed successfully."""
        return self._last_persistence_succeeded

    @property
    def last_persistence_error(self) -> Optional[str]:
        """Error message from most recent failed persistence operation, or None."""
        return self._last_persistence_error

    @property
    def last_listener_failures(self) -> List[Dict[str, Any]]:
        """List of listener errors encountered during the last locale switch."""
        return list(self._last_listener_failures)

    @property
    def last_refresh_completed(self) -> bool:
        """True if all observers and callbacks completed without exception during the last switch."""
        return self._last_refresh_completed

    def get_available_languages(self) -> List[LocaleMetadata]:
        """List of all validly registered and available language metadata."""
        return [cat.metadata for cat in self._catalogs.values()]

    def get_available_locales(self) -> List[str]:
        """List of all registered language identifier codes."""
        return sorted(list(self._catalogs.keys()))

    def get_catalog(self, locale_id: str) -> Optional[TranslationCatalog]:
        """Access registered catalog for given language code with normalization and case fallback."""
        if not locale_id or not isinstance(locale_id, str):
            return None
        clean_id = locale_id.strip()
        if clean_id in self._catalogs:
            return self._catalogs[clean_id]
        if is_valid_locale_id(clean_id):
            canon_id = canonicalize_locale_id(clean_id)
            if canon_id in self._catalogs:
                return self._catalogs[canon_id]
        lower_tag = clean_id.lower().replace("_", "-")
        for k, cat in self._catalogs.items():
            if k.lower().replace("_", "-") == lower_tag:
                return cat
        return None

    # -------------------------------------------------------------------------
    # Catalog Registration & Discovery
    # -------------------------------------------------------------------------

    def register_catalog(self, catalog: TranslationCatalog, replace: bool = False) -> bool:
        """
        Register a valid TranslationCatalog into the manager.
        
        Duplicate Registration Policy:
        - Accidental duplicate registrations are strictly rejected with a clear diagnostic error and return False.
        - Replacing an existing catalog requires an explicit `replace=True` flag.
        - Normalizes locale identifiers before duplicate detection so case variations are caught.
        - Enforces placeholder compatibility against the configured fallback catalog.
        """
        if not catalog or not hasattr(catalog, "id"):
            self._record_diagnostic("error", "Rejected invalid catalog object")
            return False

        raw_id = catalog.id
        if not is_valid_locale_id(raw_id):
            msg = f"Rejected catalog with invalid locale identifier: {raw_id!r}"
            self._record_diagnostic("error", msg, locale_id=str(raw_id))
            logger.warning(msg)
            return False

        canon_id = canonicalize_locale_id(raw_id)

        # Check for existing duplicate registrations across canonical and case variants
        existing_key = None
        if canon_id in self._catalogs:
            existing_key = canon_id
        else:
            lower_norm = canon_id.lower()
            for k in self._catalogs.keys():
                if k.lower() == lower_norm:
                    existing_key = k
                    break

        if existing_key is not None and not replace:
            msg = (
                f"Duplicate catalog registration rejected for locale '{canon_id}' "
                f"(already registered as '{existing_key}'). Pass replace=True to overwrite."
            )
            self._record_diagnostic("error", msg, locale_id=canon_id)
            logger.warning(msg)
            return False

        # Structural & Schema Validation
        errors = catalog.validate()
        if errors:
            msg = f"Rejected catalog '{canon_id}': {'; '.join(errors)}"
            self._record_diagnostic("error", msg, locale_id=canon_id)
            logger.warning(msg)
            return False

        # Placeholder Compatibility Validation against fallback catalog
        fb_key = canonicalize_locale_id(self._fallback_locale) if is_valid_locale_id(self._fallback_locale) else self._fallback_locale
        if canon_id != fb_key and fb_key in self._catalogs:
            fb_cat = self._catalogs[fb_key]
            mismatches = LanguageCatalogLoader.validate_placeholder_compatibility(catalog, fb_cat)
            if mismatches:
                msg = (
                    f"Rejected catalog '{canon_id}' due to placeholder incompatibility with fallback '{fb_key}': "
                    f"{'; '.join(mismatches)}"
                )
                self._record_diagnostic("error", msg, locale_id=canon_id)
                logger.warning(msg)
                return False

        # If we are registering or replacing the fallback catalog, check existing catalogs for compatibility
        if canon_id == fb_key:
            for exist_id, exist_cat in list(self._catalogs.items()):
                if exist_id != canon_id:
                    mismatches = LanguageCatalogLoader.validate_placeholder_compatibility(exist_cat, catalog)
                    if mismatches:
                        msg = (
                            f"Warning: Existing catalog '{exist_id}' has placeholder incompatibility with newly registered fallback '{canon_id}': "
                            f"{'; '.join(mismatches)}"
                        )
                        self._record_diagnostic("warning", msg, locale_id=exist_id)
                        logger.warning(msg)

        if existing_key is not None and existing_key != canon_id:
            del self._catalogs[existing_key]

        self._catalogs[canon_id] = catalog
        logger.info(f"Registered language catalog: {canon_id} ({catalog.name}) with {catalog.count()} keys (replace={replace})")
        return True

    def load_catalog_file(self, filepath: str, replace: bool = False) -> bool:
        """Load and register a single catalog file."""
        cat, err = LanguageCatalogLoader.load_from_file(filepath)
        if not cat:
            self._record_diagnostic("error", f"Failed to load '{filepath}': {err}")
            return False
        return self.register_catalog(cat, replace=replace)

    def discover_locales(self, directory: Optional[str] = None) -> int:
        """
        Discover language packs from a directory and register valid ones.
        Returns count of newly registered languages.
        """
        dirs = []
        if directory:
            dirs.append(directory)

        # Also support user external locale directory (~/.parto/locales)
        user_locales = os.path.expanduser("~/.parto/locales")
        if os.path.isdir(user_locales):
            dirs.append(user_locales)

        discovered = LanguageCatalogLoader.discover_catalogs(dirs)
        added = 0
        for cat in discovered.values():
            if self.register_catalog(cat, replace=False):
                added += 1
        return added

    # -------------------------------------------------------------------------
    # Translation Engine & Fallback Chain
    # -------------------------------------------------------------------------

    def translate(
        self,
        key: str,
        default: Optional[str] = None,
        count: Optional[int] = None,
        **kwargs,
    ) -> str:
        """
        Primary translation lookup method.
        
        Fallback chain:
        1. Active language catalog entry.
        2. Configured fallback language catalog entry (default 'en').
        3. Explicit 'default' value if provided.
        4. Diagnostic fallback formatted key string, e.g. '[key]'.
        """
        return self._resolve_and_format(
            target_locale=self._current_locale,
            key=key,
            default=default,
            count=count,
            params=kwargs,
        )

    def t(self, key: str, default: Optional[str] = None, count: Optional[int] = None, **kwargs) -> str:
        """Convenience alias for translate()."""
        return self.translate(key=key, default=default, count=count, **kwargs)

    def translate_plural(
        self,
        key: str,
        count: int,
        default: Optional[str] = None,
        **kwargs,
    ) -> str:
        """Translate a message using grammatical plural rules."""
        kwargs["count"] = count
        return self.translate(key, default=default, count=count, **kwargs)

    def translate_for_locale(
        self,
        locale_id: str,
        key: str,
        default: Optional[str] = None,
        count: Optional[int] = None,
        **kwargs,
    ) -> str:
        """
        Translate a message for a specific target locale, independent of active UI locale.
        Essential for background tasks, logs, exports, or multi-lingual Intent responses.
        """
        return self._resolve_and_format(
            target_locale=locale_id,
            key=key,
            default=default,
            count=count,
            params=kwargs,
        )

    def format_intent_response(
        self,
        key: str,
        locale: Optional[str] = None,
        **kwargs,
    ) -> str:
        """
        Dedicated Intent Subsystem integration contract.
        Formats structured operation results, confirmation prompts, or errors
        in the requested locale (defaulting to current active locale).
        """
        target = locale or self._current_locale
        return self.translate_for_locale(target, key, **kwargs)

    def _resolve_and_format(
        self,
        target_locale: str,
        key: str,
        default: Optional[str],
        count: Optional[Any],
        params: Dict[str, Any],
    ) -> str:
        if not key or not isinstance(key, str):
            return default if default is not None else ""

        entry = None
        effective_locale = target_locale

        # 1. Look up in target catalog with normalization
        target_cat = self.get_catalog(target_locale)
        if target_cat:
            entry = target_cat.get(key)
            effective_locale = target_cat.id

        # 2. Look up in fallback catalog if missing in target
        fb_locale = self._fallback_locale
        if entry is None and (target_cat is None or target_cat.id != fb_locale):
            fb_cat = self.get_catalog(fb_locale)
            if fb_cat:
                entry = fb_cat.get(key)
                if entry is not None:
                    effective_locale = fb_cat.id
                    self._record_missing_key(key, target_locale)

        # 3. Neither catalog provides an entry
        if entry is None:
            self._record_missing_key(key, target_locale)
            if default is not None:
                template = default
            else:
                template = f"[{key}]"
            result, _ = safe_interpolate(template, params, effective_locale)
            return result

        # 4. Resolve pluralization if entry is plural dictionary
        template = resolve_translation_entry(entry, count=count, locale_id=effective_locale)

        # 5. Named interpolation
        result, missing_params = safe_interpolate(template, params, effective_locale)
        if missing_params:
            msg = f"Missing interpolation parameter(s) for key '{key}': {missing_params}"
            self._record_diagnostic("warning", msg, locale_id=effective_locale, key=key)
            logger.debug(msg)

        return result

    # -------------------------------------------------------------------------
    # Runtime Language Switching (Atomic & Safe)
    # -------------------------------------------------------------------------

    def set_locale(
        self,
        locale_id: str,
        persist: bool = True,
        strict_persistence: bool = False,
    ) -> bool:
        """
        Switch active application language at runtime in an atomic, failure-safe transaction.
        
        Atomicity & Safety guarantees:
        1. Validates requested identifier conforms to BCP 47 and has no path traversal.
        2. Idempotent: No-op if requested locale is already active.
        3. Prevents recursive switching via re-entrancy guard.
        4. Dynamically attempts catalog discovery if not currently in memory.
        5. Validates candidate catalog metadata and translations before committing.
        6. If any validation stage fails, completely preserves previously active locale and direction.
        7. On commit: updates locale, direction, and broadcasts notifications safely.
        8. Contract for persistence:
           - Default (strict_persistence=False): Persistence is a non-critical post-commit side effect.
             Disk write errors log diagnostics and set `last_persistence_succeeded = False`,
             but do NOT invalidate or revert the running session. Returns True on activation.
           - Strict mode (strict_persistence=True): Persistence failure causes transaction rollback
             to the previous locale and returns False.
        9. Subscriber isolation: Failure in one observer callback is recorded in `last_listener_failures`
           and does not prevent other subscribers from receiving notifications.
        """
        if self._is_switching:
            logger.warning("Rejected recursive set_locale() invocation.")
            return False

        if not locale_id or not isinstance(locale_id, str):
            logger.warning(f"Invalid locale identifier requested: {locale_id!r}")
            self._record_diagnostic("error", f"Invalid locale identifier requested: {locale_id!r}", locale_id=str(locale_id))
            return False

        raw_id = locale_id.strip()

        if not is_valid_locale_id(raw_id):
            msg = f"Invalid or malformed locale identifier format: {raw_id!r}"
            self._record_diagnostic("error", msg, locale_id=raw_id)
            logger.warning(msg)
            return False

        canon_target = canonicalize_locale_id(raw_id)

        # No-op if already active
        if raw_id == self._current_locale or canon_target == self._current_locale:
            return True

        # Resolve candidate catalog
        new_catalog = self.get_catalog(canon_target)
        if new_catalog is None:
            if self._discovery_directories:
                for disc_dir in self._discovery_directories:
                    self.discover_locales(disc_dir)
                new_catalog = self.get_catalog(canon_target)

        # Validate target catalog existence
        if new_catalog is None:
            msg = f"Requested locale '{canon_target}' is not available in registered catalogs."
            self._record_diagnostic("error", msg, locale_id=canon_target)
            logger.warning(msg)
            return False

        target_id = new_catalog.id
        if target_id == self._current_locale:
            return True

        validation_errors = new_catalog.validate()
        if validation_errors:
            msg = f"Candidate catalog '{target_id}' failed validation: {'; '.join(validation_errors)}"
            self._record_diagnostic("error", msg, locale_id=target_id)
            logger.warning(msg)
            return False

        old_locale = self._current_locale
        self._is_switching = True
        self._last_listener_failures = []
        self._last_refresh_completed = True

        try:
            # 1. Commit active locale identifier
            self._current_locale = target_id

            # 2. Synchronize layout direction with QApplication if available
            if _QT_AVAILABLE:
                app = QApplication.instance()
                if app is not None:
                    target_dir = Qt.RightToLeft if new_catalog.is_rtl else Qt.LeftToRight
                    app.setLayoutDirection(target_dir)

            # 3. Persist user preference
            if persist:
                try:
                    persisted = self._preferences.set_preferred_locale(target_id)
                    if not persisted:
                        self._last_persistence_succeeded = False
                        self._last_persistence_error = f"Preferences adapter could not write '{target_id}'"
                        self._record_diagnostic("warning", f"Could not persist preference for '{target_id}' to disk", locale_id=target_id)
                        if strict_persistence:
                            raise IOError(self._last_persistence_error)
                    else:
                        self._last_persistence_succeeded = True
                        self._last_persistence_error = None
                except Exception as pe:
                    self._last_persistence_succeeded = False
                    self._last_persistence_error = str(pe)
                    self._record_diagnostic("warning", f"Disk I/O error persisting locale preference: {pe}", locale_id=target_id)
                    if strict_persistence:
                        raise
            else:
                self._last_persistence_succeeded = True
                self._last_persistence_error = None

            # 4. Broadcast Qt signals safely
            if _QT_AVAILABLE:
                try:
                    self.locale_changed.emit(target_id)
                except Exception as se:
                    logger.error(f"Error during locale_changed signal emission: {se}")
                    self._record_diagnostic("warning", f"Signal emission warning: {se}", locale_id=target_id)
                    self._last_refresh_completed = False
                    self._last_listener_failures.append({"type": "qt_signal", "error": str(se)})

            # 5. Notify headless observers safely with subscriber isolation
            for listener in list(self._headless_listeners):
                try:
                    listener(target_id)
                except Exception as e:
                    logger.error(f"Error in locale listener callback: {e}")
                    self._record_diagnostic("warning", f"Listener callback error: {e}", locale_id=target_id)
                    self._last_refresh_completed = False
                    self._last_listener_failures.append({
                        "type": "headless_listener",
                        "callback": getattr(listener, "__name__", repr(listener)),
                        "error": str(e),
                    })

            logger.info(f"Switched application locale from '{old_locale}' to '{target_id}'")
            return True

        except Exception as e:
            # Atomic rollback to previous working locale and direction
            self._current_locale = old_locale
            if _QT_AVAILABLE:
                app = QApplication.instance()
                if app is not None:
                    old_cat = self._catalogs.get(old_locale)
                    if old_cat:
                        app.setLayoutDirection(Qt.RightToLeft if old_cat.is_rtl else Qt.LeftToRight)

            msg = f"Atomic rollback: Failed to commit locale switch to '{target_id}': {e}"
            self._record_diagnostic("error", msg, locale_id=target_id)
            logger.error(msg)
            return False

        finally:
            self._is_switching = False

    # -------------------------------------------------------------------------
    # Observers & Listeners
    # -------------------------------------------------------------------------

    def add_locale_listener(self, callback: Callable[[str], None]) -> None:
        """Register a callback invoked whenever the locale changes."""
        if callback not in self._headless_listeners:
            self._headless_listeners.append(callback)

    def remove_locale_listener(self, callback: Callable[[str], None]) -> None:
        """Unregister a locale change callback."""
        if callback in self._headless_listeners:
            self._headless_listeners.remove(callback)

    def clear_listeners(self) -> None:
        """Clear all registered headless observers."""
        self._headless_listeners.clear()
        self._last_listener_failures.clear()

    # -------------------------------------------------------------------------
    # Diagnostics & Developer Introspection
    # -------------------------------------------------------------------------

    def _record_diagnostic(self, level: str, message: str, locale_id: Optional[str] = None, key: Optional[str] = None) -> None:
        record = DiagnosticRecord(level=level, message=message, locale_id=locale_id, key=key)
        self._diagnostics.append(record)
        if len(self._diagnostics) > 500:
            self._diagnostics.pop(0)

    def _record_missing_key(self, key: str, locale_id: str) -> None:
        compound = f"{locale_id}:{key}"
        if compound not in self._missing_keys:
            self._missing_keys.add(compound)
            self._record_diagnostic("warning", f"Missing translation key '{key}'", locale_id=locale_id, key=key)

    def get_diagnostics(self) -> List[DiagnosticRecord]:
        """Return list of diagnostic events recorded during execution."""
        return list(self._diagnostics)

    def get_missing_keys(self) -> Set[str]:
        """Return all recorded missing keys."""
        return set(self._missing_keys)

    def clear_diagnostics(self) -> None:
        """Clear recorded diagnostics."""
        self._diagnostics.clear()
        self._missing_keys.clear()


def get_localization_manager() -> LocalizationManager:
    """Convenience accessor for LocalizationManager singleton."""
    return LocalizationManager.instance()


def t(key: str, default: Optional[str] = None, count: Optional[int] = None, **kwargs) -> str:
    """Global convenience translation function."""
    return get_localization_manager().translate(key=key, default=default, count=count, **kwargs)
