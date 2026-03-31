"""Get and save settings for PoEMarcut.

Defines default settings and settings file location.
"""

import logging
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path
from typing import Literal, cast

from pydantic import BaseModel, Field, ValidationError, field_serializer, field_validator, model_validator
from PyQt6.QtCore import QObject, pyqtSignal
from yaml import SafeDumper, SafeLoader, YAMLError, dump, load
from yaml.nodes import SequenceNode

from poemarcut import constants, currency

logger = logging.getLogger(__name__)


def _yaml_represent_set(dumper: SafeDumper, data: set) -> SequenceNode:
    return dumper.represent_sequence("!!python/set", list(data))


def _yaml_construct_set(loader: SafeLoader, node: SequenceNode) -> set:
    seq = loader.construct_sequence(node)
    return set(seq)


SafeDumper.add_representer(set, _yaml_represent_set)
SafeLoader.add_constructor("!!python/set", _yaml_construct_set)


SETTINGS_FILE = Path.cwd() / "settings.yaml"


class KeySettings(BaseModel):
    """Keyboard hotkey settings."""

    copyitem_key: str = Field(
        default="f1",
        description="보관함 또는 거래 탭에서 마우스를 올린 아이템의 Ctrl+Alt+C 텍스트를 복사합니다. 가격과 통화 종류도 포함됩니다.",
    )
    rightclick_key: str = Field(
        default="f2", description="거래/보관함 탭에서 아이템 가격 입력 창을 열기 위해 우클릭을 실행합니다."
    )
    calcprice_key: str = Field(
        default="f3",
        description="기존 가격을 복사해 새 가격을 계산한 뒤 입력 창에 붙여넣습니다. 필요하면 Enter까지 자동으로 누릅니다.",
    )
    enter_key: str = Field(default="f4", description="가격 입력 창에서 새 가격을 Enter로 확정합니다.")
    stop_key: str = Field(default="f6", description="다시 활성화할 때까지 단축키 감지를 중지합니다.")

    @field_validator("copyitem_key", "rightclick_key", "calcprice_key", "enter_key", "stop_key")
    @classmethod
    def validate_keys(cls, key: str) -> str:
        """Validate that keys are not empty.

        Args:
            key (str): Candidate key string to validate.

        Returns:
            str: The validated key string.

        """
        if not key:
            msg = "Key cannot be empty"
            raise ValueError(msg)
        return key


class LogicSettings(BaseModel):
    """Logic and calculation settings for price adjustments."""

    # User-facing value: discount percent (0-100). Stored in YAML as percent for clarity.
    discount_percent: int = Field(
        default=10,
        ge=1,
        le=99,
        description="현재 가격에 적용할 할인율입니다. 예를 들어 100에 10% 할인을 적용하면 90이 됩니다.",
    )

    # Maximum allowed discount percent (user-facing). For example, 50.0 means
    # the price calculation will not apply discounts greater than 50%.
    max_actual_discount: int = Field(
        default=50,
        ge=1,
        le=99,
        description="허용할 최대 할인율입니다. 계산된 할인율이 이 값을 넘으면 가격을 다른 통화로 환산하거나 조정하지 않습니다.",
    )
    enter_after_calcprice: bool = Field(
        default=True,
        description="참이면 새 가격을 계산해 붙여넣은 뒤 Enter를 자동으로 누릅니다. 거짓이면 자동으로 누르지 않습니다.",
    )
    price_delay: float = Field(
        default=0.2,
        ge=0.1,
        le=5.0,
        description="가격 입력 창을 연 뒤 새 가격을 붙여넣기 전까지의 지연 시간(초)입니다.",
    )


class WindowPosition(BaseModel):
    """Window position with explicit x/y coordinates."""

    x: int = Field(default=400, description="메인 창의 X 좌표입니다.")
    y: int = Field(default=100, description="메인 창의 Y 좌표입니다.")


class WindowSize(BaseModel):
    """Window size with explicit width/height."""

    width: int = Field(default=450, description="메인 창의 너비입니다.")
    height: int = Field(default=400, description="메인 창의 높이입니다.")


class GuiSettings(BaseModel):
    """GUI settings for PoEMarcut."""

    position: WindowPosition = Field(default_factory=WindowPosition, description="메인 창 위치입니다.")
    size: WindowSize = Field(default_factory=WindowSize, description="메인 창 크기입니다.")
    always_on_top: bool = Field(
        default=False, description="메인 창을 항상 다른 창 위에 표시할지 여부입니다."
    )
    minimize_to_tray: bool = Field(
        default=False, description="작업 표시줄 대신 시스템 트레이로 최소화할지 여부입니다."
    )


class CurrencySettings(BaseModel):
    """Currency update settings."""

    autoupdate: bool = Field(
        default=True,
        description="참이면 최신 통화 시세를 가져오고, 거짓이면 캐시 또는 수동 설정 값만 사용합니다.",
    )
    poe1leagues: set[str] = Field(
        default_factory=lambda: {"tmpstandard", "tmphardcore"}, description="사용 가능한 PoE1 거래 리그 목록입니다."
    )
    poe2leagues: set[str] = Field(
        default_factory=lambda: {"tmpstandard", "tmphardcore"}, description="사용 가능한 PoE2 거래 리그 목록입니다."
    )
    poe1currencies: dict[str, int] = Field(
        default_factory=lambda: {"divine": 1, "chaos": 100},
        description="PoE1 통화 목록과 최상위 통화 기준 상대값입니다.",
    )
    poe2currencies: dict[str, int] = Field(
        default_factory=lambda: {"divine": 1, "chaos": 30, "exalted": 240},
        description="PoE2 통화 목록과 최상위 통화 기준 상대값입니다.",
    )
    assume_highest_currency: bool = Field(
        default=True,
        description="실제 통화 종류를 알 수 없으면 현재 수정 중인 값을 최상위 통화로 가정합니다.",
    )
    active_game: Literal[1, 2] = Field(
        default=1,
        description="통화 시세에 사용할 현재 게임입니다. 1은 PoE1, 2는 PoE2입니다.",
    )
    active_league: str = Field(default="tmpstandard", description="통화 시세를 가져올 현재 리그입니다.")

    @field_serializer("poe1leagues", "poe2leagues", mode="plain")
    def _serialize_leagues(self, v: object) -> object:
        """Ensure `poe1leagues`/`poe2leagues` serialize as Python `set` objects.

        Pydantic may produce `list` during serialization in some code paths;
        returning a `set` here keeps the runtime type so the YAML dumper
        emits the `!!python/set` tag via the registered SafeDumper.
        """
        if isinstance(v, (list, tuple)):
            return set(v)
        return v

    @contextmanager
    def delay_validation(self) -> Generator[None, None, None]:
        """Context manager that temporarily disables validation during assignment of multiple attributes dependent on each other.

        Yields:
            None

        Returns:
            Generator[None, None, None]: A context manager generator that yields None.

        Raises:
            ValidationError: If validation fails when the context manager exits.

        """
        # Capture a lightweight snapshot (model_dump returns a fresh dict).
        original_state = self.model_dump()

        original_validate_assignment = self.model_config.get("validate_assignment", True)
        self.model_config["validate_assignment"] = False
        try:
            yield
        finally:
            self.model_config["validate_assignment"] = original_validate_assignment

        try:
            # Re-validate by constructing a fresh instance from the current dump.
            validated = self.__class__(**self.model_dump())
            for k, v in validated.model_dump().items():
                setattr(self, k, v)
        except (ValidationError, TypeError, ValueError):
            # Restore the original state on failure.
            for k, v in original_state.items():
                setattr(self, k, v)
            raise

    @model_validator(mode="after")
    def ensure_league_in_game_list(self) -> "CurrencySettings":
        """Validate that active_league is in the appropriate list of leagues based on active_game.

        Returns:
            CurrencySettings: Self, potentially mutated to correct leagues.

        """
        poe1 = self.poe1leagues or set()
        poe2 = self.poe2leagues or set()

        if self.active_game == 1 and self.active_league not in poe1:
            if not poe1:
                self.poe1leagues = {self.active_league}
                msg = f"No PoE1 leagues defined, setting active league '{self.active_league}' as the only PoE1 league."
                logger.warning(msg)
                return self
            msg = f"'{self.active_league}' must be in {poe1}, setting active league to '{next(iter(poe1))}'."
            logger.warning(msg)
            self.active_league = next(iter(poe1))
        if self.active_game == 2 and self.active_league not in poe2:  # noqa: PLR2004
            if not poe2:
                self.poe2leagues = {self.active_league}
                msg = f"No PoE2 leagues defined, setting active league '{self.active_league}' as the only PoE2 league."
                logger.warning(msg)
                return self
            msg = f"'{self.active_league}' must be in {poe2}, setting active league to '{next(iter(poe2))}'."
            logger.warning(msg)
            self.active_league = next(iter(poe2))
        return self

    @model_validator(mode="after")
    def ensure_leagues_nonempty(self) -> "CurrencySettings":
        """Ensure `poe1leagues` and `poe2leagues` are never empty.

        If a league set is empty, prefer to set it to `active_league` when
        available; otherwise fall back to well-known defaults.

        Returns:
            CurrencySettings: self, potentially mutated.

        """
        for field in ("poe1leagues", "poe2leagues"):
            val = getattr(self, field) or set()
            if not val:
                active = getattr(self, "active_league", None)
                # Only use active_league for the matching active_game.
                if active and (
                    (field == "poe1leagues" and self.active_game == 1)
                    or (field == "poe2leagues" and self.active_game == 2)  # noqa: PLR2004
                ):
                    setattr(self, field, {active})
                    logger.warning(
                        "No %s defined; setting to active_league %r for active_game %s", field, active, self.active_game
                    )
                else:
                    # Use the field's declared default by instantiating a fresh
                    # CurrencySettings and reading the attribute. This keeps the
                    # fallback in sync with the Field default_factory above.
                    defaults = CurrencySettings()
                    setattr(self, field, getattr(defaults, field))
                    logger.warning("No %s defined; resetting to model default values", field)
        return self

    @model_validator(mode="after")
    def validate_currency_mappings(self) -> "CurrencySettings":
        """Validate `poe1currencies` and `poe2currencies` mappings.

        - Requires a dict mapping currency->int units per highest currency.
        - Orders the dict by numeric value (ascending: most valuable -> least).
        - Ensures the smallest value is exactly 1; otherwise raises ValueError.

        Returns:
            CurrencySettings: Self, normalized and validated.

        """
        for attr in ("poe1currencies", "poe2currencies"):
            raw = getattr(self, attr)

            if not isinstance(raw, dict):
                msg = f"{attr} must be a mapping of currency->int units (dict), got {type(raw).__name__}"
                raise TypeError(msg)

            # Ensure all keys are strings and values are positive ints.
            raw_map: dict[str, int] = {}
            # Choose per-game valid currency keys
            valid_keys = (
                constants.POE1_MERCHANT_CURRENCIES if attr == "poe1currencies" else constants.POE2_MERCHANT_CURRENCIES
            )
            for k, v in raw.items():
                # Normalize key to canonical merchant id (lowercase)
                k_norm = str(k).lower()
                if k_norm not in valid_keys:
                    msg = f"{attr} mapping key '{k}' is not a recognized merchant currency short name for this game"
                    raise ValueError(msg)
                try:
                    iv = int(v)
                except (TypeError, ValueError) as _err:
                    msg = f"{attr} mapping value for '{k}' is not an integer: {v!r}"
                    raise ValueError(msg) from None
                if iv <= 0:
                    msg = f"{attr} mapping value for '{k}' must be a positive integer, got {iv}"
                    raise ValueError(msg)
                raw_map[k_norm] = iv

            if not raw_map:
                setattr(self, attr, {})
                continue

            # Order by value (ascending: most valuable -> least valuable)
            ordered_items = sorted(raw_map.items(), key=lambda kv: kv[1])

            # The smallest value must be exactly 1; otherwise refuse and raise.
            min_val = ordered_items[0][1]
            if min_val != 1:
                msg = f"{attr} mapping must have smallest unit == 1, got {min_val}"
                raise ValueError(msg)

            # Rebuild ordered dict preserving the computed order
            normalized = {k: int(v) for k, v in ordered_items}
            setattr(self, attr, normalized)

        return self


class PoEMSettings(BaseModel):
    """Settings for PoEMarcut."""

    keys: KeySettings
    logic: LogicSettings
    gui: GuiSettings
    currency: CurrencySettings


class SettingsManager(QObject):
    """Manages the application settings, including loading from and saving to a YAML file."""

    # emits (field name, new_value) when a setting is changed
    settings_changed = pyqtSignal(str, object)

    def __init__(self) -> None:
        """Initialize the SettingsManager and load settings from file.

        Returns:
            None

        """
        super().__init__()
        self._settings = self._load_settings()

    @property
    def settings(self) -> PoEMSettings:
        """Get the current application settings.

        Returns:
            PoEMSettings: The current settings object.

        """
        # Return cached settings. Use `reload_settings()` to force reloading
        # from disk when necessary. Avoid reloading on every access which can
        # be expensive (parsing/validation + file I/O).
        return self._settings

    def reload_settings(self) -> PoEMSettings:
        """Force reloading settings from disk and return the fresh settings.

        Returns:
            PoEMSettings: The reloaded settings object.

        """
        self._settings = self._load_settings()
        return self._settings

    def _load_settings(self) -> PoEMSettings:  # noqa: C901, PLR0912, PLR0915
        """Get PoEMSettings from settings.yaml, or return default settings if file is missing or invalid.

        Returns:
            PoEMSettings: Loaded or default settings object.

        """
        # Build a safe default to fall back to in any failure case
        default = PoEMSettings(
            keys=KeySettings(), logic=LogicSettings(), currency=CurrencySettings(), gui=GuiSettings()
        )

        try:
            with SETTINGS_FILE.open() as f:
                try:
                    raw = load(f, Loader=SafeLoader)
                except (YAMLError, ValidationError):
                    logger.exception("Error parsing settings YAML; using defaults")
                    try:
                        self.set_settings(default)
                    except (OSError, YAMLError, TypeError, ValidationError):
                        logger.exception("Failed to persist default settings after parse error: %s")
                    return default
        except FileNotFoundError:
            logger.warning("Settings file not found, using default settings and creating settings file")
            self.set_settings(default)
            return default

        if not isinstance(raw, dict):
            logger.warning("Settings file did not contain a mapping; using defaults")
            try:
                self.set_settings(default)
            except (OSError, YAMLError, TypeError, ValidationError):
                logger.exception("Failed to persist default settings for non-mapping YAML: %s")
            return default

        # Section handlers: (ModelClass, default_instance)
        # Use fresh default instances per-section to avoid accidental mutation
        # of the `default` PoEMSettings nested objects during validation.
        sections = {
            "keys": (KeySettings, KeySettings()),
            "logic": (LogicSettings, LogicSettings()),
            "currency": (CurrencySettings, CurrencySettings()),
            "gui": (GuiSettings, GuiSettings()),
        }

        validated: dict[str, BaseModel] = {}

        for name, (cls, default_instance) in sections.items():
            raw_section = raw.get(name, {}) or {}
            if not isinstance(raw_section, dict):
                logger.warning("Settings.%s is not a mapping; ignoring user value", name)
                raw_section = {}

            # Start from the default instance
            current = default_instance

            # If the model provides a delay_validation context manager, use it
            # to set interdependent fields together without triggering
            # partially-applied validators (avoids spurious warnings).
            if hasattr(current, "delay_validation"):
                try:
                    with current.delay_validation():
                        current_dict = current.model_dump()
                        for field_name, val in raw_section.items():
                            if field_name not in current_dict:
                                logger.debug("Unknown setting %s.%s - ignoring", name, field_name)
                                continue
                            setattr(current, field_name, val)
                except (ValidationError, TypeError, ValueError):
                    logger.warning("Invalid values in settings.%s; falling back to defaults", name)
                    current = default_instance
            else:
                # Fall back to per-field trial instantiation for models without delay_validation
                current_dict = current.model_dump()
                for field_name, val in raw_section.items():
                    if field_name not in current_dict:
                        logger.debug("Unknown setting %s.%s - ignoring", name, field_name)
                        continue
                    trial = current_dict.copy()
                    trial[field_name] = val
                    try:
                        current = cls(**trial)
                        current_dict = current.model_dump()
                    except (ValidationError, TypeError, ValueError):
                        logger.warning("Invalid value for %s.%s: %r; falling back to default", name, field_name, val)

            validated[name] = current

        # Reconstruct each section to ensure any remaining invalid nested values
        # are replaced with per-section defaults rather than falling back to the
        # entire settings object.
        cleaned: dict[str, BaseModel] = {}
        for name, (cls, default_instance) in sections.items():
            candidate = validated.get(name, default_instance)
            try:
                # Ensure the candidate can be re-instantiated/validated as its class
                if isinstance(candidate, BaseModel):
                    cleaned[name] = cls(**candidate.model_dump())
                else:
                    cleaned[name] = cls(**(candidate or {}))
            except (ValidationError, TypeError, ValueError):
                logger.warning("Invalid values in finalized settings.%s; falling back to defaults", name)
                cleaned[name] = default_instance

        try:
            # Construct final settings without re-running nested validation. We
            # already validated/cleaned each section above; constructing without
            # validation avoids a single nested failure causing a full fallback.
            settings = PoEMSettings.model_construct(
                keys=cast("KeySettings", cleaned["keys"]),
                logic=cast("LogicSettings", cleaned["logic"]),
                currency=cast("CurrencySettings", cleaned["currency"]),
                gui=cast("GuiSettings", cleaned["gui"]),
            )

        except (ValidationError, TypeError, ValueError):
            logger.exception("Failed to compose final PoEMSettings, falling back to defaults")
            try:
                self.set_settings(default)
            except (OSError, YAMLError, TypeError, ValidationError):
                logger.exception("Failed to persist default settings after final composition failure: %s")
            return default

        return settings

    def set_settings(self, new_settings: PoEMSettings) -> None:
        """Set the settings in settings.yaml, overwriting or creating file.

        Args:
            new_settings (PoEMSettings): The new settings to persist.

        Returns:
            None

        """
        # Compute diff against current cached settings and emit signals only
        # for fields that changed. This avoids triggering many UI updates when
        # only a single field was modified.
        try:
            old_dump = self._settings.model_dump() if getattr(self, "_settings", None) is not None else {}
        except (AttributeError, TypeError, ValueError):
            old_dump = {}

        # Reconstruct validated settings object and assign. Accept partial
        # `model_construct`-style inputs by falling back to fresh defaults
        # when nested sections are missing.
        keys_src = getattr(new_settings, "keys", KeySettings())
        logic_src = getattr(new_settings, "logic", LogicSettings())
        currency_src = getattr(new_settings, "currency", CurrencySettings())
        gui_src = getattr(new_settings, "gui", GuiSettings())

        self._settings = PoEMSettings(
            keys=KeySettings(**keys_src.model_dump()),
            logic=LogicSettings(**logic_src.model_dump()),
            currency=CurrencySettings(**currency_src.model_dump()),
            gui=GuiSettings(**gui_src.model_dump()),
        )

        with SETTINGS_FILE.open("w") as f:
            data = self._settings.model_dump()
            currency_section = data.get("currency", {}) or {}

            # Ensure league fields are persisted as non-empty sets. If the
            # current value is empty (or an empty list), replace it with the
            # model default to avoid writing empty sequences/sets to disk.
            defaults = CurrencySettings()
            for field in ("poe1leagues", "poe2leagues"):
                val = currency_section.get(field)
                if isinstance(val, list):
                    val = set(val)
                # Normalize falsy/empty values to the model default
                if not val:
                    val = getattr(defaults, field)
                currency_section[field] = val

            data["currency"] = currency_section
            dump(data, f, sort_keys=False, Dumper=SafeDumper)

        # Emit changed-field signals only
        new_dump = self._settings.model_dump()
        for category, cat_fields in new_dump.items():
            old_cat = old_dump.get(category) or {}
            for field_name, new_val in cat_fields.items():
                old_val = old_cat.get(field_name)
                if old_val != new_val:
                    self.settings_changed.emit(f"{category}.{field_name}", new_val)

    def add_currency_and_persist(self, *, game: int, setting_field: str, chosen_key: str) -> None:
        """Insert `chosen_key` into the appropriate position and persist updated mapping.

        Uses helpers in `poemarcut.currency` to compute ordering and mapping based on
        live exchange rates (falls back to existing stored values on error).

        Args:
            game (int): Game id (1 or 2) indicating which currency mapping to update.
            setting_field (str): Field name on `CurrencySettings` to update (e.g. 'poe1currencies').
            chosen_key (str): Currency id to insert.

        Returns:
            None

        """
        settings_obj = self.settings
        currency_settings = settings_obj.currency
        raw = getattr(currency_settings, setting_field) or {}
        current_order = list(raw.keys())

        new_order = currency.compute_new_order(
            game=game,
            league=currency_settings.active_league,
            current_order=current_order,
            chosen_key=chosen_key,
            autoupdate=currency_settings.autoupdate,
        )
        new_mapping = currency.compute_mapping_from_order(
            game=game,
            league=currency_settings.active_league,
            ordered=new_order,
            existing_raw=raw,
            autoupdate=currency_settings.autoupdate,
        )

        setattr(settings_obj.currency, setting_field, new_mapping)
        # Avoid mutating the manager's cached settings in-place. Build a
        # fresh validated settings object and persist that so
        # SettingsManager.set_settings can compute diffs and emit signals.
        current = self.settings
        new_settings = PoEMSettings(
            keys=KeySettings(**current.keys.model_dump()),
            logic=LogicSettings(**current.logic.model_dump()),
            currency=CurrencySettings(**current.currency.model_dump()),
            gui=GuiSettings(**current.gui.model_dump()),
        )
        setattr(new_settings.currency, setting_field, new_mapping)
        self.set_settings(new_settings)


# Module-level shared SettingsManager instance for easy access by other modules.
# Use this singleton to ensure signals and state are centralized.
settings_manager = SettingsManager()
