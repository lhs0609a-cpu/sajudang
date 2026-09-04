# -*- coding: utf-8 -*-
"""
명령어가 **그 화면에 맞는가.**

★ 손님이 시킨 것 (2026-09-04)

  "지금 전체 이미지 명령어랑 힉스필드 명령어 더 디테일하고 완벽하게
  **그 화면에 딱 맞게** 설계되어있는지 전수점검하고 다 개선해줘."

★ 무엇이 틀려 있었나

  명령어는 그림을 잘 적고 있었습니다. 그런데 **그 그림이 어디에
  걸리는지**가 한 줄도 없었습니다.

    · 원본은 전부 9:16 세로인데 인라인 장면은 4:3 상자로 잘라 씁니다.
      **세로의 42%만** 보입니다. 그걸 모르고 그리면 주제가 잘려 나갑니다.
    · 초상은 눈높이 37% 를 붙잡고 **2.6배 확대**해 얼굴만 씁니다.
      그 말이 없으면 크롭이 턱이나 이마에 떨어집니다.
    · 워터마크를 막는 줄이 쉰여덟 장 중 **한 장도** 없었습니다.
    · 착색 장면 다섯은 무채색으로 뽑아야 하는데 그 지시가 없었습니다.
    · 비율·길이 선언이 manifest 와 열한 군데 어긋나 있었습니다.

★ 어떻게 고쳤나

  쉰여덟 장에 손으로 적으면 한 장은 빠집니다. 공통 규칙을 한 자리에
  두고(SHOT · SHOT_CHAR · SHOT_FIGURE …) 화면이 **복사되는 글에
  붙여서** 냅니다. 화면별 쓰임은 `tools/prompt_use.py` 가 **코드에서
  읽어** 박습니다 — 손으로 적으면 화면을 옮길 때마다 갈립니다.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "apps" / "web"
PROMPTS = WEB / "public" / "asset-prompts.json"
MODAL = WEB / "components" / "scene" / "PromptModal.tsx"


def bundle() -> dict:
    return json.loads(PROMPTS.read_text(encoding="utf-8"))


# ── 공통 규칙이 서 있고, 붙어서 나가는가 ─────────────────
SHARED = ("SHOT", "SHOT_TINT", "SHOT_LOOP", "SHOT_FILL",
          "SHOT_CHAR", "SHOT_FIGURE", "PIPE", "ANIMBASE")


def test_shared_rules_exist():
    d = bundle()
    for k in SHARED:
        assert (d.get(k) or "").strip(), "공통 규칙 %s 가 없소" % k


def test_the_rules_ride_along_with_the_copy():
    """
    파일에만 있고 **복사되는 글에 안 붙으면** 없는 것과 같다.
    그림을 맡기는 사람은 카드 하나를 복사해 붙일 뿐이다.
    """
    src = MODAL.read_text(encoding="utf-8")
    assert "fullImage" in src, "복사되는 글에 규칙을 안 붙이오"
    for k in ("SHOT", "SHOT_CHAR", "SHOT_FIGURE", "SHOT_TINT",
              "SHOT_LOOP", "SHOT_FILL"):
        assert "data.%s" % k in src, "%s 를 안 붙이오" % k


def test_the_rules_say_the_things_that_cost_money_to_redo():
    """
    되돌리기 비싼 것 — 워터마크 · 글자 · 잘리는 자리 · 규격.
    다시 뽑아야 하는 것들이라 명령어 안에 있어야 한다.
    """
    d = bundle()
    for k, must in (
        ("SHOT", ("9:16", "watermark", "no text", "42%")),
        ("SHOT_CHAR", ("768", "1024", "transparent", "watermark", "2.6x")),
        ("SHOT_FIGURE", ("768", "transparent", "watermark", "STILL")),
        ("SHOT_TINT", ("DESATURATED",)),
        ("SHOT_LOOP", ("last frame", "first frame")),
    ):
        low = d[k].lower()
        for m in must:
            assert m.lower() in low, "%s 에 «%s» 가 없소" % (k, m)


def test_the_pipeline_covers_the_watermark_and_the_codec():
    """
    ★ 실제로 물렸던 자리 — 힉스필드 표식(✦)과 HEVC.
      받은 클립을 그대로 넣으면 표식이 남고, 사파리 밖에서 안 돕니다.
    """
    pipe = bundle()["PIPE"]
    assert "✦" in pipe, "힉스필드 표식을 잘라내라는 말이 없소"
    assert "HEVC" in pipe, "HEVC 로 나올 때 어쩌라는 말이 없소"
    assert "H.264" in pipe and "VP9" in pipe, "두 벌로 뽑으라는 말이 없소"
    assert "poster" in pipe, "poster 를 뽑으라는 말이 없소"


# ── 화면별 쓰임이 코드와 맞는가 ──────────────────────────
def test_every_scene_says_how_it_is_cropped():
    d = bundle()
    for sid, p in d["scenes"].items():
        assert (p.get("use") or "").strip(), \
            "%s — 이 화면에서 어떻게 걸리는지 안 적혔소" % sid


def test_the_usage_lines_are_generated_not_hand_written():
    """
    손으로 적으면 화면을 옮길 때마다 갈린다. 도구를 다시 돌렸을 때
    바뀌는 게 있으면 낡은 것이다.
    """
    out = subprocess.run(
        [sys.executable, str(ROOT / "tools" / "prompt_use.py")],
        capture_output=True, text=True, encoding="utf-8", cwd=str(ROOT))
    m = re.search(r"쓰임을 적을 것 (\d+)", out.stdout or "")
    assert m, "prompt_use 가 안 돌았소:\n%s" % (out.stderr or "")[-400:]
    assert m.group(1) == "0", \
        "화면이 바뀌었는데 쓰임을 안 다시 적었소 — python tools/prompt_use.py --write"


def test_the_audit_passes():
    """전수 감사가 통과해야 한다. 이게 관문이다."""
    out = subprocess.run(
        [sys.executable, str(ROOT / "tools" / "prompt_audit.py")],
        capture_output=True, text=True, encoding="utf-8", cwd=str(ROOT))
    assert out.returncode == 0, (out.stdout or "")[-900:]


# ── 화면이 그 상자로 그리는가 ────────────────────────────
def test_inline_scenes_are_boxed():
    """
    ★ 9:16 영상이 인라인에서 `height:auto` 로 흐르면 폭의 178% 높이가
      되어 아래 버튼이 화면 밖으로 밀립니다. 상자를 늘 잡아야 합니다 —
      전에는 `spec.box` 가 있을 때만 걸었는데 **아무도 box 를 안
      적어서** 한 번도 안 걸렸습니다.
    """
    src = (WEB / "components" / "scene" / "Scene.tsx").read_text(
        encoding="utf-8")
    assert 'className={`sceneart boxed' in src, \
        "인라인 장면이 상자 없이 흐르오"
