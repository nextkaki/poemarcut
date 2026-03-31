from poemarcut import constants


def test_get_currency_display_name_returns_korean_name() -> None:
    assert constants.get_currency_display_name("chaos", game=1) == "카오스 오브"
    assert constants.get_currency_display_name("greater-chaos-orb", game=2) == "상급 카오스 오브"


def test_get_currency_display_name_returns_original_for_unknown_id() -> None:
    assert constants.get_currency_display_name("unknown-currency", game=1) == "unknown-currency"
