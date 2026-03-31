"""Item-related functionality for PoEMarcut.

Defines simple, serializable dataclasses for items, mods, and notes
used by the rest of the application.

한국어 클라이언트 지원 패치 적용:
- 아이템 종류 / 희귀도 / 레벨 / 메모 등 한국어 키워드 파싱
- 메모의 통화명이 한글인 경우 trade id로 변환
"""

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


def parse_int_price(raw: str) -> int:
    """Parse a raw string into an integer price."""
    s = (raw or "").strip()
    normalized = re.sub(r"[^\d]", "", s)
    if not normalized:
        msg = f"invalid price: '{raw}'"
        raise ValueError(msg)
    try:
        return int(normalized)
    except (ValueError, TypeError) as e:
        msg = f"invalid price: '{raw}'"
        raise ValueError(msg) from e


# 한국어 통화명 → trade id 변환 테이블
KR_CURRENCY_NAME_TO_ID: dict[str, str] = {
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
    "장인의 오브": "artificers",
    "파열의 오브": "fracturing-orb",
}

# 한국어 희귀도 → 영어 변환
KR_RARITY_MAP: dict[str, str] = {
    "일반": "Normal",
    "마법": "Magic",
    "희귀": "Rare",
    "고유": "Unique",
}


@dataclass
class Item:
    """Represents a Path of Exile 1 or 2 item."""

    @dataclass
    class Mod:
        """Represents a single item mod."""

        name: str
        text: str
        value: float | None = None

    @dataclass
    class Note:
        """Represents a note attached to an item (trade note)."""

        text: str
        price: int | None = None
        currency: str | None = None

    class Rarity(Enum):
        """Enumeration of supported item rarities."""

        UNIQUE = "Unique"
        RARE = "Rare"
        MAGIC = "Magic"
        COMMON = "Common"

    name: str
    basetype: str
    class_: str = ""
    rarity: Rarity | None = None
    requirements: dict[str, int] = field(default_factory=dict)
    item_level: int | None = None
    droplevel: int | None = None
    enchantments: list[str] = field(default_factory=list)
    implicit_mods: list[Mod] = field(default_factory=list)
    explicit_mods: list[Mod] = field(default_factory=list)
    note: Note | None = None

    def add_implicit(self, mod: Mod) -> None:
        self.implicit_mods.append(mod)

    def add_explicit(self, mod: Mod) -> None:
        self.explicit_mods.append(mod)

    def to_dict(self) -> dict[str, Any]:
        return {
            "rarity": self.rarity.value if self.rarity is not None else None,
            "name": self.name,
            "basetype": self.basetype,
            "class": self.class_,
            "requirements": dict(self.requirements),
            "item_level": self.item_level,
            "droplevel": self.droplevel,
            "enchantments": list(self.enchantments),
            "implicit_mods": [m.__dict__ for m in self.implicit_mods],
            "explicit_mods": [m.__dict__ for m in self.explicit_mods],
            "note": self.note.__dict__ if self.note is not None else None,
        }

    @classmethod
    def from_text(cls, text: str) -> "Item":  # noqa: C901, PLR0912, PLR0915
        """Create an Item by parsing raw copied item text.

        한국어/영어 클라이언트 모두 지원합니다.
        """
        lines_raw = text.splitlines()
        lines = [raw.strip() for raw in lines_raw if raw.strip()]

        class_ = ""
        rarity = None
        name = ""
        basetype = ""
        item_level = None
        droplevel = None
        requirements: dict[str, int] = {}
        note_obj = None

        def _map_rarity(rarity_str: str) -> "Item.Rarity | None":
            if not rarity_str:
                return None
            # 한국어 희귀도를 영어로 변환
            rarity_str = KR_RARITY_MAP.get(rarity_str.strip(), rarity_str.strip())
            lr = rarity_str.lower()
            if lr == "normal":
                return cls.Rarity.COMMON
            for r in cls.Rarity:
                if r.value.lower() == lr:
                    return r
            return None

        def _startswith_any(low_line: str, *prefixes: str) -> bool:
            """Check if the line starts with any of the given prefixes."""
            return any(low_line.startswith(p) for p in prefixes)

        def _split_value(line: str, *prefixes: str) -> str:
            """Extract the value after the first matching prefix."""
            for p in prefixes:
                if line.lower().startswith(p):
                    return line[len(p):].strip()
            return line.split(":", 1)[-1].strip()

        for idx, line in enumerate(lines):
            low = line.lower()

            # ── 아이템 종류 / Item Class ──
            if _startswith_any(low, "item class:", "아이템 종류:"):
                class_ = _split_value(line, "item class:", "아이템 종류:")

            # ── 희귀도 / Rarity ──
            elif _startswith_any(low, "rarity:", "아이템 희귀도:"):
                rarity_str = _split_value(line, "rarity:", "아이템 희귀도:")
                rarity = _map_rarity(rarity_str)
                # 이름/베이스타입 수집
                j = idx + 1
                name_lines: list[str] = []
                while j < len(lines):
                    nxt = lines[j]
                    if nxt.startswith("--------") or ":" in nxt:
                        break
                    if nxt.startswith("{"):
                        break
                    name_lines.append(nxt)
                    j += 1
                if name_lines:
                    name = name_lines[0]
                    if len(name_lines) > 1:
                        basetype = name_lines[1]

            # ── 아이템 레벨 / Item Level ──
            elif _startswith_any(low, "item level:", "아이템 레벨:"):
                m = re.search(r"(\d+)", line)
                if m:
                    item_level = int(m.group(1))

            # ── 지도 등급 / Map Tier ──
            elif _startswith_any(low, "map tier", "지도 등급"):
                m = re.search(r"(\d+)", line)
                if m:
                    droplevel = int(m.group(1))

            # ── 요구사항 / Requirements ──
            elif _startswith_any(low, "requirements:", "요구사항:"):
                j = idx + 1
                while j < len(lines) and not lines[j].startswith("--------"):
                    # 영어: "Level: 52"  한국어: "레벨: 52"
                    lvl_m = re.search(r"(?:level|레벨)\s*:?\s*(\d+)", lines[j], flags=re.IGNORECASE)
                    if lvl_m:
                        requirements["level"] = int(lvl_m.group(1))
                    j += 1

            # ── 메모 / Note ── (핵심 수정)
            elif _startswith_any(low, "note:", "메모:"):
                note_text = _split_value(line, "note:", "메모:")

                # 한국어/영어 공통 패턴
                # 예) "~b/o 203 chaos"  →  price=203, currency="chaos"
                # 예) "~b/o 1 신성한 오브"  →  price=1, currency="divine"
                pattern = r"~\s*(?:b/o|price)\b[:\s]*([\d\.,\s]+)\s*(.+)"
                m = re.search(pattern, note_text, flags=re.IGNORECASE)
                if m:
                    price_str, cur_type_raw = m.groups()
                    try:
                        price_val = parse_int_price(price_str)
                    except ValueError:
                        price_val = None
                        cur_type_raw = None

                    if price_val is not None and cur_type_raw is not None:
                        cur_type_raw = cur_type_raw.strip()
                        # 한국어 통화명이면 trade id로 변환, 영어면 소문자 정규화
                        if cur_type_raw in KR_CURRENCY_NAME_TO_ID:
                            cur_type: str | None = KR_CURRENCY_NAME_TO_ID[cur_type_raw]
                        else:
                            cur_type = cur_type_raw.lower()
                    else:
                        cur_type = None
                else:
                    price_val, cur_type = None, None

                note_obj = cls.Note(text=note_text, price=price_val, currency=cur_type)

        # 이름 폴백: 키워드가 없는 라인 중 첫 번째
        if not name:
            for line in lines:
                if ":" not in line and not line.startswith("--------") and not line.startswith("{"):
                    name = line
                    break

        return cls(
            name=name,
            basetype=basetype,
            class_=class_,
            rarity=rarity,
            requirements=requirements,
            item_level=item_level,
            droplevel=droplevel,
            note=note_obj,
        )
