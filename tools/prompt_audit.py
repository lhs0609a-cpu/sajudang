# -*- coding: utf-8 -*-
"""
명령어 감사 — 그림을 맡기기 **전에** 명령어가 화면에 맞는지 본다.

    python tools/prompt_audit.py
    python tools/prompt_audit.py --why    빠진 것을 장면마다 다 적는다

★ `asset_audit.py` 와 무엇이 다른가

  그 자는 **붙일 자리가 있는가**를 봅니다 — 화면이 부르는데 발주서에
  없는 장면, 만들어도 안 나오는 장면. 자리 얘기입니다.

  이 자는 **명령어 자체**를 봅니다. 자리는 맞는데 명령어가 틀리면
  그림은 나오고 화면에는 안 맞습니다. 그리고 그건 되돌리기 가장
  비싼 실수입니다 — 다시 뽑아야 합니다.

★ 무엇이 실제로 틀려 있었나 (2026-09-04 첫 조사)

    워터마크를 막는 줄      쉰여덟 장 중 **0장**
    가장자리를 비우라는 줄   여섯 장
    글자 금지               열여덟 장 (일곱 장이 빠져 있었음)
    무채색 지시             착색 장면 다섯 중 **0장**
    비율·길이 선언          manifest 와 열한 군데 어긋남

  손으로 쉰여덟 장에 적으면 한 장은 빠집니다. 공통 규칙(SHOT)을 한
  자리에 두고 화면이 **복사되는 글에 붙여서** 냅니다. 이 자는 그
  붙임이 살아 있는지, 그리고 장면마다 다른 몫이 맞는지 봅니다.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "apps" / "web"
PROMPTS = WEB / "public" / "asset-prompts.json"
MANIFEST = WEB / "components" / "scene" / "manifest.ts"
MODAL = WEB / "components" / "scene" / "PromptModal.tsx"

# 명령어가 반드시 들고 있어야 하는 것 — 없으면 다시 뽑아야 합니다
NEED_SHOT = ("SHOT", "SHOT_TINT", "SHOT_LOOP", "SHOT_FILL",
             "SHOT_CHAR", "SHOT_FIGURE", "PIPE", "ANIMBASE")


def manifest() -> dict:
    src = MANIFEST.read_text(encoding="utf-8")
    out = {}
    for m in re.finditer(r'\{ id: "(\w+)", (.*?) \},', src):
        row = dict(re.findall(r'(\w+): "([^"]*)"', m.group(2)))
        row.update({k: v == "true"
                    for k, v in re.findall(r'(\w+): (true|false)', m.group(2))})
        row.update({k: int(v)
                    for k, v in re.findall(r'(\w+): (\d+)', m.group(2))})
        out[m.group(1)] = row
    return out


def body(p: dict) -> str:
    if p.get("seasonal"):
        return " ".join((p.get("seasons") or {}).values())
    return p.get("image") or ""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--why", action="store_true")
    a = ap.parse_args()

    d = json.loads(PROMPTS.read_text(encoding="utf-8"))
    man = manifest()
    modal = MODAL.read_text(encoding="utf-8")
    bad: list[str] = []

    print("=" * 74)
    print("  명령어 감사 — 화면에 맞게 적혀 있는가")
    print("=" * 74)

    # ── ① 공통 규칙이 서 있는가 ───────────────────────────
    print("\n[1] 공통 규칙")
    for k in NEED_SHOT:
        ok = bool((d.get(k) or "").strip())
        print("  %-11s %s" % (k, "있음" if ok else "**없음**"))
        if not ok:
            bad.append("공통 규칙 %s 가 없소" % k)
    # 화면이 그걸 **붙여서** 내는가. 파일에만 있고 안 붙이면 없는 것과 같습니다.
    for k in ("SHOT", "SHOT_TINT", "SHOT_LOOP", "SHOT_FILL",
              "SHOT_CHAR", "SHOT_FIGURE"):
        if "data.%s" % k not in modal:
            bad.append("PromptModal 이 %s 를 안 붙이오 — 복사해도 안 따라가오" % k)
    print("  붙이는가      %s"
          % ("예" if "fullImage" in modal else "**아니오**"))

    # ── ② 선언이 서로 맞는가 ─────────────────────────────
    print("\n[2] 선언 — manifest ↔ 명령어")
    cam = set(d.get("CAM", {}))
    scenes = d.get("scenes", {})
    rows = []
    for sid, spec in man.items():
        p = scenes.get(sid)
        if not p:
            bad.append("%s — manifest 에 있는데 명령어가 없소" % sid)
            continue
        for key, pk, ko in (("preset", "preset", "프리셋"),
                            ("ratio", "ratio", "비율")):
            av, bv = spec.get(key), p.get(pk)
            if av and bv and av != bv:
                rows.append("%-9s %s  manifest=%s  명령어=%s" % (sid, ko, av, bv))
                bad.append("%s %s 가 갈렸소" % (sid, ko))
        sec, dur = spec.get("seconds"), (p.get("duration") or "").rstrip("s")
        if sec and dur and str(sec) != dur:
            rows.append("%-9s 길이  manifest=%ss  명령어=%s" % (sid, sec, dur))
            bad.append("%s 길이가 갈렸소" % sid)
        if p.get("preset") not in cam:
            rows.append("%-9s 프리셋 «%s» 이 CAM 에 없소" % (sid, p.get("preset")))
            bad.append("%s 프리셋을 모르오" % sid)
    print("  어긋남 %d건" % len(rows))
    for r in rows:
        print("    · " + r)

    # ── ③ 장면마다 다른 몫 ───────────────────────────────
    print("\n[3] 장면마다 다른 몫")
    lack: dict[str, list] = {"쓰임 없음": [], "무채색": [], "루프 이음새": [],
                             "모션 없음": [], "스타일 잠금": [], "프리셋 충돌": []}
    for sid, p in scenes.items():
        mo = p.get("motion") or ""
        if not p.get("use"):
            lack["쓰임 없음"].append(sid)
        if p.get("tint") and not re.search(
                r"desaturat|greyscale|grayscale|monochrom", body(p) + mo, re.I):
            lack["무채색"].append(sid)
        if p.get("loop") and not re.search(
                r"loop|seamless|first and last", mo, re.I):
            lack["루프 이음새"].append(sid)
        if not mo.strip():
            lack["모션 없음"].append(sid)
        elif "hand-drawn animation" not in mo:
            lack["스타일 잠금"].append(sid)
        pr = p.get("preset") or ""
        if pr == "Static" and re.search(r"dolly|zoom|push in|pan ", mo, re.I):
            lack["프리셋 충돌"].append(sid)
        if pr.startswith("Dolly") and not re.search(
                r"dolly|move|toward", mo, re.I):
            lack["프리셋 충돌"].append(sid + "(정지 서술)")
    for k, v in lack.items():
        print("  %-10s %2d  %s" % (k, len(v), " ".join(v[:10])))
        # 무채색·루프는 공통 규칙이 붙어서 메웁니다 — 그건 흠이 아닙니다.
        if v and k in ("쓰임 없음", "모션 없음", "스타일 잠금", "프리셋 충돌"):
            bad.append("%s: %s" % (k, " ".join(v)))

    # ── ④ 초상과 신살 인물 ──────────────────────────────
    print("\n[4] 초상 20인 · 신살 인물 13")
    for kind, ko in (("chars", "초상"), ("figures", "신살 인물")):
        rows = d.get(kind, {})
        no_mood = [k for k, v in rows.items()
                   if kind == "chars" and not v.get("moods")]
        no_img = [k for k, v in rows.items() if not (v.get("image") or "").strip()]
        print("  %-8s %2d개 · 그림 없음 %d · 표정 없음 %d"
              % (ko, len(rows), len(no_img), len(no_mood)))
        if no_img:
            bad.append("%s 그림 명령어가 없소: %s" % (ko, " ".join(no_img)))
        if no_mood:
            bad.append("초상에 표정 셋이 없소: %s" % " ".join(no_mood))

    if a.why:
        print("\n[why] 장면마다")
        for sid, p in scenes.items():
            print("  %-9s %s" % (sid, (p.get("use") or "**쓰임 없음**")[:96]))

    print("\n" + "-" * 74)
    if bad:
        print("고칠 것 %d건" % len(bad))
        for b in bad:
            print("  · " + b)
        return 1
    print("[OK] 명령어가 화면에 맞소")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
