# -*- coding: utf-8 -*-
"""
애니메이션에 **소리가 나는가.** 그리고 돌아도 안 끊기는가.

★ 손님이 시킨 것 (2026-09-07)

  "애니메이션에 있는 소리는 자연스럽게 무한반복될 수 있도록
   끊기지 않는것처럼해서 전부 다 켜줘 기본값이, 처음이나 아니면
   상단 플로우에 소리끄기 버튼 하나 만들고"
  "어떤 페이지던 애니메이션 들어간건 다 소리가 나와야해"

★ 재 보니 켤 것이 없었습니다

  들어온 클립 열셋 중 소리가 붙은 것은 **하나**(도령의 첫인사)
  뿐이었습니다. 스위치는 멀쩡히 있었는데 켜도 켜지는 것이 없었고,
  게다가 배경음을 거는 자리가 `Shell` 한 곳에 `playBgm("hall")` 로
  **못 박혀** 있어서 스물여섯 장면이 어디를 지나든 대청 소리였습니다.

★ 여기서 지키는 것 다섯

    · 장면마다 제 소리가 적혀 있는가      (빠지면 그 화면만 조용합니다)
    · 적힌 소리가 파일로 있는가
    · 그 파일이 **돌아도 안 끊기는가**
    · 기본값이 켜짐인가                    (스위치 하나에 기본값 하나)
    · 끌 데가 **모든 화면에** 있는가       (대문 포함)

★ ffmpeg 을 안 부릅니다

  이 저장소는 skip 0 입니다. 검사가 ffmpeg 을 부르면 없는 기계에서
  건너뛰게 됩니다. 그래서 도구가 재서 `seed/ambience.json` 에 적어
  두고, 검사는 **그 기록이 지금 파일 그대로인지**만 봅니다
  (`tests/test_loop_seam.py` 와 같은 꼴).
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "apps" / "web"
BGM = WEB / "public" / "audio" / "bgm"
RECORD = ROOT / "seed" / "ambience.json"

HOWTO = "  python tools/make_ambience.py        (다시 짓고 기록까지)"


def _src(rel: str) -> str:
    return (WEB / rel).read_text(encoding="utf-8")


def _scenes() -> list[tuple[str, str | None]]:
    """manifest 에서 (장면 id, 소리 결) 을 뽑는다."""
    src = _src("components/scene/manifest.ts")
    body = src[src.index("export const SCENES"):]
    out = []
    for line in body.splitlines():
        m = re.search(r'\{ id: "([a-z]+)",', line)
        if not m:
            continue
        b = re.search(r'bed: "([a-z]+)"', line)
        out.append((m.group(1), b.group(1) if b else None))
    return out


def _record() -> dict:
    assert RECORD.exists(), (
        "seed/ambience.json 이 없소. 소리가 도는지 아무도 안 봤다는 뜻이오.\n"
        + HOWTO)
    return json.loads(RECORD.read_text("utf-8"))


# ── 장면마다 제 소리가 있는가 ──────────────────────────────

def test_장면마다_소리가_적혀_있다():
    """
    ★ 하나라도 비면 **그 화면만 조용합니다.** 아무것도 안 죽고
      손님만 압니다 — 그래서 검사로 셉니다.
    """
    got = _scenes()
    assert got, "manifest 에서 장면을 못 읽었소"
    empty = sorted(sid for sid, bed in got if not bed)
    assert not empty, "소리를 안 적은 장면: %s" % empty


def test_적힌_소리는_파일로_있다():
    want = {bed for _, bed in _scenes() if bed}
    missing = sorted(b for b in want if not (BGM / ("%s.mp3" % b)).exists())
    assert not missing, (
        "적혀 있는데 파일이 없는 소리: %s\n%s" % (missing, HOWTO))


def test_안_쓰는_소리는_두지_않는다():
    """
    ★ 안 쓰는 파일은 아무도 안 지웁니다. 다음 사람이 「이건 뭐지」
      하다가 그냥 둡니다.
    """
    want = {bed for _, bed in _scenes() if bed}
    have = {p.stem for p in BGM.glob("*.mp3")}
    assert not (have - want), "아무 장면도 안 부르는 소리: %s" % sorted(have - want)


# ── 돌아도 안 끊기는가 ────────────────────────────────────

def test_기록이_지금_파일_그대로다():
    """
    ★ 소리를 다시 굽고 기록을 안 갱신하면, 재 놓은 값은 **딴 파일의
      값**입니다. 그걸 믿고 배포하면 끊기는 소리가 그대로 나갑니다.
    """
    rec = _record()["beds"]
    for name, m in sorted(rec.items()):
        p = BGM / ("%s.mp3" % name)
        assert p.exists(), "기록에는 있는데 파일이 없소: %s" % name
        sha = hashlib.sha256(p.read_bytes()).hexdigest()
        assert sha == m["sha256"], (
            "%s 를 다시 구웠는데 기록이 옛것이오.\n%s" % (name, HOWTO))
    have = {p.stem for p in BGM.glob("*.mp3")}
    assert have == set(rec), "기록에 없는 소리: %s" % sorted(have - set(rec))


@pytest.mark.parametrize("name", sorted(_record()["beds"]))
def test_돌아도_안_끊긴다(name):
    """
    ★ 어떻게 재는가 — **파형 안 아무 데나 자른 것**과 견줍니다.

      「이음새가 작다」는 그 자체로는 뜻이 없습니다. 낮은 드론은
      이웃 샘플 차가 원래 작아서 조금만 어긋나도 커 보이고, 소음은
      그 반대입니다. 그래서 한 바퀴 도는 자리의 단차를, 안쪽에서
      아무 데나 잘랐을 때 생기는 단차(99퍼센타일)와 견줍니다.

      도는 자리가 안쪽 아무 데보다 얌전하면 그 자리는 특별한 데가
      아닙니다. 귀에는 그게 「안 끊긴다」입니다.
    """
    m = _record()["beds"][name]
    assert m["wrap"] <= m["inside"], (
        "%s — 도는 자리(%.4f)가 안쪽 아무 데(%.4f)보다 거칠어 딸깍하오.\n%s"
        % (name, m["wrap"], m["inside"], HOWTO))


@pytest.mark.parametrize("name", sorted(_record()["beds"]))
def test_영상_길이와_안_맞는다(name):
    """
    ★ 소리가 영상과 같은 길이면 손님이 **되도는 것을 알아챕니다.**

      장면 클립은 2~10초입니다. 소리가 4.5초면 그림과 소리가 같이
      돌아서 「아, 이거 4.5초짜리구나」가 됩니다. 훨씬 길게 두고
      배수도 피하면 둘이 어긋나며 계속 새 조합이 나옵니다.
    """
    secs = _record()["beds"][name]["seconds"]
    assert secs >= 15.0, "%s 가 %.1f초뿐이오 — 되도는 게 들리오" % (name, secs)


# ── 기본값과 끄는 자리 ────────────────────────────────────

def test_기본이_켜짐이다():
    """
    ★ 손님이 시킨 것 — "전부 다 켜줘 기본값이".
    """
    src = _src("lib/sound.ts")
    assert 'localStorage.getItem(KEY) === "off" ? "off" : "on"' in src, (
        "기본값이 켜짐이 아니오 (lib/sound.soundState)")


def test_스위치_하나에_기본값도_하나다():
    """
    ★ 전에는 배경음이 기본 꺼짐, 영상 소리가 기본 켜짐이었습니다.
      그러면 ♪ 가 「꺼짐」을 그리는데 영상은 소리를 냅니다 — 손님은
      무엇이 켜져 있는지 알 수가 없습니다.

      `videoSoundOn` 은 제 값을 갖지 말고 `soundState` 를 봐야 합니다.
    """
    src = _src("lib/sound.ts")
    body = src[src.index("export function videoSoundOn"):]
    body = body[:body.index("\n}")]
    assert "soundState()" in body, "영상 소리가 제 기본값을 따로 갖고 있소"
    assert "localStorage" not in body, (
        "영상 소리가 저장소를 따로 보오 — 기본값이 둘로 갈리오")


def test_배경음을_한_이름으로_못_박지_않는다():
    """
    ★ `Shell` 이 `playBgm("hall")` 을 한 번 걸어 두고 있었습니다.
      그래서 스물여섯 장면이 어디를 지나든 대청 소리였습니다.
      소리는 **보이는 장면**이 가져갑니다 (`lib/ambience.ts`).
    """
    src = _src("components/Shell.tsx")
    src = re.sub(r"/\*.*?\*/", " ", src, flags=re.S)
    assert not re.search(r'playBgm\("', src), (
        "Shell 이 배경음을 한 이름으로 못 박고 있소")


def test_소리는_보이는_장면을_따라간다():
    """
    ★ 한 페이지에 `<Scene>` 이 여덟까지 얹힙니다. 얹힐 때 걸면 여덟이
      동시에 걸어 **마지막 것**이 이깁니다 — 손님이 보고 있는 장면이
      아닙니다. 보이는지를 봐야 합니다.
    """
    amb = _src("lib/ambience.ts")
    assert "IntersectionObserver" in amb, "보이는지를 안 보오"
    scene = _src("components/scene/Scene.tsx")
    assert "useAmbience(" in scene, "장면이 제 소리를 안 거오"


def test_끌_데가_모든_화면에_있다():
    """
    ★ 상단바는 대문(a1)에서만 숨깁니다. 그런데 소리가 기본 켜짐이 되면
      **소리가 처음 나는 화면에 끌 단추가 없어집니다** — 브라우저가 첫
      손짓을 기다리니 그 손짓은 십중팔구 대문의 「다음으로」이고,
      소리는 거기서 납니다. 회사에서 연 사람이 그 자리에서 꺼야 합니다.
    """
    src = _src("components/Shell.tsx")
    bare = re.search(r"\{bare && \(([\s\S]{0,400}?)\)\}", src)
    assert bare and "SoundToggle" in bare.group(1), (
        "대문(bare)에 소리 끄는 자리가 없소")
    assert src.count("<SoundToggle />") >= 2, (
        "상단바와 대문 둘 다에 있어야 하오")


def test_버튼이_끄는_말을_한다():
    """
    ★ 손님이 시킨 것 — "소리끄기 버튼 하나". 켜져 있는 사람에게
      「소리 켜기」라 적혀 있으면 그건 딴 버튼입니다.
    """
    src = _src("components/SoundToggle.tsx")
    assert 'on ? "소리 끄기" : "소리 켜기"' in src, "켬/끔 말이 뒤바뀌었소"
    # 첫 그림도 켜짐이라야 서버가 그린 것과 같습니다 (안 그러면 깜빡).
    assert "useState(true)" in src, "첫 그림이 꺼짐이라 한 번 깜빡이오"
