"""
내주기와 돌려받기 — 도입부에서 손님이 얼마나 오래 주기만 하는가.

    python tools/give_take.py
    python tools/give_take.py --show    화면마다 무엇을 돌려주는지

★ 왜 이 자가 생겼는가 (2026-09-04)

  연출 점수는 스물여덟 화면이 다 90점 위인데 손님이 말했습니다 —
  "몰입이 전혀 안되잖아. 밍숭맹숭한 말만 하니까."

  자가 틀린 게 아니라 **안 재는 것이 있었습니다.** 연출 점수는 화면
  하나를 따로 봅니다. 그런데 도입부에서 무너지는 것은 화면이 아니라
  **차례**입니다 — 이름, 고민, 해, 달, 날, 시, 분, 넉 자. 열여섯 칸을
  내주는 동안 손님이 돌려받는 것이 없으면, 화면 하나하나가 아무리
  좋아도 그건 서식을 채우는 일입니다.

★ 무엇을 재는가

    내줌     그 화면이 손님에게 요구하는 칸 수 (입력·고르기)
    돌려줌   그 화면이 **손님의 값**으로 하는 말의 수
             (화면 글에 박힌 ▮ — 이름·글자·나이·개수처럼 이 손님한테만
              해당하는 자리. screenscan 이 값 자리를 ▮ 로 남깁니다)
    빚       내준 것에서 돌려받은 것을 뺀 누적

★ 무엇이 잘못인가

  ① 빚이 오래 쌓이는 구간 — 세 화면 넘게 돌려줌이 0이면 서식입니다
  ② 첫 돌려줌이 늦은 것 — 「나에 대한 말」을 몇 번째 화면에서 처음
     듣는가. 정보 격차 이론(Loewenstein 1994)은 빈칸이 **가까이 있다고
     믿을 때** 호기심이 선다고 합니다. 멀면 궁금하지 않고 지칩니다.

★ 재지 않는 것 — 글의 좋고 나쁨. 그건 연출 점수가 봅니다.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services" / "api"))

from engine import screenscan as S                     # noqa: E402

# 손님이 도는 차례 — docs/08. 진입은 이 순서로 지납니다.
FUNNEL = ["a1", "a2", "a5", "a3", "a4", "a4b", "a6", "a7"]

# 손님이 값을 내주는 자리
FIELD = re.compile(r"<(input|select|textarea)\b", re.I)

# ★ 되비추기와 돌려주기는 다릅니다 (2026-09-04).
#
#   `{s.year}` 는 손님이 방금 적은 것을 그대로 되비추는 것입니다. 칸에
#   글자가 보이는 건 당연한 일이라, 손님은 아무것도 받은 것이 없습니다.
#
#   `{f.day_gan}` 은 **우리가 셈해서** 돌려주는 것입니다. 손님이 안 적은
#   것이고, 적은 것에서 나온 것입니다. 이것만 「돌려줌」 으로 셉니다.
#
#   이 둘을 안 가르면 자가 모든 화면에서 「돌려줬다」 고 합니다 —
#   실제로는 여섯 화면 동안 한 번도 안 돌려줬는데도요.
BRACE = re.compile(r"\{([^{}]{2,80})\}")
# 셈해서 나온 것 — 손님이 안 적은 값
DERIVED = re.compile(
    r"\bfeatures\b|\bf\.[a-z_]|\bpeek\b|\bp\.gz\b|day_gan|day_ji"
    r"|pillars|elements|ten_gods"
    r"|daeun|yongsin|strength|segments|chart|sinsal|rarity|axis|c\.(why|ours"
    r"|mine|theirs|moved)")
# 되비추기 — 손님이 방금 적은 것
ECHO = re.compile(r"\bs\.(name|year|month|day|hour|minute|city|sex|axis4"
                  r"|concern)\b|askWord|clockWord")


# ★ 셈할 재료가 없는 자리도 있습니다 (2026-09-04).
#
#   a1·a2·a5 는 아직 생년월일을 안 받았으니 **돌려줄 것이 없습니다.**
#   그렇다고 그냥 받기만 해도 되는 건 아닙니다. 돌려줄 수 없으면
#   **구체적인 고리**라도 열어야 합니다 —
#
#       고리 아님   「무언가 알게 되오」   (막연함 · 안 궁금함)
#       고리 맞음   「셋만 적으면 여섯이 서오」 (수 · 가깝고 · 다음 자리)
#
#   정보 격차 이론(Loewenstein 1994)이 말하는 조건 그대로입니다 —
#   빈칸이 **구체적**이고 **가까이 있다고 믿을 때** 호기심이 섭니다.
#
#   그래서 「받기만 하오」 는 돌려줌도 고리도 **둘 다 없을 때**만
#   붙입니다. 그리고 아무것도 안 받는 화면(a1 대문)은 애초에 빚이
#   없으니 나무라지 않습니다.
LOOP_NUM = re.compile(r"[0-9]|하나|둘|셋|넷|다섯|여섯|일곱|여덟|아홉|열")
LOOP_NEXT = re.compile(r"다음|이제|적으면|세우면|나오오|서오|드리오|하겠소"
                       r"|여쭙|보겠소")


def loops(text: str) -> int:
    """이 화면이 연 **구체적인 고리** — 수가 있고 다음을 가리키는 줄."""
    n = 0
    for line in re.split(r"(?<=[.!?…])\s+", text):
        if LOOP_NUM.search(line) and LOOP_NEXT.search(line):
            n += 1
    return n


def gives(chunk: str) -> list:
    """이 화면이 **셈해서** 돌려주는 자리들."""
    out = []
    for m in BRACE.finditer(chunk):
        e = m.group(1).strip()
        if len(e) > 60 or "className" in e:
            continue
        # 화살표 함수라도 **안에서 셈한 값을 그리면** 돌려주는 것입니다 —
        # `peek.pillars.map((p, i) => <span>{p.gz}</span>)` 가 그렇소.
        if "=>" in e and not DERIVED.search(e):
            continue
        # ★ 상태를 **넣는** 자리는 돌려주는 것이 아닙니다.
        #   `features: null, chartId: null` 은 값을 지우는 코드지 손님에게
        #   하는 말이 아닙니다. 이걸 안 빼면 a3 가 「넷을 돌려줬다」 고
        #   나오는데, 실제로 손님이 보는 것은 자기가 적은 숫자뿐입니다.
        if re.search(r"\w+\s*:\s*", e) and "?" not in e:
            continue
        if ECHO.search(e) and not DERIVED.search(e):
            continue
        if DERIVED.search(e):
            out.append(e)
    return out
# 고르는 자리 — 여섯 칸 한 벌은 **한 번 고르는 것**이라 하나로 셉니다
PICKS = re.compile(r"\.map\(\(?\w+\)? =>[^)]*<button", re.S)


def screens_src() -> dict:
    """화면마다 (읽는 글, 소스 덩이)."""
    out = {}
    for rel in S.PAGES:
        p = S.WEB / rel
        if not p.exists():
            continue
        src = p.read_text(encoding="utf-8")
        masked = S._strip_code(src)
        for sid, v in S._split(masked).items():
            out[sid] = v[0]
    return out


def raw_chunks() -> dict:
    """화면마다 소스 그대로 — 칸을 세려면 태그가 살아 있어야 합니다."""
    out = {}
    for rel in S.PAGES:
        p = S.WEB / rel
        if not p.exists():
            continue
        src = p.read_text(encoding="utf-8")
        marks = []
        for m in S.SCREEN_DECL.finditer(src):
            marks.append((m.group(1), m.start()))
        marks.append(("__end__", len(src)))
        for i in range(len(marks) - 1):
            sid, a = marks[i]
            chunk = src[a:marks[i + 1][1]]
            if len(chunk) > len(out.get(sid, "")):
                out[sid] = chunk
    return out


def main() -> int:
    show = "--show" in sys.argv
    S._screens.cache_clear()
    text = screens_src()
    raw = raw_chunks()

    print("=" * 76)
    print("  내주기와 돌려받기 — 도입부에서 얼마나 오래 주기만 하는가")
    print("=" * 76)
    print()
    print("     %-5s %-11s %5s %6s %5s %6s"
          % ("화면", "이름", "내줌", "돌려줌", "고리", "빚"))

    debt, first_give, dry, worst_dry = 0, None, 0, 0
    rows = []
    for sid in FUNNEL:
        t = text.get(sid, "")
        chunk = raw.get(sid, "")
        give = len(FIELD.findall(chunk)) + len(PICKS.findall(chunk))
        # 셈해서 돌려주는 자리만 셉니다 — 되비추기는 안 셉니다
        got = gives(chunk)
        back = len(got)
        loop = loops(t)
        debt += give - min(back, give)
        if back and first_give is None:
            first_give = sid
        # 돌려줌도 고리도 없을 때만 마른 것입니다. 받는 것이 없는
        # 화면(대문)은 애초에 빚이 없으니 세지 않습니다.
        wet = back or loop or give == 0
        dry = 0 if wet else dry + 1
        worst_dry = max(worst_dry, dry)
        rows.append((sid, S.KO.get(sid, "?"), give, back, loop, debt, got))

    for sid, ko, give, back, loop, d, got in rows:
        bad = give and not back and not loop
        mark = "  ← 받기만 하오" if bad else ""
        print("     %-5s %-11s %5d %6d %5d %6d%s"
              % (sid, ko, give, back, loop, d, mark))
        if show and got:
            print("            %s" % " · ".join(sorted(set(got))[:5]))

    print()
    print("-" * 76)
    order = [r[0] for r in rows]
    print("  첫 돌려줌   %s (%d번째 화면)"
          % (first_give or "없소",
             order.index(first_give) + 1 if first_give else 0))
    print("  가장 긴 마른 구간   %d화면" % worst_dry)
    print("  쌓인 빚   %d칸" % debt)
    print("-" * 76)
    print("  ※ 빈칸이 가까이 있다고 믿을 때 호기심이 서오 (Loewenstein 1994).")
    print("    멀면 궁금한 게 아니라 지치오 — 그때는 좋은 글도 서식이오.")
    print("-" * 76)
    return 1 if worst_dry >= 3 else 0


if __name__ == "__main__":
    raise SystemExit(main())
