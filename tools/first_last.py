"""
첫 줄과 끝 줄 — 자리마다 할 일이 다르다.

    python tools/first_last.py
    python tools/first_last.py --show    첫 줄·끝 줄을 그대로

★ 손님이 못박은 세 자리 (2026-09-04)

    처음      팩폭으로 뼈를 때려서 「이거 내 이야기야」 공감하게
    마지막    다음 페이지를 보고 싶어 미치도록
    결제 전   궁금해 미치도록

★ 이미 재고 있던 것과 아닌 것

  연출 점수의 **당김**은 끝을 봅니다 — 액트아웃 다섯 꼴(밝힘·뒤집기·
  딜레마·끊긴 동작·남긴 물음)과 콜드 오픈을 셉니다. 거기는 자가 있습니다.

  **팩폭**은 화면 전체에서 셀 수 있는 말을 셉니다. 그런데 **어디에**
  있는지는 안 봅니다. 셀 수 있는 말이 스무 줄째에 처음 나오면, 손님은
  그 앞에서 이미 훑기 시작합니다. 첫인상은 첫 줄이 만듭니다.

  그래서 이 자는 **자리**만 봅니다 — 무엇이 있는가가 아니라, 그것이
  맨 앞에 있는가.

★ 무엇을 세는가

    첫 팩폭   첫 두 줄 안에 **셀 수 있는 것**이 있는가
              (수 · 글자 · 나이 · 해 · 「0」 · 「없소」)
    끝 고리   마지막 두 줄이 다음을 가리키는가
              (물음표 · 다음 자리 이름 · 아직/남았/열리오)

★ 재지 않는 것 — 글의 좋고 나쁨. 그건 연출 점수가 봅니다.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services" / "api"))

from engine import screenscan as S                     # noqa: E402

# 셀 수 있는 것 — 손님이 세어 보고 다르면 우리가 지는 말
# ★ 한글에는 `\b` 가 안 듣습니다 (2026-09-04).
#
#   「표 하나로」 「손이 한 번」 의 수사가 안 잡혔습니다. `\b(하나)\b`
#   는 뒤에 조사 「로」 가 붙으면 낱말 경계가 아니라고 봅니다 — 한글은
#   조사가 붙어 다니므로 뒤쪽 경계를 걸면 거의 다 놓칩니다.
#   앞만 봅니다.
COUNTABLE = re.compile(
    r"[0-9]|하나도 없|없소|없어요|없습니다|"
    r"(?:^|[\s(「『·—-])(하나|둘|셋|넷|다섯|여섯|일곱|여덟|아홉|열|한 번|두 번)|"
    r"몇|살이|년은|자리가")

# ★ 수만 뼈를 때리는 게 아닙니다 (2026-09-04).
#
#   생년월일을 받기 **전** 화면(a1·a2·a5)에는 셀 수 있는 것이 없습니다.
#   아직 아무것도 안 셌으니까요. 그렇다고 그 자리에서 「이거 내
#   이야기야」 를 못 만드는 건 아닙니다 — 이 집이 쓰는 다른 연장이
#   **관찰**입니다.
#
#       「여태 이런 칸에서 가짜 이름을 적어 본 적이 있소.」
#       「고르기를 미루다 그냥 닫은 사람이 적지 않소.」
#
#   이것도 **틀릴 수 있는 말**입니다 — 그런 적이 없는 사람에게는
#   안 맞습니다. 그러니 바넘이 아니고, 맞는 사람에게는 수만큼 아픕니다.
#
#   자가 수만 세면 이 연장을 못 봅니다. 그러면 잘 쓴 화면을 「첫 줄에
#   팩폭이 없다」 고 나무라고, 고치라는 대로 고치면 오히려 나빠집니다.
OBSERVED = re.compile(
    r"여태|늘 그|자꾸|번번이|매번|한 번쯤|해 본 적|들었을 것|"
    r"았을 것이오|었을 것이오|았을 게요|었을 게요|"
    r"적이 있|적이 없|사람이 적지 않|사람을 여럿")

# 다음을 가리키는 끝
HOOK = re.compile(
    r"[?？]|「[^」]{2,20}」|아직|남았|남은|다음|뒤에|더 있|열리|"
    r"안 (?:했|보|열)|이제")

# 뒤로 볼 줄 수
EDGE = 2
# ★ 앞은 **세 줄**까지 봅니다.
#   이 집의 화면은 지문(나레이션) 한두 줄로 엽니다 — 그건 장면이고,
#   연출 점수의 당김이 그걸 보고 「콜드 오픈」 으로 셉니다. 지문을
#   없애면 당김이 죽습니다. 그러니 지문은 두고, **그 다음 줄**이
#   뼈를 때리는지를 봅니다.
#
#   넷인 까닭 — 이 집의 화면은 차례가 정해져 있습니다.
#       ① 지문 (장면)      「붓이 저 혼자 떠올랐다.」
#       ② 지문 (한 줄 더)  「종이는 아직 비어 있다.」
#       ③ 인사·물음        「처음 뵙겠소. 그대를 뭐라 적으면 되겠소?」
#       ④ **뼈**           「여태 이런 칸에서 가짜 이름을 적어 본 적이 있소.」
#   ③ 을 없애면 손님은 왜 묻는지 모른 채 답부터 듣습니다. 그러니
#   넷째 줄까지가 「처음」 입니다. 다섯째부터는 늦습니다.
HEAD = 4


# 손님이 누르는 말 — 「…하겠습니다」. 화면의 **끝**이 아니라 손잡이입니다.
#
# ★ 끝 고리를 재는데 마지막 줄이 늘 버튼이었습니다. 버튼은 이 집의
#   말이 아니라 손님의 말이고(CLAUDE.md), 막을 끊는 줄은 그 **위**에
#   있습니다. 버튼을 끝으로 보면 어느 화면이나 「고리가 없다」 가 됩니다.
BUTTON = re.compile(r"(습니다|겠소|시오)$")


def lines(text: str) -> list:
    out = [x.strip() for x in re.split(r"(?<=[.!?…])\s+|\n+", text)]
    return [x for x in out if len(x) > 4]


def body_lines(text: str) -> list:
    """끝에 붙은 버튼 말을 걷어낸 줄들."""
    ls = lines(text)
    while ls and BUTTON.search(ls[-1]) and len(ls[-1]) < 30:
        ls.pop()
    return ls


def main() -> int:
    show = "--show" in sys.argv
    S._screens.cache_clear()
    rows = S.scan_all()
    text, named = {}, {}
    for sid, v in S._screens().items():
        text[sid] = v[0]
        # ★ 예고는 **선언**으로도 옵니다 (2026-09-04).
        #
        #   화면은 「다음 자리 — 「글자가 서다」」 로 그려지는데, 그 글자는
        #   `ActOut.tsx` 안에 있고 화면 파일에는 `next="글자가 서다"` 라는
        #   **속성**으로만 있습니다. 속성은 태그 안이라 글 긁는 자에 안
        #   걸립니다.
        #
        #   그래서 「끝이 다음을 안 가리킨다」 로 잡힌 열둘 중 여럿이
        #   실은 **이름까지 대고 있었습니다.** screenscan 이 이미 읽어
        #   두었으니(ACT_NEXT) 그 값을 씁니다 — 같은 것을 두 번 읽으면
        #   두 잣대가 갈립니다.
        named[sid] = v[2]
    eng = S._engine_text()
    for sid, html in eng.items():
        text[sid] = html + " " + text.get(sid, "")

    print("=" * 76)
    print("  첫 줄과 끝 줄 — 처음은 팩폭, 끝은 고리")
    print("=" * 76)
    print()
    print("     %-5s %-11s %8s %8s" % ("화면", "이름", "첫 팩폭", "끝 고리"))
    print("     %s" % ("첫 팩폭 = 앞 %d줄에 셀 수 있는 것 **또는** 관찰"
                       % HEAD))

    bad_head, bad_tail = [], []
    for r in rows:
        sid = r["id"]
        plain = re.sub(r"<[^>]+>", " ", text.get(sid, ""))
        ls = lines(plain)
        if not ls:
            continue
        head = " ".join(ls[:HEAD])
        # 끝은 **버튼을 걷고** 봅니다
        tl = body_lines(plain) or ls
        tail = " ".join(tl[-EDGE:])
        h = bool(COUNTABLE.search(head)) or bool(OBSERVED.search(head))
        t = bool(HOOK.search(tail)) or bool(named.get(sid))
        if not h:
            bad_head.append((sid, r["title"], head))
        if not t:
            bad_tail.append((sid, r["title"], tail))
        print("     %-5s %-11s %8s %8s"
              % (sid, r["title"], "○" if h else "✕", "○" if t else "✕"))
        if show and (not h or not t):
            if not h:
                print("        첫 : %s" % head[:66])
            if not t:
                print("        끝 : %s" % tail[:66])
                print("             (다음 자리를 이름으로 안 부르오)")

    print()
    print("-" * 76)
    print("  첫 줄에 셀 수 있는 말이 없는 화면 %d" % len(bad_head))
    print("  끝이 다음을 안 가리키는 화면 %d" % len(bad_tail))
    print("-" * 76)
    print("  ※ 첫인상은 첫 줄이 만드오. 셀 수 있는 말이 스무 줄째에")
    print("    나오면 손님은 그 앞에서 이미 훑기 시작하오.")
    print("-" * 76)
    return 1 if (bad_head or bad_tail) else 0


if __name__ == "__main__":
    raise SystemExit(main())
