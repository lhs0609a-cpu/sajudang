"""
스무 사람의 얼굴 — 초상 발주서.

    python tools/char_sheet.py                한 장으로 뽑는다
    python tools/char_sheet.py pungun         한 사람만
    python tools/char_sheet.py --write 캐릭터_초상_발주서.txt

★ 왜 이 도구가 생겼나

  발주서(docs/10 §7)는 `/char/{id}/bust.png` 768×1024 를 요구하는데,
  **무엇을 그릴지는 아무 데도 없었습니다.** 신살 인물 13명은 프롬프트가
  있고 장면 24개도 있는데, 정작 이 집이 파는 **스무 사람**만 없었습니다.

  그래서 화면에 얼굴이 없었고, 손님은 일곱 화면을 지나도록 그 사람을
  못 봤습니다.

★ 지어내지 않습니다

  각 사람의 것은 이미 정해져 있습니다 — 이름·한자·유파·원형(archetype)·
  성별·색·전문 분야. 여기서는 그걸 **그림 지시로 옮길 뿐**입니다.
  설정집에 없는 성격을 새로 붙이면 글과 그림이 갈립니다.

★ 화풍은 신살 인물과 같습니다

  같은 집의 사람들입니다. 화풍이 갈리면 스무 명이 한 집 식구로 안
  보입니다. 머리말은 asset-prompts.json 의 신살 인물 것을 그대로 씁니다.

★ 배경은 흰색입니다

  초상은 투명 PNG 로 잘라 써야 합니다(대사 옆·진열대·첫 대면에서 각각
  다른 바탕 위에 얹힙니다). 배경이 들어가면 잘라낼 수 없습니다.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LENSES = ROOT / "seed" / "lenses.json"
PROMPTS = ROOT / "apps" / "web" / "public" / "asset-prompts.json"

# ── 원형(archetype) → 얼굴·머리·옷 ─────────────────────────
#
#   설정집이 정한 원형을 그림 말로 옮긴 것입니다. 여기 없는 성격을
#   새로 붙이지 않습니다 — 글과 그림이 갈립니다.
LOOK = {
    "차가운 미남": ("a composed young nobleman with cool distant eyes and a "
                "straight mouth, black hair tied high with a jade pin, deep "
                "indigo scholar's robe with silver trim"),
    "백발 미청년": ("a serene young monk with long silver-white hair loose over "
                "one shoulder, pale grey-green eyes, plain undyed hemp robe, "
                "a single wooden bead bracelet"),
    "무뚝뚝한 장년": ("a broad-shouldered man in his forties, weathered face, "
                 "thick brows, unsmiling, greying topknot, worn dark blue "
                 "hanbok with rolled sleeves"),
    "야성적인": ("a rugged man with an unkempt topknot, a thin old scar across "
             "one brow, open collar, dark hemp robe"),
    "지적인 안경": ("a slender young man wearing round brass-rimmed spectacles, "
                "neat side-parted hair, a fine chain across his chest, "
                "pale grey robe with many small pockets"),
    "차가운 분석가": ("a woman with an unreadable calm face, hair pulled back "
                 "severely, silver hairpin, high-collared dark hanbok, "
                 "eyes catching a faint cold light"),
    "위험한 매력": ("a striking woman with a knowing half-smile, loose crimson "
                "hanbok slipping off one shoulder, dark red lips, a single "
                "long earring, hair falling free"),
    "서늘한 신비": ("a pale otherworldly young woman with long unbound black "
                "hair, distant unfocused gaze, layered gauzy pale-lilac "
                "hanbok that seems to drift"),
    "이국적 미남": ("a young man of foreign features — deeper set eyes, higher "
                "nose bridge, sun-darkened skin — dark travelling coat over "
                "hanbok, small brass astrolabe hanging at his belt"),
    "능글맞은 미남": ("a handsome man with a lazy amused grin, one brow raised, "
                 "hair carelessly tied, loose plum robe open at the throat, "
                 "a card held between two fingers"),
    "날카로운 미남": ("a sharp-featured man with narrow observing eyes that seem "
                 "to measure the viewer, thin lips, dark high-collared robe, "
                 "hands folded"),
    "인연을 매는 사람": ("a gentle woman with a soft knowing smile, moonlit pale "
                   "hanbok, a length of red thread wound loosely around her "
                   "fingers, hair in a low braid"),
    "압도적인 언니": ("a magnificent woman in her thirties, bold direct gaze, "
                 "richly embroidered deep-red hanbok, gold hairpin, arms "
                 "crossed, utterly unbothered"),
    "상처 있는 미남": ("a quiet young man with sad downcast eyes, faint shadows "
                  "beneath them, dark muted robe worn a little loose, hair "
                  "falling over one eye"),
    "편들지 않는 판관": ("a stern androgynous figure with a level unblinking gaze, "
                   "black official's robe, hair severely bound, holding a "
                   "closed brush case like a verdict"),
    "우아한 귀공자": ("an elegant young merchant prince, fine silk robe in muted "
                 "gold, immaculate topknot, an abacus-like ledger tucked "
                 "under one arm, faint polite smile"),
    "엄격한 연상": ("a stern older scholar with grey at the temples, small "
                "reading glasses low on the nose, dark scholar's robe, a "
                "bamboo cane rod held upright"),
    "다정한 연상": ("a warm woman in her thirties with kind tired eyes, sleeves "
                "tied back for work, soft moss-green hanbok, dried herbs "
                "tucked at her sash"),
    "무심한 미남": ("a beautiful man with a flat uninterested expression, looking "
                "slightly past the viewer, pale blue-grey robe, a small sun "
                "dial hanging from his belt"),
    "원조 걸크러쉬": ("a formidable old woman with a lined face and fierce clear "
                 "eyes, white hair in a tight knot, patched dark hanbok, a "
                 "long smoking pipe resting on her shoulder"),
    "청량한 소년": ("a bright clear-eyed boy of about fourteen, tousled hair, an "
                "open easy smile, simple pale-blue hanbok, sleeves too long "
                "for his arms"),
}

# ★ 정면 초상입니다 (2026-09-03).
#
#   전에는 「slight three-quarter angle」 이라 비스듬히 나왔습니다. 이
#   초상이 가장 크게 쓰이는 자리는 **대사 옆 66×88 조각**인데, 그 크기
#   에서 얼굴을 살짝 돌리면 한쪽 눈이 묻히고 시선이 손님을 비껴갑니다.
#   마주 앉은 자리라 눈이 마주쳐야 합니다.
#
#   금지도 같이 적습니다 — 생성기는 「정면」 한 마디로는 자꾸 3/4 로
#   돌아갑니다. no head turn · no profile 까지 박아야 섭니다.
TAIL = ("Bust-up from the chest up, centered, subject occupying about 72% of\n"
        "frame height. FRONT-FACING PORTRAIT — head and shoulders squared to\n"
        "the camera, both eyes fully visible and level, gaze straight at the\n"
        "viewer. Symmetrical. No head turn, no profile, no three-quarter angle.\n"
        "\n"
        "Flat solid pure white (#FFFFFF) background — no gradient, no scenery,\n"
        "no cast shadow, no vignette. No text, letters, numbers, logos or\n"
        "watermarks. Aspect ratio 3:4. High detail.")

# ── 표정 두 벌 ─────────────────────────────────────────────
#
#   얼굴 한 장으로 다 하면 **짚는 순간과 누그러뜨리는 순간이 같은
#   얼굴**이 됩니다. 훅 0단은 아픈 데를 찌르는 자리이고 만류 문구는
#   달래는 자리인데, 같은 표정이면 둘 다 힘을 잃습니다.
#
#   문장 뱅크를 세어 셋으로 정했습니다 —
#     짚는 말 26 · 누그러뜨리는 말 19 · 아니라고 하는 말 7
#   「아니라고 하는 말」은 짚는 얼굴에 접습니다. 일곱 마디를 위해
#   스무 명분을 더 그리는 것은 값이 안 맞습니다.
#
#   ★ 같은 사람이라야 합니다. 머리·옷·빛은 그대로 두고 **눈과 입만**
#     바꿉니다. 얼굴이 달라지면 다른 사람이 됩니다.
MOODS = {
    "cut": (
        "bust_cut.png", "짚는",
        "Same character, same hair, same clothing, same lighting — only the\n"
        "expression changes. Now the eyes are fixed directly on the viewer,\n"
        "narrowed very slightly, pupils sharp. The mouth is a straight line,\n"
        "no smile. One brow a fraction lower than the other. He has just\n"
        "said something true that the viewer did not want said. Not angry,\n"
        "not cruel — certain."),
    "soft": (
        "bust_soft.png", "누그러뜨리는",
        "Same character, same hair, same clothing, same lighting — only the\n"
        "expression changes. Now the eyes are lowered a little and softened,\n"
        "the outer corners easing down. The faintest warmth at the mouth,\n"
        "not quite a smile. The head tilts a few degrees toward the viewer.\n"
        "He is letting the viewer off. Kind, unhurried, a little tired."),
}


MOTION = ("Static camera. The character blinks once, slowly. Hair and sleeve\n"
          "edges drift as if in still air. The eyes stay on the viewer.\n"
          "Nothing else moves — no head turn, no expression change.")


def house_style() -> str:
    """신살 인물과 **같은** 머리말. 갈리면 한 집 식구로 안 보입니다."""
    d = json.loads(PROMPTS.read_text(encoding="utf-8"))
    img = d["figures"]["cheoneul"]["image"]
    return img[:img.index("\n\nA serene")].strip()


def animbase() -> str:
    d = json.loads(PROMPTS.read_text(encoding="utf-8"))
    return d["ANIMBASE"]


def colors() -> dict:
    """
    그 사람의 색. seed 에는 없고 화면 쪽(lenses.ts)에 있습니다.
    빛의 색을 그 사람 색으로 맞춰야 초상과 화면이 한 벌로 보입니다.
    """
    import re
    src = (ROOT / "apps" / "web" / "lib" / "lenses.ts").read_text(
        encoding="utf-8")
    return dict(re.findall(r'id: "(\w+)"[^}]*?color: "(#[0-9A-Fa-f]{3,8})"',
                           src))


COLOR: dict = {}


def lenses() -> list:
    return json.loads(LENSES.read_text(encoding="utf-8"))


def one(l: dict, style: str, anim: str) -> list:
    look = LOOK.get(l["archetype"])
    sex = "man" if l.get("sex") == "M" else "woman"
    who = look or ("a %s in Korean hanbok" % sex)
    # 그 사람의 색. seed 에는 없고 화면 쪽(lenses.ts)에 있습니다.
    tone = ("Key light subtly tinted %s. " % COLOR.get(l["id"], "").strip()
            if COLOR.get(l["id"]) else "")

    out = []
    out.append("=" * 74)
    out.append("  %s  %s   [%s]" % (l["name"], l["hanja"], l["id"]))
    out.append("  %s · %s · %s원 · 전문 %s"
               % (l["group"], l["archetype"], format(l["price"], ","),
                  l.get("specialty", "—")))
    out.append("  두는 곳  public/char/%s/bust.png   768×1024 투명 PNG · 눈높이 y=380"
               % l["id"])
    out.append("=" * 74)
    out.append("")
    out.append("--- ① 이미지 ---")
    out.append(style)
    out.append("")
    out.append(who + "." + ((" " + tone.strip()) if tone else ""))
    out.append("")
    out.append(TAIL)
    out.append("")
    for key in ("cut", "soft"):
        fn, ko, extra = MOODS[key]
        out.append("--- ①-%s 표정 · %s ---" % (ko, fn))
        out.append(extra)
        out.append("")
        out.append("  나머지는 위 ① 과 똑같이. 배경도 흰색, 3:4.")
        out.append("  두는 곳  public/char/%s/%s" % (l["id"], fn))
        out.append("")

    out.append("--- ② 모션 (선택 · clip.webm) ---")
    out.append(MOTION)
    out.append("")
    out.append(anim)
    out.append("")
    return out


def main() -> int:
    ls = lenses()
    COLOR.update(colors())
    style, anim = house_style(), animbase()

    # ★ `--write 파일이름` 의 **값**을 사람 이름으로 세면 안 됩니다.
    #   처음 판이 그래서 "그런 사람이 없소: 캐릭터_초상_발주서.txt" 라고
    #   했습니다.
    argv, pick, skip = sys.argv[1:], [], False
    for a in argv:
        if skip:
            skip = False
            continue
        if a == "--write":
            skip = True
            continue
        if a.startswith("--"):
            continue
        pick.append(a)
    rows = [l for l in ls if not pick or l["id"] in pick]
    if pick and not rows:
        print("그런 사람이 없소: %s" % ", ".join(pick))
        print("있는 사람: %s" % ", ".join(l["id"] for l in ls))
        return 1

    missing = [l["name"] for l in ls if l["archetype"] not in LOOK]
    lines: list[str] = []
    lines.append("=" * 74)
    lines.append("  성신당 · 스무 사람 초상 발주서")
    lines.append("  화풍은 신살 인물과 같습니다 — 한 집 식구라야 합니다.")
    lines.append("  배경은 흰색입니다. 투명 PNG 로 잘라 써야 합니다 —")
    lines.append("  대사 옆 · 진열대 · 첫 대면이 서로 다른 바탕 위에 얹힙니다.")
    lines.append("=" * 74)
    lines.append("")
    if missing:
        lines.append("★ 그림 말이 아직 없는 원형: %s" % ", ".join(missing))
        lines.append("")

    for l in rows:
        lines += one(l, style, anim)

    # ── 화면이 읽는 묶음에도 넣는다 ─────────────────────────
    #
    # ★ 장면은 눌러서 프롬프트를 볼 수 있는데 캐릭터는 못 봤습니다.
    #   프롬프트가 이 도구(파이썬) 안에만 있어서 화면이 읽을 길이
    #   없었기 때문입니다. asset-prompts.json 에 `chars` 로 넣습니다 —
    #   장면·신살 인물과 **같은 자리**입니다.
    if "--json" in sys.argv:
        d = json.loads(PROMPTS.read_text(encoding="utf-8"))
        d["chars"] = {}
        for l in ls:
            look = LOOK.get(l["archetype"])
            sexw = "man" if l.get("sex") == "M" else "woman"
            who = look or ("a %s in Korean hanbok" % sexw)
            tone = (" Key light subtly tinted %s." % COLOR[l["id"]]
                    if COLOR.get(l["id"]) else "")
            d["chars"][l["id"]] = {
                "title": "%s %s" % (l["name"], l["hanja"]),
                "who": "%s · %s" % (l["group"], l["archetype"]),
                "hint": "전문 %s · %s원" % (l.get("specialty", "—"),
                                          format(l["price"], ",")),
                "spec": ["3:4", "초상", "768×1024 투명 PNG · 눈높이 y=380"],
                "seasonal": False, "seasons": None, "note": None,
                "preset": "Static", "ratio": "3:4", "duration": "3s",
                "loop": True, "tint": False, "still": False,
                "image": style + "\n\n" + who + "." + tone + "\n\n" + TAIL,
                "motion": MOTION + "\n\n" + anim,
                # 표정 두 벌 — 모달이 같이 보여 줍니다
                "moods": {k: {"file": v[0], "ko": v[1], "image": v[2]}
                          for k, v in MOODS.items()},
            }
        PROMPTS.write_text(json.dumps(d, ensure_ascii=False, indent=2) + "\n",
                           encoding="utf-8")
        print("화면이 읽는 묶음에 %d명을 넣었습니다 — %s"
              % (len(d["chars"]), PROMPTS.name))

    text = "\n".join(lines)
    if "--write" in sys.argv:
        i = sys.argv.index("--write")
        out = ROOT / (sys.argv[i + 1] if len(sys.argv) > i + 1
                      else "캐릭터_초상_발주서.txt")
        out.write_text(text + "\n", encoding="utf-8")
        print("%d명을 적었습니다 — %s" % (len(rows), out))
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
