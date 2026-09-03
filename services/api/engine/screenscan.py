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

# ★ 호명도 **선언**입니다.
#
#   화면에 박은 대사가 손님을 부를 때 「그대」 라고 적어 두면, 자네라
#   부르는 훈장도 손님이라 부르는 행수도 전부 「그대」 라고 말합니다.
#   스무 명 중 「그대」 를 쓰는 사람은 셋뿐이라, 그건 열일곱 자리에서
#   틀린 말입니다 (`lenses.youOf` · `engine/lens.you_of`).
#
#   그래서 캐릭터가 말하는 자리는 `{you}` 로 씁니다. 그런데 그건
#   **값**이라 글 긁는 자가 ▮ 로 지웁니다 — 제대로 고친 화면이
#   「누구한테 하는 말인지 없소」 로 내려앉았습니다.
#
#   `next` · `kind` 에서 겪은 것과 같은 자리입니다. 선언은 읽습니다.
ADDRESSED = re.compile(r"\{\s*you\s*\}|youOf\s*\(")

# 엔진 글이 화면 **가운데**에 놓이는 자리. 나머지는 맨 위입니다.
#
#   c4  접힌 컷 목록 — 나레이션과 대사 아래에 놓입니다
#   a7  훅 다섯 마디 — 위에 여는 줄(「도령이 종이에서 눈을 뗐다」)과
#       무슨 일이 벌어질지 적은 안내가 있고, 아래에 마감과 버튼이
#       있습니다. 엔진 글을 맨 앞에 붙이면 그 여는 줄이 안 보여
#       「첫 줄이 설명이오」 가 나옵니다.
#   c2 · c3 · d0 · g1 도 같습니다. 엔진이 짓는 컷은 화면 **가운데**에
#       놓이고, 위에는 여는 줄과 뜸이, 아래에는 마감과 버튼이 있습니다.
#       맨 앞에 붙이면 네 화면이 다 「첫 줄이 설명이오」 로 내려앉습니다.
#
# ★ 사실상 엔진 글이 오는 화면은 **전부** 가운데입니다. 그래도 목록으로
#   적어 둡니다 — 새 화면이 생겼을 때 어느 쪽인지 사람이 정하게 합니다.
ENGINE_MID = {"c4", "a7", "c2", "c3", "d0", "g1"}
# 그 화면에서 **끝으로 남겨 두는** 줄 수 (액트아웃 + 버튼).
TAIL_KEEP = 3

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
    # ★ 조각 사이는 **줄바꿈**으로 잇습니다.
    #
    #   여기서 나오는 조각 하나하나가 화면에서는 따로 앉는 덩이입니다
    #   (문단 · 나레이션 한 줄 · 버튼). 빈칸으로 이으면 줄길이·읽기속도
    #   축이 화면 하나를 **한 문단**으로 보고, 어느 화면이나 「벽으로
    #   읽히오」 가 됩니다. 글자를 세는 자리(plain)는 공백을 고르므로
    #   앞의 여섯 축은 그대로입니다.
    return "\n".join(uniq)


# 화면 파일 — 손님이 도는 순서대로
PAGES = ("app/page.tsx", "app/lobby/page.tsx", "app/report/[id]/page.tsx",
         "app/pay/page.tsx", "app/me/page.tsx", "app/daily/page.tsx",
         "app/relay/page.tsx", "app/summary/page.tsx",
         # ★ 공유로 건너오는 자리(s1). 이 파일이 빠져 있어서 **이 집을
         #   처음 보는 사람이 서는 화면**이 점수 밖에 있었습니다.
         #   글은 page.tsx 가 아니라 SharedView.tsx 가 들고 있습니다.
         "app/s/[token]/SharedView.tsx")


# ★ 찍어 둔 화면 글 — 배포본에서도 점수를 내기 위해 (2026-09-03)
#
#   배포 이미지에는 `seed/` 와 `services/api/` 만 들어갑니다. 화면 글은
#   `apps/web` 에 있으니 fly 에서는 스물일곱 중 여섯만 잡혀서, 관리자
#   화면이 「이 서버에서는 못 재오」 라고 적고 끝났습니다. 손님이
#   「관리자 페이지에서 각 페이지별로 점수 다 볼 수 있어야 한다」 고
#   했습니다.
#
#   그래서 소스에서 **읽어 낸 글**(화면마다 글 · 액트아웃 선언 · 다음
#   자리 · 호명)을 `seed/screen_text.json` 에 찍어 둡니다. seed 는
#   이미지에 들어가니 배포본이 그걸 읽습니다. 소스가 있으면 소스가
#   이깁니다 — 찍어 둔 것은 소스가 없을 때만 씁니다.
#
#   ★ 찍어 둔 것은 **낡습니다.** 그래서 찍은 때와 소스의 지문을 같이
#     적고, 관리자 화면은 「찍어 둔 글로 잰 것」 이라고 말합니다.
#     tests/test_screen_snapshot.py 가 소스와 어긋나면 잡습니다 —
#     `.\dev.ps1 drama` 가 돌 때마다 다시 찍습니다.
SNAP = Path(__file__).resolve().parents[3] / "seed" / "screen_text.json"


def _source_files() -> list:
    """글을 읽는 소스 파일 전부 — 지문은 이걸로 냅니다."""
    out = [WEB / rel for rel in PAGES]
    out.append(WEB / "components" / "HookSegments.tsx")
    return [p for p in out if p.exists()]


def source_fingerprint() -> str:
    """
    글이 바뀌었는가.

    ★ 줄끝은 안 셉니다.

      전에는 파일 바이트를 그대로 넣었습니다. 그런데 이 저장소는
      LF 로 적히고 윈도우에서 새로 받으면 git 이 CRLF 로 풀어 놓습니다.
      그러면 **글이 한 자도 안 바뀌었는데** 지문이 달라져서, 새로 받은
      사본에서는 「찍어 둔 글이 낡았소」 가 늘 뜹니다.

      늑대가 안 왔는데 늑대라고 외치는 자는 곧 아무도 안 믿습니다.
      줄끝을 고르고 셉니다.
    """
    import hashlib
    h = hashlib.sha1()
    for p in _source_files():
        h.update(p.read_bytes().replace(b"\r\n", b"\n"))
    return h.hexdigest()[:12]


def _from_source() -> dict:
    out = {}
    for rel in PAGES:
        p = WEB / rel
        if p.exists():
            out.update(_split(_strip_code(p.read_text(encoding="utf-8"))))
    # a7 은 훅 부품이 그립니다. page.tsx 만 보면 껍데기만 잡힙니다.
    part = WEB / "components" / "HookSegments.tsx"
    if part.exists() and "a7" in out:
        t, d, nx, ad, fd = out["a7"]
        out["a7"] = (t + " " + _readable(_strip_code(
            part.read_text(encoding="utf-8"))), d, nx, ad, fd)
    return out


def write_snapshot() -> dict:
    """소스에서 읽은 글을 seed 에 찍는다. 소스가 없으면 아무것도 안 한다."""
    if not WEB.exists():
        return {}
    from datetime import datetime
    import json
    body = {
        "_at": datetime.now().isoformat(timespec="seconds"),
        "_fingerprint": source_fingerprint(),
        "screens": {sid: list(v) for sid, v in _from_source().items()},
    }
    SNAP.write_text(json.dumps(body, ensure_ascii=False, indent=1) + chr(10),
                    encoding="utf-8")
    return body


def _read_snapshot() -> Optional[dict]:
    if not SNAP.exists():
        return None
    import json
    try:
        return json.loads(SNAP.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def source_mode() -> str:
    """source · snapshot · none — 어느 글로 재는가."""
    if WEB.exists():
        return "source"
    return "snapshot" if _read_snapshot() else "none"


def snapshot_at() -> Optional[str]:
    """찍어 둔 글의 때. 소스로 잴 때는 None."""
    if WEB.exists():
        return None
    snap = _read_snapshot()
    return snap.get("_at") if snap else None


def has_source() -> bool:
    """
    화면 소스를 읽을 수 있는가 — 찍어 둔 글이 있어도 참입니다.

    ★ 이 자는 **소스 파일을 읽어서** 셉니다 — 화면 글이 코드에 박혀
      있기 때문입니다. 그런데 배포 이미지(Dockerfile)에는  와
       만 들어갑니다.  이 없습니다.

      그러니 배포본에서 이걸 부르면 **엔진이 짓는 글 몇 개만** 재고
      화면 글은 통째로 빠집니다. 스물일곱 화면이 여섯쯤으로 줄고
      숫자는 그럴듯하게 나옵니다 — 그게 제일 나쁩니다.

      틀린 숫자를 내느니 **못 잰다고 말합니다.** 연출 점수는 글을
      고치는 자리에서 쓰는 자입니다.
    """
    return WEB.exists() or _read_snapshot() is not None


# 모듈 자리에 놓인 글 덩이 — `const PROMISE = "…"` · `const OPENING = {…}`
#
# ★ 화면 글이 늘 화면 안에 있지는 않습니다.
#
#   대문(a1)은 약속 세 줄을 `PROMISE` 로, 계절 나레이션을 `OPENING` 으로
#   **파일 맨 위에** 두고 씁니다. 덩이는 화면의 갈림에서 열리므로 그
#   위에 있는 것은 어느 화면에도 안 붙습니다 — 그래서 대문이 **80자**로
#   잡혔습니다. 실제로 손님이 읽는 것은 그 네 배입니다.
#
#   덩이가 그 이름을 **부르면** 그 글은 그 화면의 글입니다. 이름을
#   안 부르는 화면에는 안 붙입니다. (`kind` · `next` · `{you}` 와 같은 결)
TOPCONST = re.compile(
    r"^const ([A-Z][A-Z0-9_]*)\s*(?::[^=\n]+)?=\s*(.*?)(?=^\S|\Z)",
    re.M | re.S)


def _top_copy(src: str) -> dict:
    """모듈 자리 상수마다 (이름 → 읽는 글)."""
    out = {}
    for m in TOPCONST.finditer(src):
        got = _readable(m.group(2))
        if got:
            out[m.group(1)] = got
    return out


# 접어 둔 말 — <Fold>…</Fold>
#
# ★ 화면에 있기는 한데 **기본으로는 안 읽힙니다** (2026-09-03).
#
#   적는 자리에 글이 너무 많아 손님이 읽다 지쳤습니다. 지우면 그 안의
#   팩폭·울림까지 사라지므로 **접었습니다**(components/Fold.tsx).
#   그러면 자도 같이 갈라 세야 합니다 —
#
#       분량(pace)   접힌 글은 **빼고** 셉니다. 아무도 안 펴니까요.
#       그 밖의 축   그대로 셉니다. 편 사람은 읽으니까요.
#
#   안 가르면 접어도 점수가 그대로라, 접을 이유가 없어집니다.
FOLD = re.compile(r"<Fold\b.*?</Fold>", re.S)


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
    top = _top_copy(src)
    out = {}
    for i in range(len(marks) - 1):
        sid, a = marks[i]
        chunk = src[a:marks[i + 1][1]]
        got = _readable(chunk)
        # 이 덩이가 이름을 부른 모듈 상수의 글을 함께 셉니다.
        #
        # ★ **부른 자리**를 봅니다. 늘 끝에 붙이면 콜드 오픈을 놓칩니다 —
        #   대문은 계절 나레이션(`OPENING`)으로 여는데, 그걸 뒤에 붙이면
        #   첫 줄이 액트아웃이 되어 「첫 줄이 설명이오」 가 나옵니다.
        #   손님이 보는 순서와 자가 읽는 순서가 같아야 합니다.
        head, tail = [], []
        for nm, txt in top.items():
            m = re.search(r"\b%s\b" % re.escape(nm), chunk)
            if not m:
                continue
            (head if m.start() < len(chunk) * 0.3 else tail).append(txt)
        got = " ".join([x for x in head] + [got] + [x for x in tail])
        # 한 화면이 여러 꼴로 나오면(못 세웠을 때 · 값을 치르는 중)
        # **가장 긴** 덩이가 그 화면입니다.
        if len(got) > len(out.get(sid, ("", [], None, False, 0))[0]):
            # 접힌 글이 몇 자인가 — 분량 축에서만 뺍니다.
            fold = sum(len(_readable(m.group(0)))
                       for m in FOLD.finditer(chunk))
            out[sid] = (got, _declared(chunk), _next_named(chunk),
                        bool(ADDRESSED.search(chunk)), fold)
    return out


@lru_cache(maxsize=1)
def _screens() -> dict:
    """화면마다 (읽는 글 · 선언한 액트아웃 · 이름으로 부른 다음 자리)."""
    if WEB.exists():
        return _from_source()
    snap = _read_snapshot()
    if not snap:
        return {}
    return {sid: tuple(v) for sid, v in snap.get("screens", {}).items()}


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
    # ★ 따로 서는 것은 **따로 잇습니다** (줄바꿈으로).
    #
    #   화면에서 근거 딱지는 컷 위에 따로 앉고, 접힌 컷들은 각각
    #   제 상자에 앉습니다. 그걸 빈칸으로 이어 붙이면 줄길이·읽기속도
    #   축이 한 덩이로 보고 「안 끊고 83초를 이어 가오」 라 합니다 —
    #   실제로는 여섯 상자에 나뉘어 있는데요.
    NL = chr(10)
    out["d0"] = NL.join(
        '<span class="src">근거 · %s</span>%s%s'
        % (c["source"], NL, c["html"])
        for c in free["cuts"])
    if free.get("locked"):
        out["c4"] = NL.join(
            "「%s」%s%s" % (l["title"], NL, l.get("teaser") or "")
            for l in free["locked"])

    paid = build_report(f, "scan", "pungun", "one", "work", "INTJ")
    out["c2"] = ((paid.get("opening") or "") + NL + NL.join(
        '<span class="src">근거 · %s</span>%s%s'
        % (c["source"], NL, c["html"])
        for c in paid["cuts"]) + NL + (paid.get("closing") or ""))
    mapcut = [c for c in paid["cuts"] if c["id"] == "daeun_map"]
    if mapcut:
        out["c3"] = ('<span class="src">근거 · %s</span>%s%s'
                     % (mapcut[0]["source"], NL, mapcut[0]["html"]))

    # 일진은 html 을 안 냅니다 — 줄로 옵니다.
    dly = build_daily(f, on=date.today())
    out["g1"] = NL.join(filter(None, [
        dly.get("text") or "",
        NL.join(dly.get("lines") or []),
        NL.join(dly.get("notes") or []),
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
    addr = {k: v[3] for k, v in pairs.items()}
    # 접힌 글 — 찍어 둔 옛 글에는 이 칸이 없으니 0 으로 받습니다.
    fold = {k: (v[4] if len(v) > 4 else 0) for k, v in pairs.items()}
    # 엔진 글이 있는 화면은 **엔진 글이 이깁니다** — 손님이 읽는 것은
    # 코드에 박힌 안내가 아니라 실제로 나온 해석입니다.
    #
    # ★ 다만 **놓이는 자리**가 화면마다 다릅니다.
    #
    #   a7 · c2 · c3 · d0 · g1 은 엔진 글이 곧 본문이라 맨 위에 옵니다.
    #   c4 는 아닙니다 — 거기서 엔진이 주는 것은 **접힌 컷 목록**이고,
    #   화면에서는 나레이션과 대사 **아래**에 놓입니다. 그런데 자는
    #   그걸 맨 앞에 붙여 놓고 「첫 줄이 설명이오」 라 적었습니다.
    #   손님이 보는 첫 줄은 「두루마리가 반쯤 접혀 있다」 입니다.
    #
    #   콜드 오픈은 **첫 두 줄**만 봅니다. 순서를 틀리면 그 자리가
    #   통째로 헛됩니다.
    eng = _engine_text()
    for sid, html in eng.items():
        if sid in ENGINE_MID:
            # 화면 글의 **앞은 앞에, 끝은 끝에** 두고 그 사이에 넣습니다.
            # 콜드 오픈은 첫 두 줄을, 버튼은 마지막 한 줄을 봅니다 —
            # 둘 다 화면 글이라야 실제로 보이는 것과 같아집니다.
            # ★ 이을 때도 **줄바꿈으로** 잇습니다. 빈칸으로 이으면
            #   화면 글이 도로 한 덩이가 되어, 줄길이·읽기속도 축이
            #   없는 벽을 봅니다 (_readable 과 같은 까닭).
            nl = chr(10)
            ls = D._lines(text.get(sid, ""))
            head = nl.join(ls[:-TAIL_KEEP]) if len(ls) > TAIL_KEEP else ""
            tail = nl.join(ls[-TAIL_KEEP:]) if ls else ""
            text[sid] = nl.join(x for x in (head, html, tail) if x)
        else:
            text[sid] = html + chr(10) + text.get(sid, "")

    rows = []
    for sid, html in text.items():
        if sid not in KO:
            continue
        rows.append(D.score(sid, KO[sid], html, KIND.get(sid, "read"),
                            next_named=nxt.get(sid),
                            declared=decl.get(sid),
                            addressed=bool(addr.get(sid)),
                            folded=fold.get(sid, 0)))
    order = list(KO)
    rows.sort(key=lambda r: order.index(r["id"]))
    return rows


def summary(rows: Optional[list] = None) -> dict:
    rows = rows if rows is not None else scan_all()
    if not rows:
        return {"screens": 0, "has_source": has_source(),
                "source": source_mode(), "snapshot_at": snapshot_at()}
    avg = lambda k: round(sum(r[k] for r in rows) / len(rows))  # noqa: E731
    weak = sorted(rows, key=lambda r: r["total"])[:5]
    return {
        "screens": len(rows),
        # 화면 소스를 읽을 수 있었는가. 배포본은 못 읽습니다 — 그때는
        # 숫자가 반쪽이라, 화면이 숫자 대신 그 사실을 말해야 합니다.
        "has_source": has_source(),
        # source 소스째 · snapshot 찍어 둔 글 · none 못 잼.
        # 찍어 둔 글이면 관리자 화면이 그 때를 함께 적습니다.
        "source": source_mode(),
        "snapshot_at": snapshot_at(),
        "pull": avg("pull"), "bite": avg("bite"),
        "heart": avg("heart"), "clear": avg("clear"),
        "plain": avg("plain"), "figure": avg("figure"),
        # 글이 앉은 모양 — 줄길이와 읽는 시간 (engine/typo.py)
        "measure": avg("measure"), "pace": avg("pace"),
        "secs": sum(r["secs"] for r in rows),
        "total": avg("total"),
        "weakest": [{"id": r["id"], "title": r["title"], "total": r["total"]}
                    for r in weak],
    }
