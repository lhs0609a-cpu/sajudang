"""
척추 시안 — 30컷 평면을 **한 사람의 흐름**으로 다시 놓아 본다.

★ API 에는 아직 안 붙었습니다. 같은 명식으로 지금 리포트와 나란히
  놓고 보려고 만든 도구입니다. 문장은 `seed/spine.json` 과 지금
  리포트(`build_report`)의 컷에서 가져오고, 여기서 새로 짓지 않습니다.

  흐름
    1 한 줄        척추 — 이 사람은 무엇을 하는 사람인가
    2 까닭         흐름 세 단(庚 → 癸 → 甲)과 옛 이름
    3 앞과 뒤      같은 힘의 강점 셋 · 그림자 셋
    4 보통은/그대는
    5 굽히는 자리  흐름을 굽히는 빈 자리 하나
    6 가장 위험한 착각 하나
    7 맞는 판
    8 그 캐릭터가 따로 보는 자리 (관점 컷)
    9 넉 자 · 지나온 자리 · 때 · 위로 · 희망 · 이번 주 (지금 컷)
   10 덮으며       한 줄을 다시 · 다음에 바뀌는 때
   ─ 셈 장부 ─    명식 · 없는 것 · 조후 · 신살 · 희소도 · 대운 맵 …

  사실 장부 — 한 문장은 **한 번만** 나갑니다. 뒤에서 또 나오면 지웁니다.

    python tools/spine_draft.py [out.html] --birth 1993-11-25T15:50 \
        --city 수원 --sex M --concern work --axis4 INTJ [--lens baegun]
    python tools/spine_draft.py --spread 4000     # 척추 칸 인구 분포
"""
from __future__ import annotations

import argparse
import html as _html
import re
import sys
from collections import Counter
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "services" / "api") not in sys.path:
    sys.path.insert(0, str(ROOT / "services" / "api"))

from engine import guard                                  # noqa: E402
from engine import lens as lens_mod                       # noqa: E402
from engine import relay as relay_mod                     # noqa: E402
from engine import spine as spine_mod                     # noqa: E402
from engine import voice as voice_mod                     # noqa: E402
from engine.calendar import build_chart                   # noqa: E402
from engine.features import build_features               # noqa: E402
from engine.report import _close_turn, build_report      # noqa: E402

STYLES = (ROOT / "apps" / "web" / "styles" / "tokens.css",
          ROOT / "apps" / "web" / "styles" / "reference.css",
          ROOT / "apps" / "web" / "styles" / "scroll.css")

CSS = """
.smp { max-width: 820px; margin: 0 auto; padding: 24px 18px 80px; }
.smp h1 { font-family: var(--serif); font-size: 24px; color: var(--gold); }
.smp h2 { font-family: var(--serif); font-size: 18px; color: var(--c);
          margin: 36px 0 8px; border-top: 1px solid var(--line); padding-top: 18px; }
.note { font-size: 12.5px; color: var(--paper3); line-height: 1.75;
        border-left: 2px solid var(--line2); padding-left: 12px; margin: 10px 0; }
.spine { font-family: var(--serif); font-size: 21px; line-height: 1.6;
         color: var(--paper); margin: 6px 0 10px; }
.spname { font-family: var(--serif); color: var(--gold); font-size: 14px;
          letter-spacing: .08em; }
.chain { display: flex; flex-wrap: wrap; align-items: center; gap: 8px;
         margin: 10px 0; }
.chain .st { display: flex; flex-direction: column; align-items: center;
             border: 1px solid var(--line2); border-radius: 8px; padding: 8px 12px;
             background: var(--bg2); min-width: 72px; text-align: center; }
.chain .st b { font-family: var(--serif); font-size: 20px; color: var(--c); }
.chain .st small { font-size: 11px; color: var(--paper3); line-height: 1.5; }
.chain .ar { color: var(--gold); font-size: 18px; }
.pair { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin: 8px 0; }
.pair > div { border: 1px solid var(--line); border-radius: 8px; padding: 8px 12px;
              font-size: 13.5px; line-height: 1.75; }
.pair .sh { border-color: rgba(201,112,122,.45); }
.pair .k { font-size: 11px; color: var(--paper3); display: block; }
.vs { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin: 6px 0; }
.vs > div { font-size: 13.5px; line-height: 1.7; padding: 6px 10px; }
.vs .m { color: var(--paper3); }
.probe { border: 1px dashed var(--line2); border-radius: 8px; padding: 8px 12px;
         margin: 8px 0; font-size: 13px; }
.probe span { display: inline-block; border: 1px solid var(--line2);
              border-radius: 999px; padding: 2px 10px; margin: 3px 4px 0 0; }
.probe span.hit { border-color: var(--gold); color: var(--gold); }
.ledger { opacity: .82; }
.cut { font-size: 11.5px; color: var(--paper3); font-family: var(--mono); }
@media (max-width: 560px) { .pair, .vs { grid-template-columns: 1fr; } }
"""

# 흐름 9 — 지금 컷에서 그대로 가져오는 것 (이 차례대로)
ARC_KEEP = ["concern_face", "hindsight", "concern_turn", "solace", "hope", "week"]
# 셈 장부 — 근거로 남기되 본문 뒤로
LEDGER = ["chart", "lack", "concern", "concern_scale", "concern_pattern",
          "place", "why", "daeun_now", "yongsin", "rarity", "axis",
          "sinsal", "helper", "ancestor", "daeun_map"]
# 한 줄로 척추가 대신하는 것 — 시안에서는 뺍니다
DROP = ["closing_cut"]


def esc(s) -> str:
    return _html.escape(str(s if s is not None else ""))


# ── 사실 장부 ────────────────────────────────────────────
_P = re.compile(r'(<p\b[^>]*>)(.*?)(</p>)', re.S)
_SENT = re.compile(r'.*?[.?!](?:\s*</(?:b|mark|u|span|em|i)>)*(?=\s|$)|.+$', re.S)


def _plain(s: str) -> str:
    return re.sub(r"\s+", " ", _html.unescape(re.sub(r"<[^>]+>", "", s))).strip()


class Ledger:
    """한 문장은 한 번만. 뒤에서 또 나오면 지우고 센다."""

    def __init__(self):
        self.seen: set = set()
        self.dropped: list = []

    def pass_(self, html: str, cut: str) -> str:
        def para(m):
            kept = []
            for s in _SENT.findall(m.group(2)):
                k = _plain(s)
                if not k:
                    continue
                if len(k) >= 8 and k in self.seen:
                    self.dropped.append((cut, k))
                    continue
                self.seen.add(k)
                kept.append(s.strip())
            if not kept:
                return ""
            return m.group(1) + " ".join(kept) + m.group(3)
        return _P.sub(para, html)


# ── 척추 절 ──────────────────────────────────────────────
def spine_sections(f, sp) -> list:
    """(id, 제목, 근거, html) — 하오체 한 벌 · 「그대」 한 벌."""
    out = []
    out.append(("sp_line", "한 줄", sp["source"],
                '<p class="spname">%s</p><p class="spine">%s</p>'
                % (esc(sp["name"]), sp["line"])))
    why = sp["chain_html"]
    if sp["pattern"]:
        base = sp["pattern"].split("(")[0]
        ra = "이라" if spine_mod._jo(base, "x", "") != base else "라"
        why += ('<p class="tale">옛 책은 이 길을 <b>%s</b>%s 불렀소. '
                '그대 여덟 글자에서 힘이 가장 많이 가는 길이 이것이오.</p>'
                % (sp["pattern"], ra))
    why += '<p class="tale">%s</p>' % sp["strength_line"]
    out.append(("sp_chain", "왜 그렇게 말하는가", "여덟 글자에서 힘이 흘러가는 길",
                why))
    pairs = "".join(
        '<div class="pair"><div><span class="k">강점</span>%s</div>'
        '<div class="sh"><span class="k">같은 힘의 그림자</span>%s</div></div>'
        % (a, b) for a, b in sp["pairs"])
    out.append(("sp_pairs", "같은 힘의 앞과 뒤",
                "강점과 그림자는 짝이오 — 하나를 버리면 다른 하나도 줄어드오",
                pairs))
    vs = "".join('<div class="vs"><div class="m">%s</div><div>%s</div></div>'
                 % (c["most"], c["you"]) for c in sp["contrast"])
    out.append(("sp_vs", "남들은, 그대는", "틀릴 수 있는 말이오 — 아니면 여기서 덮으시오",
                vs))
    if sp["empty_line"]:
        out.append(("sp_empty", "흐름을 굽히는 자리",
                    "%s 0 — 생의 고리를 따라가다 처음 만나는 빈 자리" % sp["empty"],
                    '<p class="tale">%s</p>' % sp["empty_line"]))
    out.append(("sp_risk", "가장 위험한 착각 하나", "그림자 셋이 한데 모이는 자리",
                '<p class="tale">%s</p>' % sp["risk"]))
    out.append(("sp_fit", "맞는 판", "흐름이 막히지 않는 자리",
                '<p class="tale">%s</p>' % sp["fit"]))
    return out


def probes_html(sp) -> str:
    rows = []
    for p in sp["probes"]:
        opts = "".join('<span class="%s">%s</span>'
                       % ("hit" if i in p["hit"] else "", esc(o))
                       for i, o in enumerate(p["opts"]))
        rows.append('<div class="probe">%s<br />%s</div>' % (p["q"], opts))
    return "".join(rows)


def block(cid, title, src, body, cls="") -> str:
    return ('<div class="blk in%s"><div class="lab">%s <span class="cut">%s</span></div>'
            '<span class="src">%s</span>%s</div>'
            % (cls, esc(title), esc(cid), esc(src), body))


def build(args) -> tuple[str, str, dict]:
    dt = datetime.fromisoformat(args.birth)
    ch = build_chart(dt.year, dt.month, dt.day, dt.hour, dt.minute,
                     args.sex, True, args.city)
    f = build_features(ch, as_of=date.fromisoformat(args.today))

    lens_id = args.lens
    if not lens_id:
        rec = relay_mod.recommend(f, read=["pungun"], skipped=[],
                                  session_relay_count=0, last_lens="pungun")
        items = rec.get("recommend") or []
        lens_id = items[0]["lens_id"] if items else relay_mod.FALLBACK_LENS
    view = lens_mod.view(lens_id)
    tone = view.get("voice")
    you = lens_mod.you_of(lens_id, "", f.sex)

    def say(h: str) -> str:
        return guard.enforce(voice_mod.speak(voice_mod.address(h, you), tone),
                             {"cut": "spine"})

    rep = build_report(f, "draft", lens_id, "one", args.concern, args.axis4)
    cuts = {c["id"]: c for c in rep["cuts"]}
    sp = spine_mod.read(f)
    led = Ledger()
    before_chars = sum(len(_plain(c["html"])) for c in rep["cuts"])

    arc, ledger_html, text = [], [], []

    def put(cid, title, src, body, dest, cls=""):
        body = led.pass_(body, cid)
        if not _plain(body):
            return
        dest.append(block(cid, title, src, body, cls))
        text.append("■ %s  [%s]\n%s\n" % (title, cid, _plain(re.sub(
            r"</(p|div)>", "\n", body.replace("<br />", "\n")))))

    for cid, title, src, body in spine_sections(f, sp):
        put(cid, title, say(src), say(body), arc)
    # 8 — 그 캐릭터가 따로 보는 자리
    for c in rep["cuts"]:
        if c["id"].startswith("lc_"):
            put(c["id"], "%s의 눈 · %s" % (rep["lens"]["name"], c["title"]),
                c["source"], c["html"], arc)
    # 9 — 지금 컷에서 흐름에 맞는 것
    for cid in ARC_KEEP:
        c = cuts.get(cid)
        if c:
            put(cid, c["title"], c["source"], c["html"], arc)
    # 10 — 덮으며
    closing = say('<p class="tale">오늘 본 것을 한 줄로 접으면 이것이오 — %s</p>'
                  % sp["line"]) + _close_turn(f)
    put("sp_close", "덮으며", say(sp["source"]), closing, arc)
    # 셈 장부
    text.append("\n──────── 셈 장부 ────────\n")
    placed = {c for c in ARC_KEEP} | set(DROP)
    for cid in LEDGER + [c["id"] for c in rep["cuts"]]:
        if cid in placed or cid.startswith("lc_") or cid not in cuts:
            continue
        placed.add(cid)
        c = cuts[cid]
        put(cid, c["title"], c["source"], c["html"], ledger_html, " ledger")

    after_chars = sum(len(_plain(b)) for b in arc + ledger_html)
    arc_chars = sum(len(_plain(b)) for b in arc)
    stats = {
        "lens": rep["lens"]["name"], "spine": sp["key"], "name": sp["name"],
        "cuts_before": len(rep["cuts"]), "chars_before": before_chars,
        "chars_after": after_chars, "arc_chars": arc_chars,
        "dropped": len(led.dropped),
    }

    head = (
        '<h1>척추 시안 — %s</h1>'
        '<p class="note">%s · %s · %s · 고민 %s · 넉 자 %s · 캐릭터 %s<br />'
        '여덟 글자 <b>%s</b> · 척추 <b>%s</b><br />'
        '지금 리포트 %d컷 %s자 → 시안 본문 %s자 + 셈 장부 · '
        '<b>되풀이 문장 %d개를 지웠소</b> (사실 장부)</p>'
        '<p class="note">★ 시안입니다. API 에는 안 붙었습니다. 척추 표'
        '(seed/spine.json)는 사람 검수 전 초안입니다.</p>'
        % (esc(sp["name"]),
           esc(args.birth.replace("T", " ")), esc(args.city), esc(args.sex),
           esc(args.concern), esc(args.axis4 or "—"), esc(rep["lens"]["name"]),
           esc(" ".join(p["gz"] for p in f.pillars)), esc(sp["key"]),
           len(rep["cuts"]), format(before_chars, ","), format(arc_chars, ","),
           len(led.dropped)))
    probe_part = ('<h2>3단계에서 붙을 것 — 척추가 맞는지 묻는 문항</h2>'
                  '<p class="note">답이 오면 「그대의 답에서 보인 것」 절이 '
                  '척추 뒤에 섭니다. 금빛 테두리는 척추가 맞으면 고를 쪽.</p>'
                  + say(probes_html(sp)))
    dropped = "".join("<li><span class=\"cut\">%s</span> %s</li>" % (esc(c), esc(s))
                      for c, s in led.dropped)
    body = (head + '<h2>본문 — 한 사람의 흐름</h2><div class="scroll">'
            + "".join(arc) + '</div>' + probe_part
            + '<h2>셈 장부 — 근거</h2><div class="scroll">'
            + "".join(ledger_html) + '</div>'
            + '<h2>사실 장부가 지운 문장 %d개</h2><ul class="note">%s</ul>'
            % (len(led.dropped), dropped))
    css = "\n".join(p.read_text("utf-8") for p in STYLES if p.exists())
    font = ('<link rel="stylesheet" href="https://fonts.googleapis.com/css2?'
            'family=Gowun+Batang:wght@400;700&family=Noto+Sans+KR:'
            'wght@300;400;500;700&family=IBM+Plex+Mono:wght@400;500'
            '&display=swap">')
    page = ('<title>척추 시안</title>\n%s\n<style>%s\n%s</style>\n'
            '<div class="smp">%s</div>' % (font, css, CSS, body))
    return page, "\n".join(text), stats


def spread(n: int) -> None:
    """척추 칸이 인구에서 어떻게 갈리는가. ★ 최다 점유를 보세요."""
    sys.path.insert(0, str(ROOT / "tools"))
    import population
    keys, full = Counter(), Counter()
    for f in population.sample(n):
        k = spine_mod.key(f)
        keys[k] += 1
        full[(k, spine_mod.empty_group(f), f.strength)] += 1
    print(population.banner(n))
    print("척추 열 칸 (흐름>닿는 자리)")
    for k, v in keys.most_common():
        print("  %-8s %5.1f%%" % (k, 100 * v / n))
    top = full.most_common(1)[0]
    print("척추 × 굽히는 자리 × 강약 — %d갈래 · 최다 점유 %.2f%% %s"
          % (len(full), 100 * top[1] / n, top[0]))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("out", nargs="?", default="spine_draft.html")
    ap.add_argument("--birth", default="1993-11-25T15:50")
    ap.add_argument("--city", default="수원")
    ap.add_argument("--sex", default="M", choices=["F", "M"])
    ap.add_argument("--concern", default="work")
    ap.add_argument("--axis4", default="INTJ")
    ap.add_argument("--lens", default=None)
    ap.add_argument("--today", default=date.today().isoformat())
    ap.add_argument("--spread", type=int, default=0)
    args = ap.parse_args()
    if args.spread:
        spread(args.spread)
        return 0
    page, text, st = build(args)
    out = Path(args.out)
    out.write_text(page, encoding="utf-8")
    out.with_suffix(".txt").write_text(text, encoding="utf-8")
    print("썼습니다: %s · %s" % (out, out.with_suffix(".txt")))
    print("척추 %s 「%s」 · 캐릭터 %s" % (st["spine"], st["name"], st["lens"]))
    print("지금 %d컷 %s자 → 시안 본문 %s자 (셈 장부 포함 %s자) · 되풀이 %d문장 지움"
          % (st["cuts_before"], format(st["chars_before"], ","),
             format(st["arc_chars"], ","), format(st["chars_after"], ","),
             st["dropped"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
