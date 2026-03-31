# ruff: noqa: T201 # disable print() warning since this is the CLI
"""Tool to quickly reprice Path of Exile 1/2 merchant tab items.

Also works for stash tab items, but you'll have to select the price text yourself.

On start, prints a list of suggested new prices for 1-unit currency items based on current poe.ninja currency prices.
"""

import logging
import sys
import time

from poemarcut import constants, currency, keyboard, settings, update
from poemarcut.__init__ import __version__
from poemarcut.constants import BOLD, RESET, S_IN_HOUR


def _currency_name(game: int, currency_id: str) -> str:
    return constants.get_currency_display_name(currency_id, game=game)


def print_last_updated(game: int, league: str, file_mtime: float) -> None:
    """Print when the currency data was last updated from the cache file.

    Args:
        game (int): The game version, either 1 (PoE1) or 2 (PoE2).
        league (str): The league name.
        file_mtime (float): The mtime of the cache file.

    Returns:
        None

    """
    time_diff = time.time() - file_mtime
    diff_hours = int(time_diff // S_IN_HOUR)
    diff_mins = int((time_diff % S_IN_HOUR) // 60)
    updated_at = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(file_mtime))
    print(
        f"(PoE{game} '{league}' 통화 데이터 최근 갱신: {diff_hours}시간 {diff_mins:02d}분 전 ({updated_at}))"
    )


def print_poe1_currency_suggestions(discount_percent: int, data: dict) -> None:
    """Print suggested new currency prices for PoE1 based on current poe.ninja currency values.

    Args:
        discount_percent (float): The discount percent to apply (0-100).
        data (dict): The currency data fetched from poe.ninja.

    Returns:
        None

    """
    if "lines" in data and "core" in data and data["core"].get("primary"):
        if data["core"]["primary"] == "chaos" and data["core"].get("rates") and data["core"]["rates"].get("divine"):
            chaos_div_val: float = data["core"]["rates"]["divine"]
        elif data["core"]["primary"] == "divine" and data["core"].get("rates") and data["core"]["rates"].get("chaos"):
            chaos_div_val: float = 1 / data["core"]["rates"]["chaos"]
        elif any((item.get("id") == "chaos") for item in data.get("lines", [])):
            chaos_div_val: float = next(item for item in data.get("lines", []) if item.get("id") == "chaos")[
                "primaryValue"
            ]
        else:
            print("오류: 잘못된 데이터라 PoE1 통화 추천값을 계산할 수 없습니다.", file=sys.stderr)
            return

        div_chaos_adj: float = 1 / chaos_div_val * (1.0 - (discount_percent / 100.0))
        print(f"{BOLD}PoE1{RESET} 현재 시세 기준, 현재 설정값이 1일 때 추천 통화 설정:")
        print(
            f"{discount_percent:.2f}% 할인 ({(1.0 - discount_percent / 100.0):.2f}배) {_currency_name(1, 'divine')} 1개"
        )
        print(f" = {int(div_chaos_adj)} {_currency_name(1, 'chaos')} ({div_chaos_adj:.2f})")
        print(f"{(1.0 - discount_percent / 100.0):.2f}배 {_currency_name(1, 'chaos')} 1개")
        print(" = 그냥 상점에 파세요!")
    else:
        print("오류: 잘못된 데이터라 PoE1 통화 추천값을 계산할 수 없습니다.", file=sys.stderr)


def print_poe2_currency_suggestions(discount_percent: int, data: dict) -> None:
    """Print suggested new currency prices for PoE2 based on current poe.ninja currency values.

    Some calculations are inverted depending on if poe.ninja provides "div per X" or "X per div".

    Args:
        discount_percent (float): The discount percent to apply (0-100).
        data (dict): The currency data fetched from poe.ninja.

    Returns:
        None

    """  # Compute multiplier from discount_percent inline where needed
    if (
        "lines" in data
        and "core" in data
        and data["core"].get("primary")
        and any((item.get("id") == "annul") for item in data.get("lines", []))
        and any((item.get("id") == "chaos") for item in data.get("lines", []))
        and any((item.get("id") == "exalted") for item in data.get("lines", []))
    ):
        annul_div_val: float = next(item for item in data.get("lines", []) if item.get("id") == "annul")["primaryValue"]
        chaos_div_val: float = next(item for item in data.get("lines", []) if item.get("id") == "chaos")["primaryValue"]
        exalt_div_val: float = next(item for item in data.get("lines", []) if item.get("id") == "exalted")[
            "primaryValue"
        ]

        div_annul_adj: float = 1 / annul_div_val * (1.0 - (discount_percent / 100.0))
        div_chaos_adj: float = 1 / chaos_div_val * (1.0 - (discount_percent / 100.0))
        div_exalt_adj: float = 1 / exalt_div_val * (1.0 - (discount_percent / 100.0))
        annul_chaos_adj: float = 1 / chaos_div_val * annul_div_val * (1.0 - (discount_percent / 100.0))
        annul_exalt_adj: float = 1 / exalt_div_val * annul_div_val * (1.0 - (discount_percent / 100.0))
        chaos_exalt_adj: float = 1 / exalt_div_val * chaos_div_val * (1.0 - (discount_percent / 100.0))
        print(f"{BOLD}PoE2{RESET} 현재 시세 기준, 현재 설정값이 1일 때 추천 통화 설정:")
        print(
            f"{discount_percent:.2f}% 할인 ({(1.0 - discount_percent / 100.0):.2f}배) {_currency_name(2, 'divine')} 1개"
        )
        print(f" = {int(div_annul_adj)} {_currency_name(2, 'annul')} ({div_annul_adj:.2f})")
        print(f" = {int(div_chaos_adj)} {_currency_name(2, 'chaos')} ({div_chaos_adj:.2f})")
        print(f" = {int(div_exalt_adj)} {_currency_name(2, 'exalted')} ({div_exalt_adj:.2f})")
        print(
            f"{discount_percent:.2f}% 할인 ({(1.0 - discount_percent / 100.0):.2f}배) {_currency_name(2, 'annul')} 1개"
        )
        print(f" = {int(annul_chaos_adj)} {_currency_name(2, 'chaos')} ({annul_chaos_adj:.2f})")
        print(f" = {int(annul_exalt_adj)} {_currency_name(2, 'exalted')} ({annul_exalt_adj:.2f})")
        print(f"{discount_percent:.2f}% 할인 ({(1.0 - discount_percent / 100.0):.2f}배) {_currency_name(2, 'chaos')} 1개")
        print(
            f" = {int(chaos_exalt_adj)} {_currency_name(2, 'exalted')} ({chaos_exalt_adj:.2f})",
            end="",
        )
        print()
        print(
            f"{discount_percent:.2f}% 할인 ({(1.0 - discount_percent / 100.0):.2f}배) {_currency_name(2, 'exalted')} 1개"
        )
        print(" = 그냥 상점에 파세요!")
    else:
        print("오류: 잘못된 데이터라 PoE2 통화 추천값을 계산할 수 없습니다.", file=sys.stderr)


def main() -> int:  # noqa: C901, PLR0915
    """Read settings from file, fetch and print currency values, then start keyboard listener.

    Returns:
        int: Process exit code (0 for success).

    """
    logging.basicConfig(
        level=logging.WARNING,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(),  # Output to console
        ],
    )

    settings_man: settings.SettingsManager = settings.settings_manager
    # Parsed binding tuples from keyboard.keyorkeycode_from_str
    keys: dict[str, tuple[str, object]] = {
        k: keyboard.keyorkeycode_from_str(key_str=v) for k, v in settings_man.settings.keys.model_dump().items()
    }

    def _binding_to_str(binding: tuple[str, object]) -> str:
        """Format a keyboard binding tuple as a readable string.

        Args:
            binding (tuple[str, object]): A tuple of binding type and value.

        Returns:
            str: Human-readable representation of the binding.

        """
        t, v = binding
        if t == "special":
            return str(v)
        if t == "char":
            return str(v)
        if t == "vk":
            return f"vk:{v}"
        if t == "scan":
            return f"scan:{v}"
        return str(binding)

    def _print_instructions() -> None:
        """Print user-facing keyboard instructions to the console.

        Returns:
            None

        """
        print("> PoEMarcut 실행 중 <")
        print(
            f'아이템에 마우스를 올린 상태에서 "{_binding_to_str(binding=keys["copyitem_key"])}" 또는 "ctrl+shift+c"를 눌러 클립보드로 복사한 뒤...'
        )
        print(
            f'아이템에 마우스를 올린 상태에서 "{_binding_to_str(binding=keys["rightclick_key"])}" 또는 "우클릭"으로 가격 창을 연 뒤...'
        )
        print(f'"{_binding_to_str(binding=keys["calcprice_key"])}"를 눌러 가격을 조정하세요.')
        if not settings_man.settings.currency.autoupdate:
            print(f'새 가격을 적용하려면 "{_binding_to_str(binding=keys["enter_key"])}" 또는 "enter"를 누르세요.')
        print(f'프로그램을 종료하려면 "{_binding_to_str(binding=keys["stop_key"])}"를 누르세요.')
        print("================================")

    _print_instructions()

    def _print_currency_suggestions(discount_percent: int) -> None:
        """Fetch and print currency suggestions for supported games.

        Args:
            discount_percent (float): Discount percent used to compute suggested prices.

        Returns:
            None

        """
        games: list[int] = [1, 2]
        for game in games:
            league = (
                next(iter(settings_man.settings.currency.poe1leagues))
                if game == 1
                else next(iter(settings_man.settings.currency.poe2leagues))
            )
            try:
                data = currency.store.get_data(
                    game=game, league=league, update=settings_man.settings.currency.autoupdate
                )
            except (LookupError, ValueError, OSError):
                print(f"오류: PoE{game} ({league}) 통화 데이터를 가져올 수 없습니다.", file=sys.stderr)
                data = {}
            print_last_updated(game=game, league=league, file_mtime=data.get("mtime", 0))

            # If data object is valid, print suggested currency values for case where current price is 1
            if game == 1 and "lines" in data and "core" in data and data["core"].get("primary"):
                print_poe1_currency_suggestions(discount_percent=discount_percent, data=data)
                print()
            elif game == 2 and "lines" in data and "core" in data and data["core"].get("primary"):  # noqa: PLR2004
                print_poe2_currency_suggestions(discount_percent=discount_percent, data=data)
                print()
            else:
                print(f"오류: PoE{game} 통화 추천값을 가져올 수 없습니다.", file=sys.stderr)
                print()

        update_available, github_version = update.is_github_update_available()
        if update_available and github_version:
            print(
                f"{BOLD}새로운 PoEMarcut 버전을 사용할 수 있습니다{RESET}: https://github.com/cdrg/poemarcut ({github_version}, 현재 버전 {__version__})"
            )

    _print_currency_suggestions(discount_percent=settings_man.settings.logic.discount_percent)

    keyboard.start_listener(blocking=True)

    # Ensure singleton-managed listener is stopped/cleaned up (no-op if already stopped)
    try:
        keyboard.stop_listener()
    except (RuntimeError, OSError):
        logging.getLogger(__name__).exception("Error while stopping keyboard listener on exit.")

    print("PoEMarcut을 종료합니다...")
    return 0


if __name__ == "__main__":
    sys.exit(main())
