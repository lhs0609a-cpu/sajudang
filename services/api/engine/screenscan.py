"""
화면마다 손님이 **실제로 읽는 글**을 모아 연출 점수를 매긴다.

    from engine.screenscan import scan_all
    scan_all()   →  [{id, title, pull, bite, depth, plain, total, missing…}]

★ 두 군데에서 옵니다

    엔진이 짓는 글    훅 5단 · 리포트 컷 · 일진 · 분석지
                     — 사람마다 다릅니다. 표본 하나를 실제로 돌립니다.
    화면이 든 글      a1 골목 · a2 이름 · a3 날 · a4 때 · b1 진열대 …
                     — 코드에 박힌 글입니다. 그대로 읽습니다.

  두 벌을 **같은 자로** 잽니다. 안 그러면 입력 화면만 늘 붉거나
  리포트만 늘 푸릅니다.

★ 점수는 관리자 화면과 CLI 가 **같은 것**을 봅니다

  `engine/dramaturgy.py` 한 자리에서 잽니다. 도구가 따로 재면
  "도구는 통과인데 화면은 붉은" 자리가 생깁니다.

★ 못 하는 것 — 알고 씁니다

  화면 글을 **소스 순서**로 읽습니다. 리액트가 실제로 그리는 순서가
  아닙니다. 그래서 —

    · `tab === "b1"` 처럼 **표시가 없는** 화면(마지막 return 으로
      떨어지는 자리)은 앞 화면 조각에 섞입니다. b4 의 끝에 b1 의
      글이 붙는 식입니다.
    · 조건부로만 나오는 글은 늘 있는 것으로 셉니다.

  그래서 이 점수는 **어느 화면을 먼저 볼지 가리키는 값**이지
  등수가 아닙니다. 붉은 화면을 눈으로 열어 보는 것까지가 한 벌입니다.
"""
from __future__ import annotations

import re
from datetime import date
from functools import lru_cache
from pathlib import Path
from typing import Optional

from . import dramaturgy as D

WEB = Path(__file__).resolve().parents[3] / "apps" / "web"

# ══════════════════════════════════════════════════════════
# 화면 이름표 — docs/08 §1
# ══════════════════════════════════════════════════════════
KO = {
    "a1": "골목", "a2": "이름", "a5": "걸리는 것", "a3": "날·고을",
    "a4": "때", "a4b": "성향 넉 자", "a6": "글자가 서다", "a7": "훅 5단",
    "b1": "진열대", "b2": "스무 사람", "b3": "그 사람", "b4": "내 명식",
    "c1": "표지", "c2": "본문", "c3": "대운 맵", "c4": "페이월",
    "c5": "공유 카드", "c6": "남기다", "c7": "분석지", "c8": "내보내기",
    "d0": "무료 6단", "d1": "어디까지", "d2": "값을 치르다", "d3": "다 됐소",
    "f2": "인장첩", "r1": "다녀간 사람들", "g1": "오늘", "g2": "이번 주", "g3": "다과상",
    "h1": "이어지다", "s1": "받은 글", "s2": "나도 보기",
}

# 화면 종류 — 기준 분량이 다릅니다
KIND = {
    "a1": "input", "a2": "input", "a3": "input", "a4": "input",
    "a4b": "input", "a5": "input", "b1": "list", "b2": "list",
    "b3": "list", "b4": "read", "c1": "beat", "c4": "list",
    "c5": "beat", "c6": "beat", "d1": "list", "d2": "beat", "d3": "beat",
    "f2": "list", "r1": "beat", "h1": "list", "s2": "beat",
}

# 화면이 스스로 적은 액트아웃 — <ActOut kind="딜레마" next="본문">
ACT_DECL = re.compile(r'<ActOut\s[^>]*kind="([^"]+)"')
# ★ 예고도 **선언**입니다.
#
#   `next` 는 「다음 자리 — 「본문」」 으로 그려집니다. 그런데 그 글자는
#   `ActOut.tsx` 안에 있고, 화면 파일에는 `next="본문"` 이라는 **속성**
#   으로만 있습니다. 속성은 태그 안이라 글 긁는 자(JSX_TEXT)에 안 걸리고,
#   두 글자짜리 이름은 문자열 자(TSX_STR, 여섯 자 이상)에도 안 걸립니다.
#
#   그래서 열아홉 자리 중 **열일곱이 이미 이름을 부르고 있는데** 도구는
#   스물둘이 안 부른다고 적고 있었습니다. 어제 `kind` 에서 겪은 것과
#   같은 자리입니다 — 선언은 읽고, 말뭉치는 부품을 안 쓰는 자리에.
ACT_NEXT = re.compile(r'<ActOut\s[^>]*next=(?:"([^"]+)"|\{([^{}]+)\})')

# 화면이 스스로 적은 이름 — <Shell screen="a7">
SCREEN_DECL = re.compile(r'<Shell\s[^>]*screen="(\w+)"')
# 화면이 갈리는 자리 — `if (step === "a6") {`
BRANCH = re.compile(r'if \((?:step|tab) === "\w+"')

TSX_STR = re.compile(r'"([^"\\<>{}\n]{6,200})"')
# ★ 줄을 넘는 글도 잡습니다.
#
#   전에는 `[^<>{}\n]` 이라 **한 줄 안의 글만** 잡았습니다. 그런데
#   화면 글은 대개 이렇게 생겼습니다 —
#
#       <ActOut kind="딜레마">
#         스물을 다 들을 수는 없소. <b>이을 수 있는 건 둘이오.</b><br />
#         누구를 고르느냐가 곧 무엇을 볼 것인가요.
#       </ActOut>
#
#   `<b>` 와 줄바꿈에 걸려 조각조각 잘리고, 짧은 조각은 버려집니다.
#   그래서 **막 끝을 새로 써 넣었는데 점수가 안 움직였습니다.**
#   자가 글을 못 읽으면 그 자는 글이 아니라 줄바꿈을 재는 것입니다.
JSX_TEXT = re.compile(r">([^<>]{4,400})<", re.S)
# ★ 중괄호를 **버리지 말고 지웁니다.**
#
#   `{Math.max(0, n - used)}` 처럼 값이 낀 문장은 통째로 버려지고
#   있었습니다. 그런데 화면에서 가장 센 문장이 대개 그런 문장입니다 —
#   수가 박힌 문장이라서요. 값 자리를 ▮ 로 바꾸고 글은 살립니다.
BRACE = re.compile(r"\{[^{}]*\}")
# 글이 아닌 것 — 태그 사이에 낀 코드 조각
CODEY = re.compile(r"=>|className|useState|const |return |;|\)\s*\{|\bprops\b")


def _strip_code(src: str) -> str:
    src = re.sub(r"/\*.*?\*/", " ", src, flags=re.S)
    return re.sub(r"//[^\n]*", " ", src)


def _declared(chunk: str) -> list:
    """이 조각이 선언한 액트아웃 꼴."""
    out = []
    for k in ACT_DECL.findall(chunk):
        if k not in out:
            out.append(k)
    return out


def _next_named(chunk: str) -> Optional[str]:
    """이 조각이 이름으로 부른 다음 자리. 값이 낀 것(`{firstOwn?.title}`)도
    이름을 부르는 것입니다 — 무엇이 오는지 화면이 압니다."""
    for lit, expr in ACT_NEXT.findall(chunk):
        got = (lit or expr or "").strip()
        if got:
            return got
    return None


def _readable(chunk: str) -> str:
    """코드 조각에서 손님이 읽는 한국어만 긁어낸다."""
    out = []
    for m in list(TSX_STR.finditer(chunk)) + list(JSX_TEXT.finditer(chunk)):
        t = re.sub(r"\s+", " ", BRACE.sub(" ▮ ", m.group(1))).strip()
        if not re.search(r"[가-힣]", t):
            continue
        # 클래스 이름·주소·키는 글이 아닙니다
        if re.match(r"^[a-z0-9 _\-/.]+$", t) or t.startswith("/"):
            continue
        if CODEY.search(t):
            continue
        out.append(t)
    # 같은 글이 두 번 잡히면(문자열 + JSX) 한 번만 셉니다
    seen, uniq = set(), []
    for t in out:
        if t not in seen:
            seen.add(t)
            uniq.append(t)
    return " ".join(uniq)


# 화면 파일 — 손님이 도는 순서대로
PAGES = ("app/page.tsx", "app/lobby/page.tsx", "app/report/[id]/page.tsx",
         "app/pay/page.tsx", "app/me/page.tsx", "app/daily/page.tsx",
         "app/relay/page.tsx", "app/summary/page.tsx")


def _split(src: str) -> dict:
    """
    `<Shell screen="a7">` 가 선 자리부터 다음 선언까지가 한 화면.

    ★ 다만 **갈림에서부터** 셉니다.

      화면 글이 늘 Shell 안에 있지는 않습니다. a6 은 뜸에 찍을 여섯
      줄을 Shell 앞에서 `const beats = [...]` 로 짓습니다. Shell 자리만
      보고 자르면 그 여섯 줄이 **앞 화면(a5)의 글**로 붙습니다 —
      a5 가 「서머타임 구간이오」 를 제 글로 들고 있었습니다.

      그래서 덩이는 그 화면의 갈림(`if (step === "a6")`)에서 엽니다.
      갈림이 없는 화면(마지막 return)은 Shell 자리에서 엽니다.
    """
    marks = []
    branches = [m.start() for m in BRANCH.finditer(src)]
    prev = 0
    for m in SCREEN_DECL.finditer(src):
        head = [b for b in branches if prev <= b < m.start()]
        marks.append((m.group(1), head[-1] if head else m.start()))
        prev = m.end()
    if not marks:
        return {}
    marks.append(("__end__", len(src)))
    out = {}
    for i in range(len(marks) - 1):
        sid, a = marks[i]
        chunk = src[a:marks[i + 1][1]]
        got = _readable(chunk)
        # 한 화면이 여러 꼴로 나오면(못 세웠을 때 · 값을 치르는 중)
        # **가장 긴** 덩이가 그 화면입니다.
        if len(got) > len(out.get(sid, ("", [], None))[0]):
            out[sid] = (got, _declared(chunk), _next_named(chunk))
    return out


@lru_cache(maxsize=1)
def _screens() -> dict:
    """화면마다 (읽는 글 · 선언한 액트아웃 · 이름으로 부른 다음 자리)."""
    out = {}
    for rel in PAGES:
        p = WEB / rel
        if p.exists():
            out.update(_split(_strip_code(p.read_text(encoding="utf-8"))))
    # a7 은 훅 부품이 그립니다. page.tsx 만 보면 껍데기만 잡힙니다.
    part = WEB / "components" / "HookSegments.tsx"
    if part.exists() and "a7" in out:
        t, d, nx = out["a7"]
        out["a7"] = (t + " " + _readable(_strip_code(
            part.read_text(encoding="utf-8"))), d, nx)
    return out


# ══════════════════════════════════════════════════════════
# 엔진이 짓는 글 — 표본 하나를 실제로 돌린다
# ══════════════════════════════════════════════════════════
#
# ★ 한 사람만 봅니다. 사람마다 문장이 갈리지만 **구조**는 같습니다 —
#   여기서 재는 것은 구조입니다. 문장 쏠림은 dup_rate 가 봅니다.
SAMPLE = (1993, 11, 25, 15, 55, "M")


def _engine_text() -> dict:
    from .bank import build_hook
    from .calendar import build_chart
    from .daily import build_daily
    from .features import build_features
    from .report import build_report

    y, m, d, h, mi, sex = SAMPLE
    f = build_features(build_chart(y, m, d, h, mi, sex, city="서울"),
                       as_of=date.today())
    out = {}

    segs = build_hook(f, "work", "INTJ", name="", you="그대")
    out["a7"] = "".join(s["html"] for s in segs)

    free = build_report(f, "scan", "pungun", "free", "work", "INTJ")
    out["d0"] = "".join(
        '<span class="src">근거 · %s</span>%s' % (c["source"], c["html"])
        for c in free["cuts"])
    if free.get("locked"):
        out["c4"] = " ".join(
            "「%s」 %s" % (l["title"], l.get("teaser") or "")
            for l in free["locked"])

    paid = build_report(f, "scan", "pungun", "one", "work", "INTJ")
    out["c2"] = (paid.get("opening") or "") + "".join(
        '<span class="src">근거 · %s</span>%s' % (c["source"], c["html"])
        for c in paid["cuts"]) + (paid.get("closing") or "")
    mapcut = [c for c in paid["cuts"] if c["id"] == "daeun_map"]
    if mapcut:
        out["c3"] = ('<span class="src">근거 · %s</span>%s'
                     % (mapcut[0]["source"], mapcut[0]["html"]))

    # 일진은 html 을 안 냅니다 — 줄로 옵니다.
    dly = build_daily(f, on=date.today())
    out["g1"] = " ".join(filter(None, [
        dly.get("text") or "",
        " ".join(dly.get("lines") or []),
        " ".join(dly.get("notes") or []),
        dly.get("score_says") or "",
        # 「이게 무슨 말이오」 상자도 손님이 그 자리에서 읽습니다.
        dly.get("terms_html") or "",
        '<span class="src">근거 · %s</span>' % (dly.get("source") or ""),
    ]))
    return out


# ══════════════════════════════════════════════════════════
def scan_all() -> list:
    """모든 화면의 점수. 관리자 화면과 CLI 가 같이 씁니다."""
    pairs = dict(_screens())
    text = {k: v[0] for k, v in pairs.items()}
    decl = {k: v[1] for k, v in pairs.items()}
    nxt = {k: v[2] for k, v in pairs.items()}
    # 엔진 글이 있는 화면은 **엔진 글이 이깁니다** — 손님이 읽는 것은
    # 코드에 박힌 안내가 아니라 실제로 나온 해석입니다.
    eng = _engine_text()
    for sid, html in eng.items():
        text[sid] = html + " " + text.get(sid, "")

    rows = []
    for sid, html in text.items():
        if sid not in KO:
            continue
        rows.append(D.score(sid, KO[sid], html, KIND.get(sid, "read"),
                            next_named=nxt.get(sid),
                            declared=decl.get(sid)))
    order = list(KO)
    rows.sort(key=lambda r: order.index(r["id"]))
    return rows


def summary(rows: Optional[list] = None) -> dict:
    rows = rows if rows is not None else scan_all()
    if not rows:
        return {"screens": 0}
    avg = lambda k: round(sum(r[k] for r in rows) / len(rows))  # noqa: E731
    weak = sorted(rows, key=lambda r: r["total"])[:5]
    return {
        "screens": len(rows),
        "pull": avg("pull"), "bite": avg("bite"),
        "heart": avg("heart"), "clear": avg("clear"),
        "plain": avg("plain"), "figure": avg("figure"),
        "total": avg("total"),
        "weakest": [{"id": r["id"], "title": r["title"], "total": r["total"]}
                    for r in weak],
    }
