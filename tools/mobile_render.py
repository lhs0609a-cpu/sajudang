# -*- coding: utf-8 -*-
"""
폰에서 **실제로 그려 보고** 잰다.

    python tools/mobile_render.py [--web http://127.0.0.1:3031] [--shot out/폴더]

★ 왜 또 만드나

  `tools/mobile_audit.py` 는 CSS 규칙을 읽어서 잽니다. 그래서 「못 박은
  폭」 「44px 아래 단추」 처럼 **글자로 적힌 것**만 봅니다. 그 도구는
  머리말에 스스로 적어 두었습니다 — 글자 크기와 여백은 «눈으로 볼 것»
  이라 안 잰다고요.

  그런데 눈으로 볼 것도 **수로 나오는 것**이 있습니다. 줄이 몇 개로
  끊기는지, 손가락이 닿는 자리가 실제로 몇 px 인지, 화면 밖으로
  삐져나온 것이 있는지는 그려 봐야 압니다. 여기서는 진짜 브라우저로
  그려 놓고 잽니다.

★ 무엇을 재는가 — 세 폭에서

    가로 넘침    문서가 화면보다 넓은가 (좌우 스크롤이 생기는가)
    삐져나온 것   화면 오른쪽 끝을 넘는 칸이 있는가 (무엇인지까지)
    손가락       누를 수 있는 것이 44×44 아래인가
    글자 크기     12px 아래로 그려진 글이 있는가
    스크롤 길이   이 화면을 다 보려면 몇 번 쓸어 올려야 하는가
    겹침         고정된 것이 글을 덮는가

  ★ 폭 셋 — 320(작은 폰) · 360(갤럭시 S) · 390(아이폰).
    320 에서 안 깨지면 나머지는 대개 됩니다.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# 손님이 실제로 지나는 자리. 관리자는 뺍니다.
ROUTES = [
    ("a1 골목", "/?step=a1"),
    ("a5 걸리는 것", "/?step=a5"),
    ("a3 날·고을", "/?step=a3"),
    ("a4 때", "/?step=a4"),
    ("a4b 성향", "/?step=a4b"),
    ("a2 이름", "/?step=a2"),
    ("b1 진열대", "/lobby?tab=b1"),
    ("b2 스무 사람", "/lobby?tab=b2"),
    ("b4 내 명식", "/lobby?tab=b4"),
    ("d1 어디까지", "/pay?step=d1"),
    ("g1 오늘", "/daily"),
    ("f2 인장첩", "/me"),
    ("h1 이어지다", "/relay"),
    ("c7 분석지", "/summary"),
    ("legal 고지", "/legal"),
]

WIDTHS = [(320, "작은 폰"), (360, "갤럭시 S"), (390, "아이폰")]

# 화면에 그려진 것을 세는 자리. 브라우저 안에서 도는 글입니다.
PROBE = r"""() => {
  const W = document.documentElement.clientWidth;
  const out = {w: W, docW: document.documentElement.scrollWidth,
               docH: document.documentElement.scrollHeight,
               over: [], small: [], tiny: [], fixed: []};
  const seen = (el) => {
    const s = getComputedStyle(el);
    if (s.display === 'none' || s.visibility === 'hidden' || s.opacity === '0') return false;
    const r = el.getBoundingClientRect();
    return r.width > 0 && r.height > 0;
  };
  const name = (el) => {
    const id = el.id ? '#' + el.id : '';
    const cl = (el.className && typeof el.className === 'string')
      ? '.' + el.className.trim().split(/\s+/).slice(0, 2).join('.') : '';
    const t = (el.textContent || '').trim().slice(0, 24);
    return el.tagName.toLowerCase() + id + cl + (t ? ' 「' + t + '」' : '');
  };
  for (const el of document.querySelectorAll('body *')) {
    if (!seen(el)) continue;
    const r = el.getBoundingClientRect();
    // ① 화면 오른쪽을 넘는가 (2px 는 반올림 몫으로 봐 줍니다)
    if (r.right > W + 2 && el.children.length === 0) out.over.push({el: name(el), right: Math.round(r.right)});
    // ② 누르는 것이 44 아래인가
    const tag = el.tagName;
    const role = el.getAttribute('role');
    const press = tag === 'BUTTON' || tag === 'A' || tag === 'SELECT' || tag === 'INPUT'
                  || tag === 'SUMMARY' || role === 'button';
    if (press && (r.width < 44 || r.height < 44))
      out.small.push({el: name(el), w: Math.round(r.width), h: Math.round(r.height)});
    // ③ 12px 아래로 그려진 글
    const s = getComputedStyle(el);
    const fs = parseFloat(s.fontSize);
    if (el.children.length === 0 && (el.textContent || '').trim() && fs && fs < 12)
      out.tiny.push({el: name(el), px: fs});
    // ④ 고정된 것이 얼마나 덮는가
    if (s.position === 'fixed' && r.height > 0)
      out.fixed.push({el: name(el), h: Math.round(r.height), w: Math.round(r.width)});
  }
  const dedup = (a) => { const m = new Map(); for (const x of a) if (!m.has(x.el)) m.set(x.el, x); return [...m.values()]; };
  out.over = dedup(out.over).slice(0, 6);
  out.small = dedup(out.small).slice(0, 6);
  out.tiny = dedup(out.tiny).slice(0, 6);
  out.fixed = dedup(out.fixed).slice(0, 4);
  return out;
}"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--web", default="http://127.0.0.1:3031")
    ap.add_argument("--shot", default="")
    ap.add_argument("--width", type=int, default=0, help="한 폭만 볼 때")
    a = ap.parse_args()

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("playwright 가 없소:  pip install playwright && playwright install chromium")
        return 2

    widths = [(a.width, "고른 폭")] if a.width else WIDTHS
    shot = Path(a.shot) if a.shot else None
    if shot:
        shot.mkdir(parents=True, exist_ok=True)

    bad = 0
    print("=" * 78)
    print("  폰에서 그려 보고 재기 — %s" % a.web)
    print("=" * 78)
    with sync_playwright() as pw:
        br = pw.chromium.launch()
        for W, wname in widths:
            ctx = br.new_context(viewport={"width": W, "height": 780},
                                 device_scale_factor=2, is_mobile=True,
                                 has_touch=True)
            pg = ctx.new_page()
            print()
            print("── %dpx · %s " % (W, wname) + "─" * 46)
            print("  %-14s %5s %6s %6s %5s %5s %5s"
                  % ("화면", "넘침", "삐짐", "쓸기", "작은", "잔글", "고정"))
            for label, path in ROUTES:
                try:
                    pg.goto(a.web + path, wait_until="networkidle", timeout=25000)
                    pg.wait_for_timeout(350)
                    r = pg.evaluate(PROBE)
                except Exception as e:                       # noqa: BLE001
                    print("  %-14s  못 염 — %s" % (label, str(e)[:40]))
                    continue
                spill = r["docW"] - r["w"]
                swipes = r["docH"] / 780.0
                flags = (1 if spill > 2 else 0) + len(r["over"]) + len(r["small"]) + len(r["tiny"])
                bad += flags
                print("  %-14s %5s %6d %6.1f %5d %5d %5d"
                      % (label, "예" if spill > 2 else "-", len(r["over"]),
                         swipes, len(r["small"]), len(r["tiny"]), len(r["fixed"])))
                for k, ko in (("over", "삐짐"), ("small", "작은 단추"), ("tiny", "잔글")):
                    for x in r[k][:3]:
                        extra = ("%dpx" % x["right"]) if k == "over" else (
                            "%d×%d" % (x["w"], x["h"]) if k == "small" else "%.1fpx" % x["px"])
                        print("       · %s %s — %s" % (ko, extra, x["el"][:58]))
                if shot:
                    pg.screenshot(path=str(shot / ("%dpx-%s.png" % (W, label.split()[0]))),
                                  full_page=True)
            ctx.close()
        br.close()
    print()
    print("-" * 78)
    print("  걸린 자리 %d" % bad)
    print("  넘침·삐짐·작은 단추·잔글이 0 이면 폰에서 깨지는 데가 없소.")
    print("  쓸기는 그 화면을 다 보는 데 몇 번 쓸어 올려야 하는가요 (780px 기준).")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
