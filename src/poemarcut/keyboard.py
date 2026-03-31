"""Keyboard event handling for PoEMarcut."""

import contextlib
import logging
import platform
import time
from collections.abc import Callable
from threading import Lock
from typing import Any

import pyautogui
import pyperclip
from pynput.keyboard import Key, KeyCode, Listener

from poemarcut import constants, currency, settings
from poemarcut.item import Item, parse_int_price
from poemarcut.logic import (
    compute_discounted_price_and_actual,
    convert_and_compute_price,
)

# pydirectinput uses Windows-only APIs at import-time; import only on Windows
pydirectinput: Any | None = None
if platform.system() == "Windows":
    try:
        pydirectinput = __import__("pydirectinput")
    except ImportError:
        pydirectinput = None

logger = logging.getLogger(__name__)

# Module-level state to persist the last-extracted price/type between
# `on_release` invocations (the pynput listener calls this function per key
# event). Protect access with a lock to be safe if the listener runs on a
# separate thread.
_state_lock = Lock()
_last_price: int | None = None
_last_type: str | None = None

# Cache parsed bindings so we don't re-parse on every key event.
# Parsed binding format: ('special', Key) | ('char', str) | ('vk', int) | ('scan', int)
_parsed_keys_lock = Lock()
# Keep caches as mutable dicts so we can update in-place (avoid global rebind).
_cached_key_strs: dict[str, str] = {}
_parsed_keys: dict[str, tuple[str, Any]] = {}


def _match_char(event_key: Key | KeyCode | None, char: str) -> bool:
    """Return True if the event_key matches the provided character string.

    Args:
        event_key (Key | KeyCode | None): The event key from the listener.
        char (str): Single-character string to compare.

    Returns:
        bool: True if the event key represents the given character.

    """
    if not isinstance(event_key, KeyCode):
        return False
    if getattr(event_key, "char", None) == char:
        return True
    try:
        return KeyCode.from_char(char) == event_key
    except ValueError:
        return False


def binding_matches(event_key: Key | KeyCode | None, binding: tuple[str, Any]) -> bool:
    """Return True if the event key matches the parsed binding tuple.

    Binding tuples have shape `(type_str, value)` where `type_str` is one
    of: 'special', 'vk', 'scan', 'char'.

    Args:
        event_key (Key | KeyCode | None): The key event to match.
        binding (tuple[str, Any]): Parsed binding tuple.

    Returns:
        bool: True if the event matches the binding.

    """
    if not isinstance(binding, tuple) or len(binding) != 2:  # noqa: PLR2004
        return False

    binding_type, binding_value = binding

    if binding_type == "special":
        return event_key == binding_value

    if binding_type == "vk":
        return getattr(event_key, "vk", None) == binding_value

    if binding_type == "scan":
        return getattr(event_key, "scan", None) == binding_value

    if binding_type == "char":
        return _match_char(event_key, binding_value)

    # final fallback
    return event_key == binding_value


class KeyboardListenerManager:
    """Singleton manager that owns the `pynput` Listener and related state.

    Encapsulates the listener and a lock so callers don't rely on module
    globals. Use the module-level `_listener_manager` instance.
    """

    def __init__(self) -> None:
        """Initialize the manager's lock and listener state.

        Returns:
            None

        """
        self._lock = Lock()
        self._listener: Listener | None = None

    def start(
        self,
        *,
        blocking: bool = True,
        on_stop: Callable[[], None] | None = None,
    ) -> Listener | None:
        """Start and track a `pynput` Listener with the provided parameters.

        Returns: the started `Listener` when `blocking` is False, otherwise
        blocks until the listener exits and returns None.
        """

        def _on_release(key: Key | KeyCode | None) -> bool:
            """Wrap the module-level `on_release` used by the Listener.

            Args:
                key (Key | KeyCode | None): The released key event supplied by pynput.

            Returns:
                bool: True to continue listening, False to stop.

            """
            should_continue = on_release(key=key)
            if not should_continue and on_stop is not None:
                # Let on_stop exceptions propagate so they're visible to callers.
                on_stop()
            return should_continue

        listener = Listener(on_release=_on_release)  # type: ignore[arg-type]

        with self._lock:
            self._listener = listener

        if blocking:
            try:
                with listener:
                    listener.join()
            finally:
                with self._lock:
                    if self._listener is listener:
                        self._listener = None
            return None

        # Non-blocking: start the listener in a separate thread and return it.
        try:
            listener.start()
        except RuntimeError:
            logger.exception("리스너를 시작하는 중 오류가 발생했습니다.")
            # Ensure we don't keep a reference to a failed listener
            with self._lock:
                if self._listener is listener:
                    self._listener = None
            return None
        else:
            return listener

    def stop(self) -> None:
        """Stop the currently tracked listener, if any.

        Safe to call from another thread. No-op if there's no active listener.

        Returns:
            None

        """
        with self._lock:
            listener = self._listener
            self._listener = None

        if listener is None:
            return

        try:
            listener.stop()
            with contextlib.suppress(RuntimeError):
                listener.join(timeout=1.0)
        except RuntimeError:
            logger.exception("리스너를 중지하는 중 오류가 발생했습니다.")


# Module-level singleton instance
_listener_manager = KeyboardListenerManager()


def start_listener(
    *,
    blocking: bool = True,
    on_stop: Callable[[], None] | None = None,
) -> Listener | None:
    """Start the keyboard listener.

    Args:
        blocking (bool): Whether to block the main thread with the listener. If False, the listener will run in a separate thread.
        on_stop (Callable[[], None] | None): Optional callback invoked when
            the listener stops itself by handling the configured stop key.

    Returns:
        Listener | None: The started Listener when `blocking` is False, otherwise None.

    """
    # Delegate to the module-level singleton manager. The manager handles
    # storing and stopping the active Listener instance.
    return _listener_manager.start(
        blocking=blocking,
        on_stop=on_stop,
    )


def stop_listener() -> None:
    """Stop the active keyboard listener started by `start_listener`.

    This delegates to the `KeyboardListenerManager` singleton and is safe
    to call from another thread.

    Returns:
        None

    """
    _listener_manager.stop()


def on_release(  # noqa: C901, PLR0911, PLR0912, PLR0915
    key: Key | KeyCode | None,
) -> bool:
    """Handle pynput key release events.

    Args:
        key (Key | KeyCode | None): The released key.

    Returns:
        bool: True to continue listening, False to stop.

    """
    # Use module-level persisted state so the value extracted when the
    # `copyitem_key` is pressed is available later when `calcprice_key` is
    # pressed. Access is protected with `_state_lock`.
    global _last_price, _last_type

    if key is None:
        return True

    try:
        settings_manager: settings.SettingsManager = settings.settings_manager
        try:
            key_strs: dict[str, str] = settings_manager.settings.keys.model_dump()
        except (AttributeError, TypeError, ValueError):
            logger.exception("설정에서 키 바인딩을 읽는 중 오류가 발생했습니다.")
            return True

        with _parsed_keys_lock:
            if _cached_key_strs != key_strs:
                _parsed_keys.clear()
                for k, v in key_strs.items():
                    try:
                        _parsed_keys[k] = keyorkeycode_from_str(key_str=v)
                    except ValueError:
                        logger.exception("키 '%s'의 단축키 바인딩 '%s'이(가) 잘못되어 건너뜁니다.", k, v)
                        # skip invalid binding but keep listener running
                _cached_key_strs.clear()
                _cached_key_strs.update(key_strs)
        discount_percent: int = settings_manager.settings.logic.discount_percent

        max_actual_discount: int = settings_manager.settings.logic.max_actual_discount
        enter_after_calcprice: bool = settings_manager.settings.logic.enter_after_calcprice
        game: int = settings_manager.settings.currency.active_game
        league: str = settings_manager.settings.currency.active_league
        raw_currencies = (
            settings_manager.settings.currency.poe1currencies
            if game == 1
            else settings_manager.settings.currency.poe2currencies
        )
        currencies: list[str] = list(raw_currencies.keys())
        merchant_currency_prefixes = (
            constants.POE1_MERCHANT_CURRENCY_PREFIXES if game == 1 else constants.POE2_MERCHANT_CURRENCY_PREFIXES
        )

        # Helper to fetch parsed binding safely (may be missing if parsing failed)
        def _get_binding(name: str) -> tuple[str, Any] | None:
            """Retrieve a parsed binding by name from the module cache.

            Args:
                name (str): The settings key name for the binding.

            Returns:
                tuple[str, Any] | None: Parsed binding tuple or None if missing.

            """
            with _parsed_keys_lock:
                return _parsed_keys.get(name)

        copyitem_key = _get_binding("copyitem_key")
        rightclick_key = _get_binding("rightclick_key")
        calcprice_key = _get_binding("calcprice_key")
        enter_key = _get_binding("enter_key")
        stop_key = _get_binding("stop_key")

        if (
            copyitem_key is not None
            and isinstance(key, (Key, KeyCode))
            and binding_matches(event_key=key, binding=copyitem_key)
        ):
            logger.info("마우스를 올린 아이템에서 가격과 통화 종류를 추출하는 중입니다.")
            # If game is 2, hold alt beforehand to prevent item info from being pinned
            # Send ctrl+alt+c to copy hovered item text to clipboard
            if game == 2:  # noqa: PLR2004
                with pyautogui.hold("alt"):
                    pyautogui.hotkey("ctrl", "alt", "c")
            else:
                pyautogui.hotkey("ctrl", "alt", "c")
            item = Item.from_text(text=pyperclip.paste())
            if item is not None and item.note is not None:
                currency_label = constants.get_currency_display_name(item.note.currency or "", game=game)
                logger.info(
                    "마우스를 올린 아이템 '%s'에서 가격 '%s', 통화 '%s'을(를) 추출했습니다.",
                    item.name,
                    item.note.price,
                    currency_label,
                )
                price, cur_type = item.note.price, item.note.currency
            else:
                logger.warning(
                    "마우스를 올린 아이템에서 가격과 통화 종류를 추출하지 못했습니다. 클립보드 내용: %s",
                    pyperclip.paste(),
                )
                price, cur_type = None, None
            with _state_lock:
                _last_price, _last_type = price, cur_type

        if (
            rightclick_key is not None
            and isinstance(key, (Key, KeyCode))
            and binding_matches(event_key=key, binding=rightclick_key)
        ):
            logger.info("우클릭으로 가격 입력 창을 여는 중입니다.")
            # Right click to open price dialog
            # prefer to use pydirectinput because pyautogui.rightclick doesn't work properly in the game
            if platform.system() == "Windows" and pydirectinput is not None:
                pydirectinput.rightClick()
            else:
                pyautogui.rightClick()  # this doesn't work on Windows, untested on other platforms

        elif (
            calcprice_key is not None
            and isinstance(key, (Key, KeyCode))
            and binding_matches(event_key=key, binding=calcprice_key)
        ):
            logger.info("할인 가격을 계산하고 클립보드 및 가격 창을 갱신하는 중입니다.")
            # Copy (pre-selected) price to the clipboard
            # use pyautogui because it sends keys faster
            pyautogui.hotkey("ctrl", "c")

            with _state_lock:
                last_price, last_cur_type = _last_price, _last_type

            try:
                raw_clip = pyperclip.paste()
                try:
                    # Parse current price from clipboard. Strip any thousands separators (locale dependent).
                    copied_price: int = parse_int_price(raw_clip)
                except ValueError:
                    logger.warning(
                        "클립보드 값 '%s'은(는) 올바른 정수가 아닙니다. 가격 계산을 중단합니다.",
                        raw_clip,
                    )
                    return True  # do nothing if clipboard value is not a valid int

                if (
                    last_price is not None and last_price != copied_price
                ):  # sanity check that both parsed prices are the same
                    logger.warning(
                        "클립보드 가격(%d)이 예상한 이전 가격(%d)과 일치하지 않습니다. 가격 계산을 중단합니다.",
                        copied_price,
                        last_price,
                    )
                    return True  # do nothing if clipboard price doesn't match previously parsed price

                if copied_price < 1:
                    logger.error("파싱된 가격이 1보다 작습니다(%d). 가격 계산을 중단합니다.", copied_price)
                    return True  # do nothing if current price is less than 1

                # if we don't know the currency type and assume_highest is enabled, assume the currency type is the highest
                if not last_cur_type and settings_manager.settings.currency.assume_highest_currency:
                    last_price = copied_price
                    last_cur_type = currencies[0] if currencies else None

                # Compute integer discounted price and observed percent after integer rounding.
                discounted_price_candidate, actual_discount = compute_discounted_price_and_actual(
                    copied_price, discount_percent
                )
                next_cur_type: str | None = None
                # if we can't go lower because price is 1 or the calculated percent discount
                # exceeds the allowed maximum, bail out or try converting to the next currency
                if copied_price == 1 or actual_discount > float(max_actual_discount):
                    # and if we know the copied currency type and it's in our list of convertible currencies and it's not the final currency
                    if (
                        last_cur_type is not None
                        and last_cur_type in currencies
                        and last_cur_type != list(currencies)[-1]
                    ):
                        # Ensure max_actual_discount is respected but apply discount_percent otherwise when possible.
                        amount_units = int(last_price or copied_price)

                        def _get_rate(*, from_currency: str, to_currency: str) -> float:
                            return currency.get_exchange_rate(
                                game=game,
                                league=league,
                                from_currency=from_currency,
                                to_currency=to_currency,
                                autoupdate=settings_manager.settings.currency.autoupdate,
                            )

                        converted_price, converted_currency, converted_actual = convert_and_compute_price(
                            original_units=amount_units,
                            last_cur_type=last_cur_type,
                            currencies=currencies,
                            discount_percent=discount_percent,
                            max_actual_discount=max_actual_discount,
                            get_exchange_rate=_get_rate,
                        )

                        if converted_price is None:
                            logger.info(
                                "최대 실제 할인율 %.2f%%를 지키는 환산 경로를 찾지 못했습니다. 가격을 조정하지 않습니다.",
                                max_actual_discount,
                            )
                            return True

                        discounted_price_candidate = converted_price
                        actual_discount = converted_actual
                        next_cur_type = converted_currency
                    elif copied_price == 1:
                        current_currency = (
                            constants.get_currency_display_name(last_cur_type, game=game) if last_cur_type else "알 수 없음"
                        )
                        logger.info(
                            "가격이 1 %s이지만 다음 통화로 환산할 수 없습니다. 통화 종류를 모르거나, 환산 목록에 없거나, 마지막 통화입니다.",
                            current_currency,
                        )
                        return True  # do nothing if parsed int is 1 and we do not know the currency type or it's the final type
                    elif actual_discount > float(max_actual_discount):
                        logger.info(
                            "계산된 할인율 %.2f%%가 허용 최대 할인율 %.2f%%를 초과했습니다. 가격을 조정하지 않습니다.",
                            actual_discount,
                            max_actual_discount,
                        )
                        return True  # do nothing if the calculated discount exceeds the maximum allowed discount

                # Use the precomputed integer discounted price
                new_price: int = discounted_price_candidate

                # Small delay before pasting to ensure the price dialog is ready for input
                time.sleep(settings_manager.settings.logic.price_delay)

                # Paste the new price from clipboard
                logger.info(
                    "새 가격 '%d'을(를) 붙여넣습니다. 이전 가격은 '%d'이었습니다. (%.2f%%)",
                    new_price,
                    copied_price,
                    actual_discount,
                )
                pyperclip.copy(str(new_price))
                pyautogui.hotkey("ctrl", "v")

                # Change currency dropdown if currency was converted
                if next_cur_type is not None:
                    logger.info(
                        "드롭다운에서 다음 통화 '%s'을(를) 선택하는 중입니다.",
                        constants.get_currency_display_name(next_cur_type, game=game),
                    )
                    # tab to switch focus to currency dropdown
                    pyautogui.press("tab")
                    time.sleep(0.6)  # long delay is needed for the dropdown to be ready

                    # 한국어/영어 클라이언트 공통: 인덱스 차이를 방향키로 이동
                    # (한국어 클라이언트는 영문 prefix 타이핑이 동작하지 않으므로
                    #  prefix 길이와 무관하게 항상 화살표 키 방식을 사용)
                    if last_cur_type is not None and last_cur_type in merchant_currency_prefixes:
                        cur_index = list(merchant_currency_prefixes.keys()).index(last_cur_type)
                        target_index = list(merchant_currency_prefixes.keys()).index(next_cur_type)
                        index_diff = target_index - cur_index
                        if index_diff > 0:
                            for _ in range(index_diff):
                                pyautogui.press("down")
                                time.sleep(0.1)
                        elif index_diff < 0:
                            for _ in range(-index_diff):
                                pyautogui.press("up")
                                time.sleep(0.1)
                        # index_diff == 0 이면 이미 올바른 항목 선택됨
                    else:
                        logger.warning(
                            "다음 통화를 선택할 수 없습니다. 현재 통화 종류 '%s'을(를) 모르거나 prefix 맵에 없습니다.",
                            last_cur_type,
                        )
                        return True  # do nothing

                    # enter to confirm the dropdown selection
                    pyautogui.press("enter")

                if enter_after_calcprice:
                    # Press enter to confirm new price
                    pyautogui.press("enter")
            finally:
                # Clear persisted price/type since it was processed and is no longer valid.
                with _state_lock:
                    _last_price, _last_type = None, None

        elif (
            enter_key is not None
            and isinstance(key, (Key, KeyCode))
            and binding_matches(event_key=key, binding=enter_key)
        ):
            if not enter_after_calcprice:
                # Press enter to confirm new price
                pyautogui.press("enter")
        elif (
            stop_key is not None
            and isinstance(key, (Key, KeyCode))
            and binding_matches(event_key=key, binding=stop_key)
        ):
            logger.info("중지 키가 눌려 리스너를 종료합니다.")
            return False

    except (
        OSError,
        RuntimeError,
        pyautogui.FailSafeException,
        LookupError,
        pyperclip.PyperclipException,
    ):
        logger.exception("키 해제 이벤트를 처리하는 중 오류가 발생했습니다.")

    return True


def keyorkeycode_from_str(key_str: str) -> tuple[str, Any]:
    """Convert a string representation of a key to a pynput Key or KeyCode.

    This is unfortunately necessary because pynput does not provide the from_char method for both.

    Args:
        key_str (str): The string representation of the key, e.g. 'f3', 'a', etc.

    Returns:
        Key | KeyCode: The corresponding Key or KeyCode object.

    """
    key_str = key_str.strip()
    # Support vk:<int> and scan:<int> formats for layout-independent bindings
    if key_str.startswith("vk:"):
        try:
            return ("vk", int(key_str.split(":", 1)[1]))
        except (ValueError, TypeError) as e:
            msg = f"Invalid vk binding: {key_str}"
            raise ValueError(msg) from e
    if key_str.startswith("scan:"):
        try:
            return ("scan", int(key_str.split(":", 1)[1]))
        except (ValueError, TypeError) as e:
            msg = f"Invalid scan binding: {key_str}"
            raise ValueError(msg) from e

    # Check if it's a special key in the Key enum
    try:
        special_key = getattr(Key, key_str.lower(), None)
        if special_key is not None:
            return ("special", special_key)
    except AttributeError as e:
        msg = f"Invalid key string: {key_str}"
        raise ValueError(msg) from e

    # Otherwise, treat it as a regular character key
    if len(key_str) != 1:
        msg = f"Invalid key string: {key_str}"
        raise ValueError(msg)
    # store char bindings as ('char', <single-char>)
    return ("char", key_str)
