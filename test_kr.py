import sys
sys.path.insert(0, "src")

from poemarcut.item import Item

sample = """아이템 종류: 심연 주얼

아이템 희귀도: 희귀

Grim Breeze

Searching Eye Jewel

--------

아이템 레벨: 83

--------

메모: ~b/o 203 chaos"""

item = Item.from_text(sample)
print(f"이름: {item.name}")
print(f"희귀도: {item.rarity}")
print(f"아이템 레벨: {item.item_level}")
print(f"가격: {item.note.price if item.note else 'None'}")
print(f"통화: {item.note.currency if item.note else 'None'}")

assert item.note is not None,         "❌ note가 None — 메모: 파싱 실패"
assert item.note.price == 203,        f"❌ price 오류: {item.note.price}"
assert item.note.currency == "chaos", f"❌ currency 오류: {item.note.currency}"
assert item.rarity is not None,       "❌ rarity가 None — 아이템 희귀도: 파싱 실패"
assert item.item_level == 83,         f"❌ item_level 오류: {item.item_level}"

print("\n✅ 모든 테스트 통과!")