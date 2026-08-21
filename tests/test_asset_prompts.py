"""
에셋 프롬프트 — 40장이 하나도 안 빠졌는가, 복사해서 바로 쓸 수 있는가.

여기가 무너지면 사람이 그림을 만들다가 알게 됩니다. 그때는 이미
잘못된 프롬프트로 몇 장을 뽑은 뒤입니다.

  · 영상 앵커가 빠지면      → 3초 안에 얼굴이 사진처럼 변합니다 (docs/10 §2)
  · 계절 프롬프트가 하나면  → 봄·가을·겨울이 통째로 빕니다
  · 폴더 경로가 어긋나면    → 만들어 넣어도 화면에 안 나옵니다
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
BUNDLE = ROOT / "apps" / "web" / "public" / "asset-prompts.json"
FIG_SRC = ROOT / "seed" / "figure_prompts.json"
SHEET = ROOT / "에셋_프롬프트_전체.txt"
SCENE_TSX = ROOT / "apps" / "web" / "components" / "scene" / "Scene.tsx"
MODAL = ROOT / "apps" / "web" / "components" / "scene" / "PromptModal.tsx"

ANCHOR = "2D hand-drawn animation"
SEASONS = ["spring", "summer", "autumn", "winter"]

# 계절마다 이 꽃이어야 합니다. 착색으로는 꽃 모양을 못 바꿉니다.
FLOWER = {
    "spring": "cherry blossom",
    "summer": "trumpet-creeper",
    "autumn": "chrysanthemum",
    "winter": "plum branches",
}


def bundle() -> dict:
    return json.loads(BUNDLE.read_text(encoding="utf-8"))


def entries() -> dict:
    b = bundle()
    return {**b["scenes"], **b["figures"]}


# ══════════════════════════════════════════════════════════
# 하나도 안 빠졌는가
# ══════════════════════════════════════════════════════════
def test_every_scene_and_figure_has_both_prompts():
    missing = [k for k, v in entries().items() if not v.get("image") or not v.get("motion")]
    assert not missing, "프롬프트가 빈 항목: %s" % missing


def test_counts():
    b = bundle()
    assert len(b["scenes"]) == 24
    assert len(b["figures"]) == 13


@pytest.mark.parametrize("key", sorted(entries()))
def test_motion_carries_the_video_anchor(key):
    """이 문구가 빠진 채로 복사되면 3초 안에 그림이 실사로 변합니다."""
    assert ANCHOR in entries()[key]["motion"], key


def test_no_unsubstituted_placeholder():
    """참조 구현체가 문자 그대로 남기던 자리표시가 새어 나오면 안 됩니다."""
    raw = BUNDLE.read_text(encoding="utf-8")
    assert "$" + "{ANIMBASE}" not in raw


# ══════════════════════════════════════════════════════════
# 계절을 타는 장면
# ══════════════════════════════════════════════════════════
def test_gate_carries_all_four_seasons():
    g = bundle()["scenes"]["gate"]
    assert g["seasonal"] is True
    assert sorted(g["seasons"]) == sorted(SEASONS)


@pytest.mark.parametrize("season", SEASONS)
def test_each_season_names_its_own_flower(season):
    g = bundle()["scenes"]["gate"]
    text = g["seasons"][season].lower()
    assert FLOWER[season] in text, "%s 에 %s 가 없습니다" % (season, FLOWER[season])
    others = [f for s, f in FLOWER.items() if s != season and f in text]
    assert not others, "%s 에 다른 계절의 꽃이 섞였습니다: %s" % (season, others)


def test_the_four_seasons_are_actually_different():
    seasons = bundle()["scenes"]["gate"]["seasons"]
    assert len({seasons[s] for s in SEASONS}) == 4


def test_only_gate_is_seasonal():
    """계절 장면이 늘면 이 테스트가 먼저 알려 줍니다."""
    seasonal = [k for k, v in bundle()["scenes"].items() if v.get("seasonal")]
    assert seasonal == ["gate"], seasonal


# ══════════════════════════════════════════════════════════
# 만들어 넣으면 실제로 화면에 뜨는가
# ══════════════════════════════════════════════════════════
def test_component_reads_the_season_folder():
    """
    계절 장면은 /scene/gate/{계절}/ 을 봐야 합니다. 한 폴더만 보면
    넉 장을 만들어 넣어도 한 장만 쓰이고 나머지는 자리표시로 남습니다.
    """
    src = SCENE_TSX.read_text(encoding="utf-8")
    assert "spec?.seasonal" in src
    assert "/scene/${id}/${season}/" in src
    # poster·webm·mp4 가 전부 같은 base 를 써야 합니다
    for f in ("poster.jpg", "clip.webm", "clip.mp4"):
        assert "${base}" + f in src, f


def test_modal_shows_the_season_you_are_on():
    src = MODAL.read_text(encoding="utf-8")
    assert "seasons?.[season]" in src
    assert "/scene/${id}/${season}/" in src
    assert "계절 넉 장이 필요하오" in src


# ══════════════════════════════════════════════════════════
# 인물 프롬프트의 원본이 살아 있는가
# ══════════════════════════════════════════════════════════
def test_figure_prompts_have_a_checked_in_source():
    """
    산출물에서 거꾸로 읽으면 추출기를 다시 돌릴 때 인물이 날아갑니다.
    """
    assert FIG_SRC.exists(), "seed/figure_prompts.json 이 없습니다"
    src = json.loads(FIG_SRC.read_text(encoding="utf-8"))
    keys = [k for k in src if k != "_"]
    assert len(keys) == 13
    built = bundle()["figures"]
    for k in keys:
        assert k in built
        assert built[k]["image"] == src[k]["image"]
        assert built[k]["motion"] == src[k]["motion"]


def test_extractor_reads_the_source_not_the_output():
    tool = (ROOT / "tools" / "extract_asset_prompts.js").read_text(encoding="utf-8")
    assert "seed/figure_prompts.json" in tool
    assert "asset-prompts.json" not in tool.split("const FIG_SRC")[1][:400]


# ══════════════════════════════════════════════════════════
# 넘겨 준 텍스트 한 장
# ══════════════════════════════════════════════════════════
def sheet() -> str:
    return SHEET.read_text(encoding="utf-8")


def test_sheet_exists_and_lists_every_item():
    s = sheet()
    n = len(entries()) + 3          # 대문이 계절만큼 늘어난다
    assert n == 40
    heads = re.findall(r"^\s{2}(\d{2}) / 40\s", s, re.M)
    assert len(heads) == 40, "항목 %d개만 있습니다" % len(heads)
    assert [int(x) for x in heads] == list(range(1, 41)), "번호가 건너뜁니다"


def test_sheet_has_both_prompt_blocks_for_every_item():
    s = sheet()
    assert s.count("① 이미지 · 제미나이") == 40
    assert s.count("② 모션 · 힉스필드") == 40


def test_sheet_never_drops_the_video_anchor():
    """항목마다 하나씩. 머리말에도 한 번 나오므로 통째로 세면 안 됩니다."""
    blocks = re.split(r"^={70,}$\n^\s{2}\d{2} / 40\s", sheet(), flags=re.M)[1:]
    assert len(blocks) == 40
    bad = [b.splitlines()[0].strip() for b in blocks if ANCHOR not in b]
    assert not bad, "영상 앵커가 빠진 항목: %s" % bad


def test_sheet_carries_no_placeholder():
    assert "$" + "{ANIMBASE}" not in sheet()


@pytest.mark.parametrize("season", SEASONS)
def test_sheet_has_a_folder_line_for_each_gate_season(season):
    assert "public/scene/gate/%s/" % season in sheet()


def test_sheet_folders_match_the_component_paths():
    """텍스트가 시키는 폴더와 앱이 찾는 폴더가 같아야 합니다."""
    s = sheet()
    for key in bundle()["figures"]:
        assert "public/sinsal/%s/" % key in s
    for key, v in bundle()["scenes"].items():
        if v.get("seasonal"):
            continue
        assert "public/scene/%s/" % key in s


def test_sheet_warns_about_the_three_traps():
    s = sheet()
    assert ANCHOR in s
    assert "grayscale(1)" in s              # 착색 CSS
    assert "붙임 3" in s                     # 지금은 안 쓰이는 door
