"""
에셋 — 만들기 전에 붙일 자리가 있는가.

★ 에셋은 만들고 나면 되돌리기 가장 비싼 것인데, 검사가 하나도
  없었습니다. 화면 그래프(screen_graph)는 화면과 버튼을 보지만
  **에셋은 안 봅니다.**

  전수조사에서 셋이 나왔습니다 (tools/asset_audit.py):
    · `door` — 발주 목록에 있는데 아무 화면도 안 부름. 만들어도 안 나옴
    · `scroll` — 16:9 인데 9:16 강제 자리에 들어가 가로 68%가 잘림
    · 캐릭터 초상 — /char/{id}/bust.png 를 요구하는데 그리는 코드가 없음
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "apps" / "web"
MANIFEST = WEB / "components" / "scene" / "manifest.ts"

# .sceneart.hero / .fill 은 aspect-ratio 9/16 + object-fit:cover 입니다.
# 다른 비율이 들어가면 **잘려 나갑니다.**
FORCED_RATIO = "9:16"


def _manifest() -> dict:
    src = "\n".join(l for l in MANIFEST.read_text("utf-8").splitlines()
                    if not l.lstrip().startswith("//"))
    return {m.group(1): m.group(2) for m in
            re.finditer(r'\{\s*id:\s*"([^"]+)".*?ratio:\s*"([^"]+)"', src)}


def _tsx():
    return list((WEB / "app").rglob("*.tsx")) + \
           list((WEB / "components").rglob("*.tsx"))


def _usage():
    out = {}
    for p in _tsx():
        if p.name == "Scene.tsx":
            continue
        for m in re.finditer(r'<Scene\s+id="([a-z]+)"([^/>]*)', p.read_text("utf-8")):
            forced = "fill" in m.group(2) or "hero" in m.group(2)
            out.setdefault(m.group(1), []).append((str(p.name), forced))
    return out


def test_every_declared_scene_is_actually_used():
    """
    ★ 발주 목록에 있는데 아무 화면도 안 부르면 **만들어도 안 나옵니다.**
      `door` 가 그랬습니다. 에셋 하나가 그냥 돈입니다.
    """
    man, used = _manifest(), _usage()
    ghosts = sorted(set(man) - set(used))
    assert not ghosts, ("아무 화면도 안 부르는 장면: %s" % ghosts)


def test_every_used_scene_is_declared():
    """화면이 부르는데 목록에 없으면 발주에서 빠집니다."""
    man, used = _manifest(), _usage()
    missing = sorted(set(used) - set(man))
    assert not missing, ("선언에 없는 장면: %s" % missing)


def test_no_scene_is_cropped_in_a_forced_slot():
    """
    ★ `.sceneart.hero` 는 aspect-ratio 9/16 에 object-fit:cover 입니다.
      16:9 클립을 거기 넣으면 **가로의 약 68%가 사라집니다.**
      `scroll` 이 두 화면에서 그랬습니다. 아직 안 만든 에셋이라
      지금이 고칠 때였습니다.
    """
    man, used = _manifest(), _usage()
    bad = [(sid, man[sid], who) for sid, uses in used.items()
           for who, forced in uses
           if forced and man.get(sid) != FORCED_RATIO]
    assert not bad, ("강제 9:16 자리에 다른 비율: %s" % bad)


def test_the_character_portraits_have_somewhere_to_land():
    """
    ★ 발주서 §7 은 /char/{id}/bust.png 768×1024 를 요구하고 제작 순서까지
      정해 놓았는데, **그걸 그리는 코드가 하나도 없었습니다.**
      스무 장을 만들어도 갈 데가 없는 상태였습니다.
    """
    drawers = [p for p in _tsx()
               if re.search(r'/char/|bust\.png', p.read_text("utf-8"))]
    assert drawers, "초상을 그리는 컴포넌트가 없습니다"

    users = [p for p in (WEB / "app").rglob("*.tsx")
             if "<CharArt" in p.read_text("utf-8")]
    assert users, "컴포넌트만 있고 어느 화면에도 안 붙었습니다"


def test_the_placeholder_does_not_pretend_to_be_a_face():
    """
    반쯤 그린 얼굴은 없는 것보다 나쁩니다. 자리표시는 색과 글자로
    자리만 잡습니다.
    """
    src = (WEB / "components" / "CharArt.tsx").read_text("utf-8")
    assert "얼굴을 흉내내지 않습니다" in src


@pytest.mark.parametrize("path", sorted(
    p for p in (WEB / "public" / "scene").rglob("clip.*")) or [None])
def test_clips_stay_under_the_size_limit(path):
    """docs/10 §7 — 클립당 600KB 이하. 넘으면 첫 화면이 늦게 뜹니다."""
    if path is None:
        pytest.skip("들어온 클립이 없습니다")
    kb = path.stat().st_size / 1024
    assert kb <= 600, ("%s %.0fKB" % (path.name, kb))


def test_every_clip_has_a_poster():
    """
    poster.jpg 는 prefers-reduced-motion 대체본입니다. 없으면 움직임을
    끈 사람에게 아무것도 안 보입니다.
    """
    root = WEB / "public" / "scene"
    if not root.exists():
        pytest.skip("에셋이 아직 없습니다")
    for d in root.rglob("*"):
        if not d.is_dir():
            continue
        if any((d / f).exists() for f in ("clip.webm", "clip.mp4")):
            assert (d / "poster.jpg").exists(), ("%s poster.jpg 없음" % d.name)
