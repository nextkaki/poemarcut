"""Constants for PoEMarcut."""

from types import MappingProxyType

S_IN_HOUR = 3600

BOLD = "\033[1m"  # ANSI escape bold
RESET = "\033[0m"  # ANSI escape reset

# mapping of PoE1 merchant tab currency trade id to full name
# ordered by the order in the merchant tab dropdown
POE1_MERCHANT_CURRENCIES = MappingProxyType(
    {
        "chaos": "Chaos Orb",
        "divine": "Divine Orb",
        "alch": "Orb of Alchemy",
        "exalted": "Exalted Orb",
        "alt": "Orb of Alteration",
        "mirror": "Mirror of Kalandra",
        "chrome": "Chromatic Orb",
        "blessed": "Blessed Orb",
        "fusing": "Orb of Fusing",
        "jewellers": "Jeweller's Orb",
        "regal": "Regal Orb",
        "vaal": "Vaal Orb",
        "chance": "Orb of Chance",
        "annul": "Orb of Annulment",
        "aug": "Orb of Augmentation",
        "regret": "Orb of Regret",
        "scour": "Orb of Scouring",
        "transmute": "Orb of Transmutation",
        "wisdom": "Scroll of Wisdom",
        "portal": "Portal Scroll",
        "scrap": "Armourer's Scrap",
        "whetstone": "Blacksmith's Whetstone",
        "gcp": "Gemcutter's Prism",
        "bauble": "Glassblower's Bauble",
        # "offer": "Offering to the Goddess",  # noqa: ERA001 -- not in the poe.ninja currency response, would need to implement a separate call
    }
)

POE1_MERCHANT_CURRENCY_DISPLAY_NAMES = MappingProxyType(
    {
        "chaos": "카오스 오브",
        "divine": "신성한 오브",
        "alch": "연금술의 오브",
        "exalted": "고귀한 오브",
        "alt": "변화의 오브",
        "mirror": "칼란드라의 거울",
        "chrome": "색채의 오브",
        "blessed": "축복의 오브",
        "fusing": "융합의 오브",
        "jewellers": "보석공의 오브",
        "regal": "고귀화의 오브",
        "vaal": "바알 오브",
        "chance": "기회의 오브",
        "annul": "무효의 오브",
        "aug": "증폭의 오브",
        "regret": "후회의 오브",
        "scour": "정화의 오브",
        "transmute": "변환의 오브",
        "wisdom": "지혜의 두루마리",
        "portal": "차원문 두루마리",
        "scrap": "갑옷공의 스크랩",
        "whetstone": "대장장이의 숫돌",
        "gcp": "보석 세공인의 프리즘",
        "bauble": "유리공의 구슬",
    }
)

# mapping of PoE1 merchant tab currency trade id to unique minimum full-name prefix for dropdown selection
# ordered by the order in the merchant tab dropdown
POE1_MERCHANT_CURRENCY_PREFIXES = MappingProxyType(
    {
        "chaos": "c",
        "divine": "d",
        "alch": "o",
        "exalted": "e",
        "alt": "orbofalt",
        "mirror": "m",
        "chrome": "chr",
        "blessed": "b",
        "fusing": "orboff",
        "jewellers": "j",
        "regal": "r",
        "vaal": "v",
        "chance": "orbofc",
        "annul": "orbofan",
        "aug": "orbofau",
        "regret": "orbofr",
        "scour": "orbofs",
        "transmute": "orboft",
        "wisdom": "s",
        "portal": "p",
        "scrap": "a",
        "whetstone": "bla",
        "gcp": "g",
        "bauble": "gl",
    }
)

# mapping of PoE2 merchant tab currency trade id to full name
# ordered by the order in the merchant tab dropdown
POE2_MERCHANT_CURRENCIES = MappingProxyType(
    {
        "exalted": "Exalted Orb",
        "greater-exalted-orb": "Greater Exalted Orb",
        "perfect-exalted-orb": "Perfect Exalted Orb",
        "divine": "Divine Orb",
        "chaos": "Chaos Orb",
        "greater-chaos-orb": "Greater Chaos Orb",
        "perfect-chaos-orb": "Perfect Chaos Orb",
        "alch": "Orb of Alchemy",
        "annul": "Orb of Annulment",
        "regal": "Regal Orb",
        "greater-regal-orb": "Greater Regal Orb",
        "perfect-regal-orb": "Perfect Regal Orb",
        "transmute": "Orb of Transmutation",
        "greater-orb-of-transmutation": "Greater Orb of Transmutation",
        "perfect-orb-of-transmutation": "Perfect Orb of Transmutation",
        "aug": "Orb of Augmentation",
        "greater-orb-of-augmentation": "Greater Orb of Augmentation",
        "perfect-orb-of-augmentation": "Perfect Orb of Augmentation",
        "chance": "Orb of Chance",
        "vaal": "Vaal Orb",
        "artificers": "Artificer's Orb",
        "fracturing-orb": "Fracturing Orb",
        "mirror": "Mirror of Kalandra",
        "wisdom": "Scroll of Wisdom",
    }
)

POE2_MERCHANT_CURRENCY_DISPLAY_NAMES = MappingProxyType(
    {
        "exalted": "고귀한 오브",
        "greater-exalted-orb": "상급 고귀한 오브",
        "perfect-exalted-orb": "완벽한 고귀한 오브",
        "divine": "신성한 오브",
        "chaos": "카오스 오브",
        "greater-chaos-orb": "상급 카오스 오브",
        "perfect-chaos-orb": "완벽한 카오스 오브",
        "alch": "연금술의 오브",
        "annul": "무효의 오브",
        "regal": "고귀화의 오브",
        "greater-regal-orb": "상급 고귀화의 오브",
        "perfect-regal-orb": "완벽한 고귀화의 오브",
        "transmute": "변환의 오브",
        "greater-orb-of-transmutation": "상급 변환의 오브",
        "perfect-orb-of-transmutation": "완벽한 변환의 오브",
        "aug": "증폭의 오브",
        "greater-orb-of-augmentation": "상급 증폭의 오브",
        "perfect-orb-of-augmentation": "완벽한 증폭의 오브",
        "chance": "기회의 오브",
        "vaal": "바알 오브",
        "artificers": "장인의 오브",
        "fracturing-orb": "파열의 오브",
        "mirror": "칼란드라의 거울",
        "wisdom": "지혜의 두루마리",
    }
)

# mapping of PoE2 merchant tab currency trade id to unique minimum full-name prefix for dropdown selection
# ordered by the order in the merchant tab dropdown
POE2_MERCHANT_CURRENCY_PREFIXES = MappingProxyType(
    {
        "exalted": "e",
        "greater-exalted-orb": "g",
        "perfect-exalted-orb": "p",
        "divine": "d",
        "chaos": "c",
        "greater-chaos-orb": "greaterc",
        "perfect-chaos-orb": "perfectc",
        "alch": "o",
        "annul": "orbofan",
        "regal": "r",
        "greater-regal-orb": "greaterr",
        "perfect-regal-orb": "perfectr",
        "transmute": "orboft",
        "greater-orb-of-transmutation": "greatero",
        "perfect-orb-of-transmutation": "perfecto",
        "aug": "orbofau",
        "greater-orb-of-augmentation": "greaterorbofa",
        "perfect-orb-of-augmentation": "perfectorbofa",
        "chance": "orbofc",
        "vaal": "v",
        "artificers": "a",
        "fracturing-orb": "f",
        "mirror": "m",
        "wisdom": "s",
    }
)

# ──────────────────────────────────────────────
# 한국어 클라이언트 통화명 → trade id 역매핑
# 게임 내 표기명을 기준으로 작성했습니다.
# ──────────────────────────────────────────────
KR_CURRENCY_NAME_TO_ID = {
    # PoE1
    "혼돈의 오브": "chaos",
    "카오스 오브": "chaos",
    "신성한 오브": "divine",
    "연금술의 오브": "alch",
    "고귀한 오브": "exalted",
    "변화의 오브": "alt",
    "칼란드라의 거울": "mirror",
    "색채의 오브": "chrome",
    "축복의 오브": "blessed",
    "융합의 오브": "fusing",
    "보석공의 오브": "jewellers",
    "고귀화의 오브": "regal",
    "바알 오브": "vaal",
    "기회의 오브": "chance",
    "무효의 오브": "annul",
    "증폭의 오브": "aug",
    "후회의 오브": "regret",
    "정화의 오브": "scour",
    "변환의 오브": "transmute",
    "지혜의 두루마리": "wisdom",
    "차원문 두루마리": "portal",
    "갑옷공의 스크랩": "scrap",
    "대장장이의 숫돌": "whetstone",
    "보석 세공인의 프리즘": "gcp",
    "유리공의 구슬": "bauble",
    # PoE2
    "고귀한 오브": "exalted",          # PoE2도 동일
    "신성한 오브": "divine",            # PoE2도 동일
    "혼돈의 오브": "chaos",             # PoE2도 동일
    "카오스 오브": "chaos",             # PoE2도 동일
    "연금술의 오브": "alch",
    "무효의 오브": "annul",
    "고귀화의 오브": "regal",
    "변환의 오브": "transmute",
    "증폭의 오브": "aug",
    "기회의 오브": "chance",
    "바알 오브": "vaal",
    "장인의 오브": "artificers",
    "파열의 오브": "fracturing-orb",
    "칼란드라의 거울": "mirror",
    "지혜의 두루마리": "wisdom",
}

GAME_MERCHANT_CURRENCIES = MappingProxyType({1: POE1_MERCHANT_CURRENCIES, 2: POE2_MERCHANT_CURRENCIES})
GAME_MERCHANT_CURRENCY_DISPLAY_NAMES = MappingProxyType(
    {1: POE1_MERCHANT_CURRENCY_DISPLAY_NAMES, 2: POE2_MERCHANT_CURRENCY_DISPLAY_NAMES}
)


def get_currency_display_name(currency_id: str, *, game: int | None = None) -> str:
    """Return a Korean display name for a currency id when known."""

    key = str(currency_id).strip().lower()
    if game in GAME_MERCHANT_CURRENCY_DISPLAY_NAMES:
        return GAME_MERCHANT_CURRENCY_DISPLAY_NAMES[game].get(key, str(currency_id))

    for mapping in GAME_MERCHANT_CURRENCY_DISPLAY_NAMES.values():
        if key in mapping:
            return mapping[key]

    return str(currency_id)
