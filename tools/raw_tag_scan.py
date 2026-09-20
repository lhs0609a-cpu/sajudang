# -*- coding: utf-8 -*-
"""
꺾쇠가 글자로 보이는 자리를 찾는다.

    python tools/raw_tag_scan.py [--web https://sajudang-three.vercel.app]

★ 왜 생겼나 (2026-09-15)

  손님이 근거 줄에서 이것을 봤습니다 —

      근거 · 상관<i class="gl">(하고 싶은 말을 참지 않는 재주)</i>이 둘 …

  엔진은 어려운 말에 풀이를 달아 `<i class="gl">` 로 싸서 내려보냅니다.
  화면에는 작은 글씨로 앉게 되어 있고(`.gl`), 그러라고 만든 CSS 도
  있습니다. 그런데 화면이 그 글을 **글자로** 꽂아 꺾쇠가 그대로
  보였습니다. 근거를 대는 집에서 근거 줄이 가장 읽기 어려웠습니다.

★ 화면만 열어서는 안 보입니다

  훅·리포트·일진은 **명식이 있어야** 글이 옵니다. 그래서 명식을 하나
  세우고 세션을 심은 뒤에 봅니다. 안 심고 열면 전부 «OK» 가 나옵니다 —
  글이 아예 안 뜬 것을 «깨끗하다» 고 읽는 것입니다.
"""
from __future__ import annotations

import argparse
import json
import urllib.request

API = "https://sajudang-api.fly.dev"

ROUTES = [
    ("a6 명식", "/?step=a6"),
    ("a7 훅", "/?step=a7"),
    ("d0 무료", "/pay?step=d0"),
    ("d1 목패", "/pay?step=d1"),
    ("b4 내 명식", "/lobby?tab=b4"),
    ("c1 표지", "/report/pungun?tab=c1"),
    ("c2 본문", "/report/pungun?tab=c2"),
    ("c3 대운 맵", "/report/pungun?tab=c3"),
    ("c4 페이월", "/report/pungun?tab=c4"),
    ("g1 오늘", "/daily"),
    ("c7 분석지", "/summary"),
    ("h1 이어지다", "/relay"),
]

# 눈에 보이는 글에서 꺾쇠 꼴을 찾습니다.
FIND = r"""() => {
  const t = document.body.innerText || '';
  const out = [];
  const rx = new RegExp('<\\/?[a-zA-Z][^>\\n]{0,90}>', 'g');
  let m;
  while ((m = rx.exec(t))) out.push(m[0]);
  return Array.from(new Set(out)).slice(0, 6);
}"""


def chart_id() -> str:
    req = urllib.request.Request(
        API + "/v1/chart",
        data=json.dumps({"year": 1993, "month": 11, "day": 25, "hour": 15,
                         "minute": 55, "sex": "M", "hour_known": True,
                         "birth_city": "서울"}).encode("utf8"),
        headers={"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=40).read())["chart_id"]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--web", default="http://127.0.0.1:3031")
    a = ap.parse_args()
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("playwright 가 없소")
        return 2

    cid = chart_id()
    state = {"state": {
        "sessionId": "probe-rawtag", "name": "", "year": 1993, "month": 11,
        "day": 25, "hour": 15, "minute": 55, "hourKnown": True, "sex": "M",
        "city": "서울", "axis4": "INTJ", "concern": "money", "concernSet": True,
        "sexSet": True, "chartId": cid, "cur": "pungun", "read": [],
        "skipped": [], "seals": [], "tier": None, "paid": False, "visits": 1,
        "visitDate": "", "admin": False, "adminSet": False,
        "hookReview": None, "topicPick": None}, "version": 0}

    print("=" * 74)
    print("  꺾쇠가 글자로 보이는 자리 — %s" % a.web)
    print("=" * 74)
    bad = 0
    with sync_playwright() as pw:
        br = pw.chromium.launch()
        ctx = br.new_context(viewport={"width": 390, "height": 900}, is_mobile=True)
        pg = ctx.new_page()
        pg.goto(a.web, wait_until="domcontentloaded", timeout=40000)
        pg.evaluate("s => localStorage.setItem('sajudang-session', s)",
                    json.dumps(state, ensure_ascii=False))
        for name, path in ROUTES:
            try:
                pg.goto(a.web + path, wait_until="networkidle", timeout=45000)
                pg.wait_for_timeout(2200)
                hits = pg.evaluate(FIND)
            except Exception as e:                       # noqa: BLE001
                print("  %-11s 못 염 — %s" % (name, str(e)[:44]))
                continue
            if hits:
                bad += len(hits)
                print("  %-11s ★ %d종" % (name, len(hits)))
                for h in hits:
                    print("               %s" % h[:70])
            else:
                print("  %-11s OK" % name)
        br.close()
    print()
    print("-" * 74)
    print("  걸린 자리 %d" % bad)
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
