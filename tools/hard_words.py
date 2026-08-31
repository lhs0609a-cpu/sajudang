"""
어려운 말 전수조사 — 손님이 모르는 말이 풀이 없이 나오는가.

    python tools/hard_words.py            # 전부
    python tools/hard_words.py --screens  # 화면 코드만
    python tools/hard_words.py --show 상관 # 그 말이 나오는 자리 보기

★ 왜 재나

  이 집은 "맞히는 집" 이 아니라 **"근거 대는 집"** 입니다. 그런데 근거를
  **손님이 모르는 말로** 대면 그건 근거가 아니라 주문입니다.

      "주도 십신 상관 · 흐름 식상 · 용신 불 · 대운 순행"

  「상관」이 무엇인지 아는 손님은 거의 없습니다. 뜻을 모르는 채로 읽으면
  신뢰가 생기는 게 아니라 **압도당합니다.** 압도는 결제로 안 이어집니다.

★ 용어를 지우자는 게 아닙니다.

  명리 용어는 이 집의 근거이자 신뢰의 재료입니다. 없애면 여느 점집과
  같아집니다. **그 자리에서 풀어 주면** 근거가 됩니다.

★ 이 도구가 하는 일

  화면 코드와 엔진이 실제로 내놓는 글에서 어려운 말을 찾아,
  **풀이가 곁에 있는지** 봅니다. 없으면 어디에 몇 번 나오는지 셉니다.
"""
from __future__ import annotations

import collections
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "apps" / "web"
if str(ROOT / "services" / "api") not in sys.path:
    sys.path.insert(0, str(ROOT / "services" / "api"))

# ══════════════════════════════════════════════════════════
# 어려운 말과 그 뜻
# ══════════════════════════════════════════════════════════
#
# ★ 여기 있는 뜻은 **화면에 쓸 말**입니다. 사전 정의가 아니라
#   손님에게 건네는 한 마디입니다. 짧아야 읽힙니다.
HARD = {
    # ── 십신 열 ───────────────────────────────────────
    "비견": "나와 같은 힘 · 고집과 자립",
    "겁재": "나와 겨루는 힘 · 경쟁과 나눔",
    "식신": "밖으로 내놓는 힘 · 표현",
    "상관": "밖으로 내지르는 힘 · 재주와 거침",
    "편재": "굴리는 재물 · 벌이와 씀씀이",
    "정재": "쌓는 재물 · 성실과 저축",
    "편관": "나를 누르는 힘 · 압박과 책임",
    "정관": "나를 잡아 주는 힘 · 규율과 자리",
    "편인": "받아들이는 힘 · 직관",
    "정인": "기대는 힘 · 배움과 보살핌",
    # ── 묶음 ─────────────────────────────────────────
    "십신": "여덟 글자 사이의 관계에 붙인 이름 열 가지",
    "비겁": "나와 같은 편의 힘",
    "식상": "밖으로 내놓는 힘",
    "재성": "재물을 보는 자리",
    "관성": "나를 누르거나 잡아 주는 자리",
    "인성": "받아들이고 기대는 자리",
    # ── 자리 ─────────────────────────────────────────
    "일간": "나 자신을 나타내는 글자",
    "일지": "태어난 날의 아랫 글자 · 곁의 자리",
    "월지": "태어난 달의 아랫 글자 · 계절의 자리",
    "년주": "태어난 해의 두 글자",
    "월주": "태어난 달의 두 글자",
    "일주": "태어난 날의 두 글자 · 나 자신",
    "시주": "태어난 시각의 두 글자",
    "천간": "위에 오는 글자",
    "지지": "아래에 오는 글자",
    "지장간": "아랫 글자 속에 숨은 기운",
    # ── 판정 ─────────────────────────────────────────
    "신강": "기운이 넉넉한 쪽",
    "신약": "기운이 모자란 쪽",
    "중화": "한쪽으로 크게 안 기운 쪽",
    "용신": "모자란 것을 채워 줄 기운",
    "희신": "용신을 돕는 기운",
    "기신": "지금 걸리는 기운",
    "격": "이 사주를 읽는 틀",
    "조후": "춥고 더움을 고르는 것",
    "통근": "위 글자가 아래에 뿌리를 둔 것",
    # ── 때 ───────────────────────────────────────────
    "대운": "십 년마다 읽는 자리가 바뀌는 것",
    "세운": "그 해의 기운",
    "일진": "그날의 기운",
    "절기": "계절이 바뀌는 마디 스물넷",
    "절입": "그 마디로 넘어가는 시각",
    "진태양시": "해가 남중하는 때로 고친 시각",
    "순행": "앞으로 나아가며 도는 것",
    "역행": "거꾸로 거슬러 도는 것",
    # ── 관계 ─────────────────────────────────────────
    "상생": "서로 낳아 주는 사이",
    "상극": "서로 누르는 사이",
    "공망": "비어 있는 자리",
    # ── 신살 ─────────────────────────────────────────
    "도화": "사람을 끄는 자리",
    "역마": "옮겨 다니는 자리",
    "화개": "혼자 파고드는 자리",
    "괴강": "세게 서는 자리",
    "양인": "날이 선 자리",
    "원진": "까닭 없이 걸리는 자리",
    "귀문": "예민하게 도는 자리",
    "백호": "거센 자리",
}

# 풀이가 곁에 있다고 볼 표시 — 괄호·줄표·'—' 뒤 설명
NEAR = 40      # 이 글자 수 안에 뜻이 있으면 풀렸다고 봅니다


# ★ 같은 글자인데 다른 말인 자리 — 세면 안 됩니다.
#   「글자를 세운다」의 '세운' 은 용어가 아니라 동사입니다.
FALSE = {"세운": ("세운다", "세운 ", "세운다면", "세운다는")}


def _real(text: str, term: str, at: int) -> bool:
    for bad in FALSE.get(term, ()):
        if text[at:at + len(bad)] == bad:
            return False
    return True


def glossed(text: str, term: str, meaning: str) -> bool:
    """그 말 곁에 뜻이 있는가. 뜻의 앞 대여섯 자로 봅니다."""
    key = meaning.split("·")[0].strip()[:4]
    for m in re.finditer(re.escape(term), text):
        window = text[m.start(): m.end() + NEAR]
        if key and key in window:
            return True
    return False


def screen_text() -> dict:
    """화면 코드에서 사람이 읽는 말만 대충 긁어냅니다."""
    out = {}
    for p in list((WEB / "app").rglob("*.tsx")) + \
             list((WEB / "components").rglob("*.tsx")):
        if p.name == "DevRail.tsx":
            continue
        src = p.read_text(encoding="utf-8")
        src = re.sub(r"/\*.*?\*/", " ", src, flags=re.S)   # 블록 주석
        src = re.sub(r"//[^\n]*", " ", src)                 # 줄 주석
        # ★ 사람이 읽는 글만 남깁니다.
        #   JSX 태그와 속성을 그대로 두면 나란히 붙어 있는 풀이가
        #   마크업 때문에 멀리 떨어진 것으로 보입니다.
        src = re.sub(r"<[^>]*>", " ", src)
        src = re.sub(r"[{}]", " ", src)
        src = re.sub(r"\s+", " ", src)
        out[str(p.relative_to(WEB))] = src
    return out


def engine_text() -> dict:
    """엔진이 실제로 내놓는 글 — 훅 · 리포트 · 일진."""
    from engine import bank as bank_mod
    from engine import daily as daily_mod
    from engine import lens as lens_mod
    from engine.calendar import build_chart
    from engine.features import build_features
    from engine.report import build_report, _plain

    out = collections.defaultdict(str)
    for y, m, d, h, mi, sx in [(1997, 3, 22, 14, 10, "F"),
                               (1985, 11, 3, 7, 40, "M")]:
        f = build_features(build_chart(y, m, d, h, mi, sx, True, "서울"))
        for c in ("love", "money", "work"):
            out["훅 %s" % c] += " " + " ".join(
                _plain(s["html"])
                for s in bank_mod.build_hook(f, c, "INFP", "가은", "그대"))
        # ★ 리포트는 **한 장을 통째로** 봅니다.
        #   풀이는 한 장에 한 번만 답니다(engine/terms.py) — 컷마다 따로
        #   세면 두 번째 컷부터 전부 "안 풀림" 으로 잡힙니다. 손님은
        #   한 장을 이어서 읽지, 컷을 따로 읽지 않습니다.
        for l in lens_mod.released():
            tier = "one" if l.get("price") else "free"
            rep = build_report(f, "t", l["id"], tier, "love", "INFP",
                               name="가은")
            out["리포트 " + l["id"]] += " " + " ".join(
                _plain(c["html"]) for c in rep["cuts"])
        out["일진"] += " " + " ".join(daily_mod.build_daily(f)["lines"])
    return dict(out)


def main() -> int:
    only_screens = "--screens" in sys.argv
    show = None
    if "--show" in sys.argv:
        i = sys.argv.index("--show")
        show = sys.argv[i + 1] if i + 1 < len(sys.argv) else None

    texts = {}
    texts.update({"화면 · " + k: v for k, v in screen_text().items()})
    if not only_screens:
        texts.update({"글 · " + k: v for k, v in engine_text().items()})

    print("=" * 76)
    print("  어려운 말 전수조사 — 풀이 없이 나오는 자리")
    print("=" * 76)

    if show:
        print("\n「%s」 가 나오는 자리 — %s" % (show, HARD.get(show, "(모르는 말)")))
        for where, t in sorted(texts.items()):
            for m in re.finditer(re.escape(show), t):
                seg = re.sub(r"\s+", " ", t[max(0, m.start()-34): m.end()+34])
                print("  %-24s …%s…" % (where[:24], seg))
        return 0

    naked = collections.Counter()
    where_at = collections.defaultdict(set)
    total = collections.Counter()
    for where, t in texts.items():
        for term, meaning in HARD.items():
            n = sum(1 for m in re.finditer(re.escape(term), t)
                    if _real(t, term, m.start()))
            if not n:
                continue
            total[term] += n
            if not glossed(t, term, meaning):
                naked[term] += n
                where_at[term].add(where.split(" · ")[1][:22])

    print("\n풀이 없이 나오는 말 — 많은 것부터")
    print("  %-8s %6s %6s  %s" % ("말", "전체", "안 풀림", "어디에"))
    print("  " + "-" * 70)
    for term, n in naked.most_common(28):
        print("  %-8s %6d %6d  %s"
              % (term, total[term], n,
                 " · ".join(sorted(where_at[term])[:3])))

    print("\n" + "-" * 76)
    print("  어려운 말 %d가지가 글에 나옴 · 그중 **%d가지가 풀이 없이** 나옴"
          % (len(total), len(naked)))
    print("  풀이 없이 나온 횟수 합계 %d" % sum(naked.values()))
    print("-" * 76)
    print("  용어를 지우자는 게 아닙니다. 그 자리에서 풀면 근거가 됩니다.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
