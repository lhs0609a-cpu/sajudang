# -*- coding: utf-8 -*-
"""
그림과 글이 어긋나지 않는가.

★ 왜 지키나

  a4b 의 그림은 목패와 종이쪽만 있고 프롬프트에 「No hands, no faces」가
  박혀 있었는데, 바로 아래 글은 「그가 종이 한 장을 더 꺼냈다」였다.
  a5 는 밤 들판의 갈림길인데 글은 「붓을 내려놓고, 그가 물었다」였다.

  손님은 둘 중 무엇을 믿을지 몰라 한다. 그리고 이런 어긋남은 **그림이
  들어온 뒤에야** 드러난다 — 자리표시 SVG 위에서는 무슨 글을 적어도
  안 어색하다.

★ 몸짓만 보다가 물건을 놓쳤다 (2026-09-06)

  손이 있는가만 보고 있었습니다. 그런데 손님이 짚은 자리는 손이
  아니었습니다 — c2 본문의 글은 「도령이 두루마리 끈을 풀었다.
  종이가 무릎까지 흘러내렸다.」인데 영상은 **눌린 꽃이 놓인 낡은 종이
  한 장**이었습니다. 두루마리도 끈도 없습니다.

  전수로 보니 열 자리가 그랬습니다. 글이 부르는 **물건**이 그림에
  없었습니다 — 붓·먹·목패·인장·상·사람·길.

  그래서 이 자는 이제 셋을 봅니다.

    ① 글이 손을 말하면 그림에 손이 있는가
    ② 글이 부르는 물건이 그림에 있는가   (KO→EN 대응표)
    ③ 글이 센 수와 그림이 그린 수가 같은가

  대응표는 **적어 두고** 씁니다. 새 낱말이 나오면 표에 없어서 안
  걸립니다 — 그건 표를 늘릴 자리이지 검사를 끌 자리가 아닙니다.

★ 얼굴은 그림에 안 넣는다

  도령 얼굴은 초상(CharArt · Meet)으로 따로 나온다. 배경에 또 그리면
  같은 사람이 둘이 된다. 손목까지만 그린다.
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "apps" / "web"
BUNDLE = json.loads(
    (WEB / "public" / "asset-prompts.json").read_text(encoding="utf-8"))

# 사람의 몸짓을 말하는 글
#
# ★ 「풀었」이 없어서 c2 가 안 걸렸습니다. 끈을 푸는 것은 손이 하는
#   일인데 표에 없었습니다. 「넘겼」도 같습니다.
ACT = re.compile(r"(꺼냈|들었|내려놓|펼쳤|접었|건넸|짚었|따랐|풀었|넘겼|얹었)")

# ★ 글이 아예 「손」이라고 적은 자리. 이건 은유가 아닙니다.
HAND_WORD = re.compile(r"손(을|이|에|으로)?\b|손을|손이|손끝")

# ★ 손을 찾을 때 「hand-less」 「handle」 을 손으로 세면 안 됩니다.
#   실제로 handle 장면(문고리)이 그래서 잘못 걸렸습니다 —
#   프롬프트 첫 줄이 "hand-less wooden lattice door" 입니다.
HAND = re.compile(r"\bhands?\b(?!-)")

# ── 글이 부르는 물건 → 그림이 적어야 하는 말 ────────────
#
#   왼쪽은 나레이션에 나오는 낱말, 오른쪽은 그림 명령어에 하나라도
#   있어야 하는 영어입니다. 없으면 그 물건이 화면에 없다는 뜻입니다.
THING = {
    "두루마리": ("scroll",),
    "끈":       ("cord", "silk tie", "ribbon"),
    "종이":     ("paper", "hanji", "sheet", "leaf", "slip", "note"),
    "붓":       ("brush",),
    "먹":       ("ink",),
    "목패":     ("plaque", "tablet"),
    "인장":     ("seal", "stamp"),
    "엽전":     ("coin",),
    "문고리":   ("handle", "knob"),
    "대문":     ("gate",),
    "등불":     ("lantern", "lamp"),
    "고양이":   ("cat",),
    "벽":       ("wall",),
    "길":       ("path", "road", "lane", "trail"),
    "갈래":     ("split", "branch", "direction", "fork"),
    "상":       ("table", "tray", "desk", "altar"),
    "방석":     ("cushion",),
    "자리":     ("cushion", "seat", "place", "spot"),
    "첩":       ("booklet", "book"),
    "꽃":       ("flower", "blossom"),
    "무릎":     ("knee", "lap"),
    "사람":     ("figure", "person", "man", "woman", "fortune-teller",
                 "seated"),
    "불":       ("light", "flame", "lantern", "glow", "lit"),
}

# 글이 센 수 → 그림이 적어야 하는 수.
#
# ★ 「한」은 뺐습니다. 「한 겹」 「한 장」은 세는 말이라기보다 관사라서
#   넣으면 아무 데나 걸립니다.
COUNT = {
    "둘": "two", "두": "two",
    "셋": "three", "세": "three",
    "넷": "four", "네": "four",
    "다섯": "five", "여섯": "six", "일곱": "seven",
    "여덟": "eight", "아홉": "nine",
    "스무": "twenty", "스물": "twenty",
}
# ★ 「두루마리」의 「두」를 둘로 세면 안 됩니다. 물건 이름을 먼저
#   걷어내고, 세는 말 뒤에 조사나 세는 단위가 붙은 것만 셉니다.
COUNT_RE = re.compile(
    r"(%s)(?=[\s이가은는을를에의,.]|개|장|칸|갈래|줄|명|번)"
    % "|".join(sorted(COUNT, key=len, reverse=True)))


def draws_a_hand(img: str) -> bool:
    """
    그림에 **손이 있는가**.

    ★ 「No hands, no text」 의 hands 를 손으로 세면 안 됩니다. 손을
      그리지 말라는 말인데 그리라는 말로 읽습니다 — 실제로 여덟 장면이
      그래서 잘못 걸렸습니다. 부정문을 먼저 걷어냅니다.
    """
    # 줄바꿈이 사이에 낄 수 있습니다. 부정문은 줄이 갈려도 부정문입니다.
    return bool(HAND.search(re.sub(r"[Nn]o\s+hands?", " ", img)))


def _pairs():
    """
    장면과 **그 장면에 딸린** 나레이션.

    ★ 다음 `<Scene` 앞에서 끊습니다. 안 끊으면 c4 의 안 파는 갈래가
      바로 아래 갈래의 글을 제 것인 양 끌어옵니다.
    """
    for p in sorted((WEB / "app").rglob("*.tsx")):
        code = re.sub(r"/\*.*?\*/", " ", p.read_text(encoding="utf-8"),
                      flags=re.S)
        code = re.sub(r"//[^\n]*", " ", code)
        for m in re.finditer(r'<Scene\s+id="(\w+)"([^/>]*)/>', code):
            rest = code[m.end():]
            nxt = rest.find("<Scene ")
            block = rest[:nxt if nxt >= 0 else len(rest)]
            nar = re.search(r"<Narration[^>]*lines=\{\[(.*?)\]\}", block, re.S)
            lines = re.findall(r'"([^"]{2,80})"', nar.group(1)) if nar else []
            yield (str(p.relative_to(WEB).as_posix()), m.group(1), lines,
                   "<Meet" in block[:600])


def _art(sid: str) -> str:
    e = BUNDLE["scenes"].get(sid) or {}
    if e.get("seasonal"):
        img = " ".join((e.get("seasons") or {}).values())
    else:
        img = e.get("image") or ""
    return img + " " + (e.get("motion") or "")


def test_a_scene_with_a_gesture_line_shows_a_hand():
    """몸짓을 말했으면, 글이 손이라 적었으면, 그림에 손이 있어야 한다."""
    bad = []
    for where, sid, lines, has_meet in _pairs():
        act = [l for l in lines if ACT.search(l) or HAND_WORD.search(l)]
        if not act:
            continue
        # ★ 첫 대면(<Meet>)이 바로 아래 붙어 있으면 그 사람이 이미
        #   화면에 있습니다. a4 의 「도령이 고개를 들었다」가 그렇습니다 —
        #   고개는 그림이 아니라 초상이 듭니다.
        if has_meet:
            continue
        img = (BUNDLE["scenes"].get(sid) or {}).get("image") or ""
        if re.search(r"[Nn]o\s+hands", img) or not draws_a_hand(img):
            bad.append("%s %s — 글 「%s」 인데 그림에 손이 없다"
                       % (where, sid, act[0]))
    assert not bad, "글과 그림이 어긋난다:\n  " + "\n  ".join(bad)


def test_the_things_the_words_name_are_in_the_picture():
    """
    ★ 글이 부르는 물건이 그림에 있어야 한다.

      「두루마리 끈을 풀었다」인데 그림에 두루마리도 끈도 없으면
      손님은 무엇을 보고 있는지 모른다.
    """
    bad = []
    for where, sid, lines, _ in _pairs():
        art = _art(sid).lower()
        for line in lines:
            for ko, ens in THING.items():
                if ko not in line:
                    continue
                # ★ 낱말 경계로 봅니다. 「man」 이 「romance」 안에서
                #   걸려 빈 방석이 사람 있는 그림으로 통과했습니다.
                if not any(re.search(chr(92) + "b" + re.escape(en), art)
                           for en in ens):
                    bad.append("%s %s — 글 「%s」 의 «%s» 가 그림에 없다 "
                               "(찾은 말: %s)"
                               % (where, sid, line, ko, "/".join(ens)))
    assert not bad, "글이 부르는 물건이 그림에 없다:\n  " + "\n  ".join(bad)


def test_the_counts_agree():
    """
    ★ 글이 셋이라 하면 그림도 셋이라야 한다.

      d1 은 「목패 셋이 상 위에 놓였다」인데 그림은 넉 장이었다.
      손님은 세어 본다.
    """
    bad = []
    for where, sid, lines, _ in _pairs():
        art = _art(sid).lower()
        for line in lines:
            if not any(ko in line for ko in THING):
                continue
            plain = line
            for ko in THING:
                plain = plain.replace(ko, " ")
            for ko in set(COUNT_RE.findall(plain)):
                en = COUNT[ko]
                if en not in art:
                    bad.append("%s %s — 글 「%s」 는 %s(%s)인데 그림이 안 센다"
                               % (where, sid, line, ko, en))
    assert not bad, "세는 수가 갈린다:\n  " + "\n  ".join(bad)


def test_scene_art_never_draws_the_character_face():
    """얼굴은 초상으로 따로 나온다. 배경에 또 그리면 둘이 된다."""
    bad = []
    for sid, e in BUNDLE["scenes"].items():
        img = e.get("image") or ""
        if draws_a_hand(img) and not re.search(
                r"[Nn]o\s+faces?|face is not visible|no\s+head", img):
            bad.append(sid)
    assert not bad, "손을 그리면서 얼굴을 막지 않았다: %s" % bad
