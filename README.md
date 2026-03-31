# PoE Marcut (Path of Exile 1 and 2 Market Cut)

오늘도 PoE에 접속했는데 상인 탭에 팔리지 않은 아이템이 잔뜩 쌓여 있나요?

그걸 하나하나 다시 시세 확인할 건가요? 절대 안 되죠, 완전한 시간 낭비입니다.

PoEMarcut은 아이템 가격을 빠르게 낮출 수 있도록 도와줍니다. 아이템에 마우스를 올리고 F2+F3를 누르면 설정한 % 만큼 가격이 내려갑니다. 다음 아이템으로 이동하고 반복하세요. 아이템이 팔리거나 가격이 바닥날 때까지 로그인할 때마다 반복하면 됩니다.

## 사용 방법
1. `poemarcut.exe`를 실행합니다. GUI 창이 열리면 원하는 대로 설정하세요.
2. 상인 탭에서 가격을 조정할 아이템 위에 마우스 커서를 올립니다.
3. `F2` (기본값) 또는 `우클릭`으로 아이템 가격 설정 다이얼로그를 엽니다.
4. `F3` (기본값)을 눌러 가격을 10% (기본값) 낮추고 다이얼로그를 닫습니다.
   (현재 수량이 1이 되거나 max_discount에 도달하면 F3는 다음으로 낮은 통화로 전환합니다.)

- (선택사항) `F2` 전에 `F1` (기본값)을 눌러 아이템의 통화 유형을 복사할 수 있습니다. (통화 변환을 캡처하려는 경우에만 필요)

`F6` (기본값)을 누르면 단축키를 비활성화할 수 있습니다. GUI에서도 단축키를 켜고 끌 수 있습니다.

새 가격은 항상 내림(소수점 버림) 처리되어, 기존 가격이 `2`인 경우에도 반드시 낮아집니다 (설정에 따라 `1`이 됩니다).

기존 가격이 `1`인 경우, 설정된 다음 낮은 통화로 자동 전환됩니다.

선택적 설정인 `max_actual_discount`를 사용하면 지나치게 낮은 가격의 추가 인하를 방지할 수 있습니다. 예를 들어 `40%`로 설정하면 `2`가 `1`로 낮아지는 것을 막습니다 (실제 할인율 50% > 최대 허용 40%).

현재 poe.ninja 경제 데이터를 기반으로 통화 환율 목록도 함께 표시됩니다.

## GGG 이용약관 준수
이 툴은 [GGG TOS 정책](https://www.pathofexile.com/developer/docs#policy)을 완전히 준수하며 합법적입니다. 단순한 키보드 매크로로, 키 입력 한 번당 '서버 액션' 하나만 수행하며 정책을 따릅니다.
가격을 변경하려는 각 아이템마다 직접 조작이 필요합니다.

## 설치 / 실행

[Github Releases](https://github.com/cdrg/poemarcut/releases/latest)에서 다운로드 후 `poemarcut.exe`를 실행하세요.

또는 Python으로 [커맨드라인에서 소스를 직접 실행](https://github.com/cdrg/poemarcut#running-from-the-command-line)할 수도 있습니다.

## 설정
단축키, 가격 조정 비율, 리그 등의 설정은 GUI에서 변경할 수 있으며 `settings.yaml`에 저장됩니다.

`settings.yaml`은 처음 실행 시 기본값으로 자동 생성됩니다.

이 파일은 일반 텍스트 파일로, 어떤 텍스트 편집기로도 수정할 수 있으며 각 설정에 대한 설명이 포함되어 있습니다.

## 크레딧
- 원본 프로젝트: [cdrg/poemarcut](https://github.com/cdrg/poemarcut) by [@cdrg](https://github.com/cdrg) (GPL-3.0)
- 아이디어 출처: [@nickycakes](https://github.com/nickycakes/poe2price)의 개념 증명(proof-of-concept)

## 고급 설정

### 커맨드라인에서 실행하기
`poetry`로 실행하는 것을 권장합니다. 예: `poetry run python poemarcut_gui.py`

- Github의 초록색 Code 버튼에서 zip 다운로드 또는 clone으로 저장소를 가져옵니다.

- 최초 사용 전, 저장소 디렉토리에서 `poetry install`을 실행하여 poetry 가상환경을 초기화합니다.

- 필요한 경우 [poetry를 설치](https://python-poetry.org/docs/)하거나 (pipx 사용 권장) 원하는 Python 가상환경을 직접 사용해도 됩니다.

#### Windows 전체 설치 안내
1. Microsoft Store 앱에서 Python 3.12 또는 3.13을 설치합니다 (이미 설치되어 있다면 생략).
2. 터미널을 엽니다.
3. `python -m pip install --user pipx` — pipx 설치
4. `.\pipx.exe ensurepath`
5. `pipx install poetry` — poetry 설치
6. Github에서 소스를 다운로드 또는 clone합니다.
7. 소스 폴더에서 `poetry install` — poetry 환경 초기화
8. `poetry run python poemarcut_gui.py` (또는 `poemarcut_cli.py`) 실행

### 빌드
`poetry run build`를 실행하세요.
