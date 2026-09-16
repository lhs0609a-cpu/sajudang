# -*- coding: utf-8 -*-
"""배포본이 손잡이를 실제로 내보내는가 — 밖에서 두드려 본다.

    python tools/live_safety.py [주소]

★ 왜 밖에서 또 재나

  `tests/test_safety.py` 는 엔진을 직접 불러 잽니다. 그런데 손님이
  받는 것은 **배포된 API 가 내보낸 것**입니다. 둘이 갈리는 자리가
  실제로 있었습니다 — 스키마가 어긋난 옛 기록이 남아 훅이 500 을
  내던 자리가 그랬습니다.

  자는 집이 든 표를 그대로 씁니다 (engine/heart.HOLD_*). 두 벌을
  들면 자가 위로를 아픈 말로 셉니다 — 한 번 겪은 자리요.
"""
from __future__ import annotations

import json
import re
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services" / "api"))

from engine import heart as heart_mod                # noqa: E402

API = sys.argv[1] if len(sys.argv) > 1 else "https://sajudang-api.fly.dev"
CONCERNS = ("money", "work", "love", "people", "dir", "health")
BLADE = re.compile(r'class="(?:blade|bite|stab)[" ]')
HOLD = re.compile(r'class="(?:bladerelief|hold)[" ]')
WORD = re.compile(heart_mod.HOLD_WORDS)
FORWARD = {"hope", "week", "closing_cut", "helper", "yongsin", "counter"}


def post(path: str, body: dict) -> dict:
    r = urllib.request.Request(API + path,
                               data=json.dumps(body).encode("utf8"),
                               headers={"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(r, timeout=90).read())


def held(html: str) -> bool:
    return bool(HOLD.search(html or "")
                or WORD.search(re.sub(r"<[^>]+>", " ", html or "")))


def main() -> int:
    c = post("/v1/chart", {"year": 1993, "month": 11, "day": 25, "hour": 15,
                           "minute": 55, "sex": "M", "hour_known": True,
                           "birth_city": "서울"})
    cid = c["chart_id"]
    bad = []
    print("=" * 70)
    print("  배포본이 손잡이를 내보내는가 — %s" % API)
    print("=" * 70)
    for concern in CONCERNS:
        h = post("/v1/hook", {"chart_id": cid, "concern": concern,
                              "axis4": "INTJ", "lens_id": "pungun"})
        for i, s in enumerate(h["segments"]):
            if BLADE.search(s["html"]) and not held(s["html"]):
                bad.append("훅 %d마디 (%s)" % (i + 1, concern))
        rep = post("/v1/report", {"chart_id": cid, "lens_id": "pungun",
                                  "tier": "free", "concern": concern,
                                  "axis4": "INTJ"})
        cuts = rep.get("cuts") or []
        for x in cuts:
            if x["id"] in heart_mod.HOLD_CUTS:
                continue
            if BLADE.search(x["html"]) and not held(x["html"]):
                bad.append("%s · %s" % (concern, x["id"]))
        if cuts and cuts[-1]["id"] not in FORWARD:
            bad.append("%s · 끝이 %s" % (concern, cuts[-1]["id"]))
        if not ({x["id"] for x in cuts} & heart_mod.HOLD_CUTS):
            bad.append("%s · 알아주는 자리가 없소" % concern)
        print("  %-7s 훅 %d마디 · 무료 %d컷 · 끝 %s"
              % (concern, len(h["segments"]), len(cuts),
                 cuts[-1]["id"] if cuts else "-"))
    print()
    if bad:
        print("  ★ 아프게만 하는 자리 %d:" % len(bad))
        for x in bad[:12]:
            print("     %s" % x)
        return 1
    print("  [OK] 배포본에서도 아픈 말이 혼자 다니지 않소")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
