"""
값을 치르면 실제로 무엇이 나오는가 — 한 사람을 골라 상품 넷을 그대로 뽑는다.

화면(apps/web/app/report/[id])이 서버에서 받아 그리는 것과 **같은 것**을
같은 CSS 로 그립니다. 문장을 여기서 따로 짓지 않습니다.

  무료                     값 없이 보이는 데까지
  이 자리 하나 (one)        고른 영역 하나 — 시기(대운)와 용신까지
  여덟 글자 전부 (all)       대운 맵 · 성향 대조까지
  스무 사람 종합 (omnibus)   같은 명식을 스무 사람이 각자 읽은 것

    python tools/sample_report.py [출력.html] [--birth 1993-07-14T05:20] \
                                  [--city 대전] [--sex F] [--concern love] \
                                  [--axis4 INFP] [--lens wolha]
"""
from __future__ import annotations

import argparse
import html as _html
import sys
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "services" / "api") not in sys.path:
    sys.path.insert(0, str(ROOT / "services" / "api"))

import payments                              # noqa: E402
from engine import lens as lens_mod          # noqa: E402
from engine import relay as relay_mod        # noqa: E402
from engine.calendar import build_chart      # noqa: E402
from engine.features import build_features   # noqa: E402
from engine.omnibus import build_omnibus     # noqa: E402
from engine.report import build_report       # noqa: E402

STYLES = (ROOT / "apps" / "web" / "styles" / "tokens.css",
          ROOT / "apps" / "web" / "styles" / "reference.css",
          ROOT / "apps" / "web" / "styles" / "scroll.css")

# 화면 탭. apps/web/app/report/[id]/page.tsx 의 TABS 와 같습니다.
TABS = [("c1", "표지"), ("c2", "본문 — 웹툰 뷰어"), ("c3", "대운 맵"),
        ("c4", "페이월"), ("c5", "공유 카드"), ("c6", "남기다")]

PAGE_CSS = """
.smp { max-width: 860px; margin: 0 auto; padding: 24px 18px 80px; }
.smp h1 { font-family: var(--serif); font-size: 26px; color: var(--gold);
          margin-bottom: 4px; }
.smp h2 { font-family: var(--serif); font-size: 20px; color: var(--c);
          margin: 40px 0 6px; border-top: 1px solid var(--line);
          padding-top: 22px; }
.smp h3 { font-family: var(--serif); font-size: 16px; color: var(--paper2);
          margin: 22px 0 6px; }
.meta { display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
        gap: 8px; margin: 14px 0 6px; }
.meta div { background: var(--bg2); border: 1px solid var(--line);
            border-radius: 8px; padding: 8px 10px; font-size: 12.5px;
            color: var(--paper2); }
.meta b { display: block; color: var(--paper); font-size: 14px;
          font-family: var(--serif); margin-top: 2px; }
.tabs { display: flex; flex-wrap: wrap; gap: 6px; margin: 10px 0 4px; }
.tabs span { font-size: 12px; border: 1px solid var(--line2); border-radius: 999px;
             padding: 3px 10px; color: var(--paper3); }
.tabs span.on { color: var(--bg); background: var(--c); border-color: var(--c); }
.pricetag { font-family: var(--mono); font-size: 13px; color: var(--gold); }
.warnnote { font-size: 12.5px; color: var(--paper2); line-height: 1.75;
            border-left: 2px solid var(--ember); padding: 8px 12px;
            background: rgba(201,112,122,.08); border-radius: 0 6px 6px 0;
            margin: 12px 0; }
.warnnote b { color: var(--ember); }
.mono { font-family: var(--mono); font-size: .9em; color: var(--paper3); }
.note { font-size: 12.5px; color: var(--paper3); line-height: 1.75;
        border-left: 2px solid var(--line2); padding-left: 12px; margin: 10px 0; }
.omni .ch { border: 1px solid var(--line); border-radius: 10px; padding: 12px 14px;
            margin: 10px 0; background: var(--bg2); }
.omni .ch > .who { font-family: var(--serif); font-size: 15px; color: var(--c); }
.omni .ch > .lead { font-size: 12px; color: var(--paper3); }
.fold { text-align: center; color: var(--paper3); font-size: 12.5px;
        border-top: 1px dashed var(--line2); margin-top: 18px; padding-top: 14px; }
"""


def esc(s) -> str:
    return _html.escape(str(s if s is not None else ""))


def cuts_html(rep, f=None, drop=("daeun_map",)) -> str:
    """
    c2 · 두루마리가 그리는 그대로.
    (apps/web/app/report/[id]/page.tsx 의 c2 와 같은 구조입니다)
    """
    out = ['<div class="scroll">']
    out.append('<div class="scrollhead">'
               '<p class="who">%s</p><p class="hanja">%s</p>'
               % (esc(rep["lens"]["name"]), esc(rep["lens"].get("hanja"))))
    if f is not None:
        out.append('<div class="eight">%s</div>'
                   % "".join("<span>%s</span>" % esc(p["gz"]) for p in f.pillars))
    out.append('<p class="cnt">읽는 자리 %d컷%s</p></div>'
               % (len(rep["cuts"]),
                  " · 잠긴 자리 %d컷" % len(rep["locked"]) if rep["locked"] else ""))
    if rep.get("opening"):
        out.append('<p class="saying">%s</p>' % rep["opening"])
    for c in rep["cuts"]:
        if c["id"] in drop:
            continue
        own = " own" if c["id"].startswith("lc_") else ""
        out.append('<div class="blk in%s"><div class="lab">%s</div>'
                   '<span class="src">%s</span>%s</div>'
                   % (own, esc(c["title"]), esc(c["source"]), c["html"]))
    if rep.get("closing"):
        out.append('<p class="saying close">%s</p>' % rep["closing"])
    out.append('</div>')
    return "".join(out)


def locked_html(rep) -> str:
    """c4 · 페이월. ★ 잠긴 컷은 본문이 아예 안 옵니다 — 가린 게 아닙니다."""
    if not rep["locked"]:
        return '<p class="note">잠긴 자리 없음 — 다 열려 있습니다.</p>'
    rows = "".join(
        '<div class="dz"><div class="k">%s</div>'
        '<p class="sm">근거 · %s</p>'
        '<p class="bl">가가가가 가가가가가 가가가</p>'
        '<p class="sm">%s부터 열리오</p></div>'
        % (esc(l["title"]), esc(l["source"]),
           "이 자리 하나" if l["need_tier"] == "one" else "여덟 글자 전부")
        for l in rep["locked"])
    return ('<p class="note">잠긴 컷은 <b>본문이 서버에서 내려오지 않습니다.</b> '
            '블러로 가린 게 아닙니다 — 제목과 근거만 옵니다.</p>' + rows)


def tabs_html(active: str, has_map: bool) -> str:
    out = []
    for tid, label in TABS:
        if tid == "c3" and not has_map:
            continue
        out.append('<span class="%s">%s · %s</span>'
                   % ("on" if tid == active else "", tid, esc(label)))
    return '<div class="tabs">%s</div>' % "".join(out)


def product_block(title, price, rep, f, promise=None) -> str:
    has_map = any(c["id"] == "daeun_map" for c in rep["cuts"])
    dmap = next((c for c in rep["cuts"] if c["id"] == "daeun_map"), None)
    parts = [
        '<h2>%s <span class="pricetag">%s</span></h2>' % (
            esc(title), ("%s원" % format(price, ",")) if price else "값 없음"),
        '<div class="meta">'
        '<div>읽는 자리<b>%d컷</b></div>'
        '<div>잠긴 자리<b>%d컷</b></div>'
        '<div>화면<b>%d탭</b></div>'
        '<div>글자 수<b>%s자</b></div></div>'
        % (len(rep["cuts"]), len(rep["locked"]),
           len(TABS) - (0 if has_map else 1),
           format(sum(len(c["html"]) for c in rep["cuts"]), ",")),
        tabs_html("c2", has_map),
        '<h3>c1 · 표지</h3>'
        '<div class="blk in" style="text-align:center">'
        '<p style="font-family:var(--serif);font-size:24px;color:var(--c)">%s</p>'
        '<p class="sm">%s · %s</p>'
        '<p class="sm mt">여덟 글자를 %s의 눈으로 본 것</p>'
        '<p class="sm">읽는 자리 %d컷 · 잠긴 자리 %d컷</p></div>'
        % (esc(rep["lens"]["name"]), esc(rep["lens"].get("hanja")),
           esc(rep["lens"].get("group")), esc(rep["lens"]["name"]),
           len(rep["cuts"]), len(rep["locked"])),
        '<h3>c2 · 본문 (웹툰 뷰어 — 아래로 이어집니다)</h3>',
        cuts_html(rep, f),
    ]
    if dmap:
        parts.append('<h3>c3 · 대운 맵</h3>')
        parts.append('<div class="blk in"><span class="src">근거 · %s</span>%s</div>'
                     % (esc(dmap["source"]), dmap["html"]))
    if promise:
        parts.append('<p class="warnnote">결제 화면(<span class="mono">'
                     'POST /v1/pay/tiers</span>)이 세어 내려보내는 수 — '
                     '<b>%d컷</b>. 화면은 이제 제 손으로 분량을 적지 '
                     '않습니다. 전에는 <b>%s</b> 라고 적혀 있었습니다.</p>'
                     % (len(rep["cuts"]), esc(promise)))
    parts.append('<h3>c4 · 페이월</h3>')
    parts.append(locked_html(rep))
    if rep.get("needs_input"):
        parts.append('<p class="note">이 캐릭터는 <b>%s</b> 를 더 받으면 '
                     '자기 몫의 컷을 하나 더 폅니다. 안 줘도 리포트는 나옵니다.</p>'
                     % esc(rep["needs_input"]))
    return "".join(parts)


def omnibus_block(omni) -> str:
    chs = omni.get("chapters") or []
    total = sum(len(c["html"]) for ch in chs for c in ch["cuts"])
    parts = [
        '<h2>스무 사람 종합 <span class="pricetag">여덟 글자 전부를 치른 사람만'
        '</span></h2>',
        '<div class="meta"><div>장<b>%d장</b></div>'
        '<div>컷 합<b>%d컷</b></div>'
        '<div>글자 수<b>%s자</b></div></div>'
        % (len(chs), sum(len(ch["cuts"]) for ch in chs), format(total, ",")),
    ]
    if omni.get("consensus"):
        parts.append('<div class="blk in"><div class="lab">한 목소리로 짚은 것</div>%s</div>'
                     % omni["consensus"])
    # 첫 장은 통째로 폅니다 — 목록만 보면 "이름만 스무 개" 로 보입니다.
    if chs:
        ch = chs[0]
        parts.append('<h3>첫 장을 통째로 — %s</h3>' % esc(ch["name"]))
        parts.append('<div class="scroll">')
        if ch.get("opening"):
            parts.append('<p class="saying">%s</p>' % ch["opening"])
        for c in ch["cuts"]:
            own = " own" if c["id"].startswith("lc_") else ""
            parts.append('<div class="blk in%s"><div class="lab">%s</div>'
                         '<span class="src">%s</span>%s</div>'
                         % (own, esc(c["title"]), esc(c["source"]), c["html"]))
        if ch.get("closing"):
            parts.append('<p class="saying close">%s</p>' % ch["closing"])
        parts.append('</div>')
        parts.append('<h3>나머지 열아홉 장 — 여는 말과 먼저 보는 자리</h3>')
    parts.append('<div class="omni">')
    for ch in chs[1:]:
        parts.append(
            '<div class="ch"><div class="who">%s <span class="lead">%s · '
            '먼저 보는 것: %s · %d컷</span></div>%s</div>'
            % (esc(ch["name"]), esc(ch.get("group")),
               esc(ch.get("leads_with")), len(ch["cuts"]),
               ('<p class="sm">%s</p>' % ch["opening"]) if ch.get("opening") else ""))
    parts.append('</div>')
    parts.append('<p class="note">장마다 <b>본문이 다릅니다</b> — 순서와 어조만 '
                 '바뀌는 게 아니라, 그 캐릭터가 따로 받는 입력이 있으면 컷이 '
                 '하나 더 붙습니다. 명식 컷은 앞에 한 번만 나오고 장마다 '
                 '되풀이하지 않습니다.</p>')
    return "".join(parts)


def build(args) -> str:
    dt = datetime.fromisoformat(args.birth)
    ch = build_chart(dt.year, dt.month, dt.day, dt.hour, dt.minute,
                     args.sex, True, args.city)
    f = build_features(ch, as_of=date.fromisoformat(args.today))

    # 이 사람에게 실제로 추천되는 캐릭터를 씁니다 — 임의로 고르지 않습니다.
    lens_id = args.lens
    reason = None
    if not lens_id:
        rec = relay_mod.recommend(f, read=["pungun"], skipped=[],
                                  session_relay_count=0, last_lens="pungun")
        items = rec.get("recommend") or []
        lens_id = items[0]["lens_id"] if items else relay_mod.FALLBACK_LENS
        reason = items[0]["reason"] if items else None
    info = lens_mod.public(lens_id)

    free = build_report(f, "sample", lens_id, "free", args.concern, args.axis4)
    one = build_report(f, "sample", lens_id, "one", args.concern, args.axis4)
    alls = build_report(f, "sample", lens_id, "all", args.concern, args.axis4)
    omni = build_omnibus(f, "sample", args.concern, args.axis4, "")

    c = f.correction
    head = (
        '<h1>값을 치르면 무엇이 나오는가</h1>'
        '<p class="sm">한 사람을 골라 상품 넷을 그대로 뽑은 것입니다. '
        '문장은 전부 <span class="mono">seed/bank.json</span> 과 Feature Store '
        '에서 조립됐고, 여기서 새로 지은 것은 없습니다.</p>'
        '<div class="meta">'
        '<div>생년월일시<b>%s · %s</b></div>'
        '<div>여덟 글자<b>%s</b></div>'
        '<div>일간 · 신강약<b>%s · %s (%d)</b></div>'
        '<div>가장 약한 것 · 용신<b>%s · %s</b></div>'
        '<div>주도 십신 · 흐름<b>%s · %s</b></div>'
        '<div>지금 대운<b>%s · %s</b></div>'
        '<div>고민 축<b>%s</b></div>'
        '<div>성향 넉 자<b>%s</b></div>'
        '</div>'
        '<p class="note">보정 — 표준시 %s · 서머타임 %s · 진태양시 %s %+.1f분 · '
        '%s 절입 %s 기준</p>'
        % (esc(args.birth.replace("T", " ")), esc(args.city),
           esc(" ".join(x["gz"] for x in f.pillars)),
           esc(f.day_gan), esc(f.strength), f.strength_score,
           esc(f.weak_el), esc(f.yongsin),
           esc(f.top_ten_god), esc(f.flow),
           esc(f.daeun[f.daeun_now]["gz"]), esc(f.daeun_ten_god),
           esc(args.concern), esc(args.axis4 or "적지 않음"),
           esc(c["std_label"]), "적용" if c["dst"] else "해당 없음",
           esc(c["city"]), c["lon_min"],
           esc(c["jieqi_name"]), esc(c["jieqi_at_kst"])))

    head += ('<p class="note">값은 <b>보이는 값이 그대로 청구됩니다.</b> '
             '릴레이 카드의 <b>%s %s원</b>이 곧 「이 자리 하나」 값이오. '
             '전에는 카드가 캐릭터 값을 보여 주고 결제는 티어 값(3,900원)을 '
             '물려, 스무 캐릭터의 값이 <b>한 번도 청구되지 않았습니다.</b> '
             '(payments.price_of · tests/test_lens_cuts.py 가 지킵니다)</p>'
             % (esc(info["name"]), format(info["price"], ",")))

    if reason:
        head += ('<p class="note">이 사람에게는 <b>%s</b>가 1순위로 붙었습니다 — '
                 '근거는 “%s”. 아래 셋은 그 캐릭터가 읽은 것입니다.</p>'
                 % (esc(info["name"]), esc(reason)))

    # ★ 값은 payments.price_of 가 정합니다 — 화면이 보여 준 값 그대로.
    #   「이 자리 하나」는 캐릭터 값, 「여덟 글자 전부」는 하나로 둡니다.
    body = (head
            + product_block("무료 — 값 없이 보이는 데까지", 0, free, f)
            + product_block("이 자리 하나", payments.price_of("one", lens_id), one, f)
            + product_block("여덟 글자 전부", payments.TIER_PRICE["all"], alls, f,
                            promise="평생운 18컷 · 25페이지")
            + omnibus_block(omni))

    css = "\n".join(p.read_text("utf-8") for p in STYLES if p.exists())
    # 화면과 같은 활자. apps/web/app/globals.css 의 첫 줄과 같습니다.
    font = ('<link rel="stylesheet" href="https://fonts.googleapis.com/css2?'
            'family=Gowun+Batang:wght@400;700&family=Noto+Sans+KR:'
            'wght@300;400;500;700&family=IBM+Plex+Mono:wght@400;500'
            '&display=swap">')
    return ("<title>월하선녀의 두루마리</title>\n%s\n<style>%s\n%s</style>\n"
            '<div class="smp">%s</div>' % (font, css, PAGE_CSS, body))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("out", nargs="?", default="sample_report.html")
    ap.add_argument("--birth", default="1993-07-14T05:20")
    ap.add_argument("--city", default="대전")
    ap.add_argument("--sex", default="F", choices=["F", "M"])
    ap.add_argument("--concern", default="love")
    ap.add_argument("--axis4", default="INFP")
    ap.add_argument("--lens", default=None)
    ap.add_argument("--today", default="2026-08-27")
    args = ap.parse_args()

    out = Path(args.out)
    out.write_text(build(args), encoding="utf-8")
    print("썼습니다: %s (%s자)" % (out, format(len(out.read_text('utf-8')), ",")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
