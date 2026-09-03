"""
팔아도 되는가 — 잠금.

★ 코드가 도는 것과 팔아도 되는 것은 다르다

  돈을 받는 순간 이 서비스는 **통신판매**가 된다. 기능이 다 돌아도
  전자상거래법이 요구하는 표시가 없으면 못 판다. 과태료가 아니라
  영업정지까지 간다.

★ 여기서 지키는 것

  ① 약관·방침·환불이 **상시** 닿는 자리에 있는가
  ② 사업자 정보를 **코드에 박지 않았는가** — 임시값은 그대로 배포된다
  ③ 표시가 없으면 **값을 안 받는가** — 결제 키가 없으면 거절하는 것과
     같은 규칙. 열린 쪽이 기본이면 언젠가 그대로 나간다
  ④ 만 14세 미만을 막는가 — 나이를 또 묻지 않고 받은 생년월일로 센다
  ⑤ 영업 정보를 내는 문마다 지킴이가 붙어 있는가

★ 여기서 못 지키는 것

  사업자등록·통신판매업 신고·상표는 사람이 관공서에서 한다.
  검사는 **자리가 준비돼 있는가**만 본다.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "apps" / "web"
API = ROOT / "services" / "api"
sys.path.insert(0, str(API))


def _web() -> str:
    return "\n".join(
        f.read_text(encoding="utf-8")
        for f in list(WEB.glob("app/**/*.tsx")) + list(WEB.glob("components/**/*.tsx")))


def test_법정_고지_화면이_있다():
    p = WEB / "app" / "legal" / "page.tsx"
    assert p.exists(), "/legal 화면이 없소"
    t = p.read_text(encoding="utf-8")
    for k in ("이용약관", "개인정보처리방침", "환불", "청약철회"):
        assert k in t, k


def test_하단에서_늘_닿는다():
    """결제 화면에만 두면 **결제 전에** 못 읽습니다."""
    t = (WEB / "components" / "Shell.tsx").read_text(encoding="utf-8")
    assert '"/legal"' in t, "하단 고지에 법정 화면 링크가 없소"


def test_사업자_정보를_코드에_박지_않는다():
    """
    ★ 임시값은 **그대로 배포됩니다.**

      상호·대표·사업자등록번호는 관공서에서 받아 오는 것입니다.
      코드에 「(주)어쩌고」 를 박아 두면 그날 화면에 그게 뜹니다.
    """
    t = (WEB / "lib" / "biz.ts").read_text(encoding="utf-8")
    # 사업자등록번호 꼴(000-00-00000)이 코드에 있으면 안 됩니다
    assert not re.search(r"\d{3}-\d{2}-\d{5}", t), "등록번호가 박혀 있소"
    for k in ("BIZ_NAME", "BIZ_REG_NO", "BIZ_MAIL_ORDER_NO"):
        assert k in t, "%s 를 밖에서 받지 않소" % k


def test_표시가_없으면_값을_안_받는다():
    """결제 열쇠가 없으면 거절하는 것과 **같은 규칙**입니다."""
    t = (WEB / "app" / "pay" / "page.tsx").read_text(encoding="utf-8")
    assert "SELLABLE" in t, "사업자 표시 없이도 결제창이 열리오"


def test_만_14세_미만을_막는다():
    """개인정보보호법 제22조의2 — 법정대리인 동의가 필요합니다."""
    t = (WEB / "app" / "page.tsx").read_text(encoding="utf-8")
    assert "needsGuardian" in t, "나이 확인이 없소"
    b = (WEB / "lib" / "biz.ts").read_text(encoding="utf-8")
    assert "< 14" in b, "문턱이 14가 아니오"


def test_화면에_금지어가_없다():
    """
    표시광고법 — 적중률·과학적 입증·통계학.

    ★ 부정문은 세지 않습니다. 「적중률이라는 말은 아예 쓰지 않소」 는
      위반이 아니라 지켜 주는 문장입니다.
    """
    t = _web()
    ban = re.compile(r"적중률|과학적으로 (?:입증|증명)|통계학")
    neg = re.compile(r"아니|않|안 쓰|안 쓴|못 쓰|없|말라|금지|쓰지|피한|빼")
    for m in ban.finditer(t):
        near = t[max(0, m.start() - 40):m.start() + 44]
        assert neg.search(near), "금지어가 주장으로 쓰였소: %s" % near[:60]


# ══════════════════════════════════════════════════════════
# 문마다 지킴이 붙어 있는가
# ══════════════════════════════════════════════════════════
#
# ★ 세는 법 (2026-09-03 에 고쳤습니다)
#
#   전에는 `@router.get` 수와 `_guard(` 수를 견줬습니다. 그런데 문이
#   두 가지 더 생겼습니다 —
#
#     · 스스로 지키는 문 (`adminauth.session_of` 로 쪽지를 봅니다)
#     · **일부러 여는 문** (`/gate` — 화면이 로그인 칸을 그릴지 열쇠
#       칸을 그릴지 정하려면 열쇠 없이 물어봐야 합니다. 걸렸는지
#       아닌지만 답하고 아이디는 안 흘립니다.)
#
#   수만 늘려 통과시키면 다음에 진짜로 빠뜨린 문이 안 걸립니다.
#   그래서 **의도를 적게** 합니다 — 아래 표시가 없는 문은 여전히
#   지킴이 있어야 합니다.
OPEN_MARK = "# 문 없음:"           # 일부러 여는 문. 까닭을 뒤에 적는다
SELF_MARK = "session_of("          # 스스로 쪽지를 보는 문


def _unguarded(src: str) -> list:
    """지킴도 없고 표시도 없는 조회문의 이름."""
    bad = []
    blocks = src.split("@router.get")[1:]
    for b in blocks:
        body = b.split("@router.")[0]
        name = re.search(r"def (\w+)", body)
        if "_guard(" in body or SELF_MARK in body or OPEN_MARK in body:
            continue
        bad.append(name.group(1) if name else "?")
    return bad


def test_영업정보_문마다_지킴이가_있다():
    """
    ★ 문이 하나 늘 때 지킴을 빠뜨리는 것이 이 자리의 사고입니다.

      지킴도 없고 「일부러 연다」는 표시도 없는 조회문은 실수입니다.
    """
    api = API / "routers"
    for fn in ("admin.py", "events.py"):
        bad = _unguarded((api / fn).read_text(encoding="utf-8"))
        assert not bad, "%s — 지킴도 표시도 없는 문: %s" % (fn, bad)


def test_문지기가_한_자리다():
    """
    같은 일을 두 곳에서 하면 한쪽만 고치는 날이 옵니다.

    ★ 실제로 events.py 안에 **같은 코드가 두 번** 있었습니다. 한 번만
      고쳤더니 조회 문이 옛 코드로 남아 있었습니다.
    """
    assert (API / "keyguard.py").exists()
    for fn in ("admin.py", "events.py"):
        src = (API / "routers" / fn).read_text(encoding="utf-8")
        assert "from keyguard import" in src, fn
        assert 'os.getenv("FUNNEL_KEY"' not in src, "%s 가 열쇠를 또 읽소" % fn
