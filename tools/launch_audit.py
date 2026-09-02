"""
상용화해도 되는가 — 출시 전 전수조사.

    python tools/launch_audit.py

★ 코드가 도는 것과 팔아도 되는 것은 다르다

  돈을 받는 순간 이 서비스는 **통신판매**가 된다. 전자상거래법이
  요구하는 것이 있고, 없으면 과태료가 아니라 **영업정지**까지 간다.
  기능이 다 돌아도 이게 없으면 못 판다.

★ 이 도구가 세는 것 (docs/11 §9 체크리스트)

  ① 법정 고지    이용약관 · 개인정보처리방침 · 환불(청약철회)
  ② 사업자 표시  상호·대표·사업자등록번호·통신판매업신고번호·연락처
  ③ 나이 확인    만 14세 미만은 법정대리인 동의가 필요하다
  ④ 금지어       적중률·과학적 입증 — 표시광고법
  ⑤ 열쇠         결제·퍼널·알림이 열려 있지 않은지
  ⑥ 상시 고지    하단에 늘 떠 있어야 하는 문구

★ 이 도구가 **못** 하는 것

  통신판매업 신고, 사업자등록, 상표 검색은 사람이 관공서에서 한다.
  코드가 대신 못 한다. 여기서는 **자리가 준비돼 있는가**만 본다.
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "apps" / "web"
API = ROOT / "services" / "api"


def web_text() -> str:
    out = []
    for f in list(WEB.glob("app/**/*.tsx")) + list(WEB.glob("components/**/*.tsx")):
        out.append(f.read_text(encoding="utf-8"))
    return "\n".join(out)


def main() -> int:
    print("=" * 76)
    print("  상용화해도 되는가 — 출시 전 전수조사")
    print("=" * 76)

    t = web_text()
    fail = []
    warn = []

    def check(name, ok, why="", hard=True):
        print("  %-24s %s" % (name, "있음" if ok else "★ 없음"))
        if not ok:
            (fail if hard else warn).append((name, why))

    # ── ① 법정 고지 ──────────────────────────────────────
    print("\n  ① 법정 고지 — 전자상거래법 제13조")
    check("이용약관", "이용약관" in t,
          "계약 내용이 없으면 분쟁에서 근거가 없습니다")
    check("개인정보처리방침", "개인정보처리방침" in t or "개인정보 처리방침" in t,
          "생년월일시를 받습니다. 방침 게시는 개인정보보호법 제30조 의무")
    check("환불·청약철회", "청약철회" in t or "환불" in t,
          "콘텐츠는 열람 즉시 철회 제한 사유가 생기므로 **미리** 고지해야 합니다")

    # ── ② 사업자 표시 ────────────────────────────────────
    print("\n  ② 사업자 표시 — 전자상거래법 제10조")
    for k, why in (("상호", "누가 파는지"), ("대표", "책임자"),
                   ("사업자등록번호", "국세청"),
                   ("통신판매업", "신고번호 없이 팔면 미신고 영업"),
                   ("전화", "연락받을 데"), ("주소", "소재지")):
        check(k, k in t, why)

    # ── ③ 나이 ───────────────────────────────────────────
    print("\n  ③ 나이 — 만 14세 미만")
    check("14세 확인", "14세" in t,
          "만 14세 미만은 법정대리인 동의가 필요합니다 (개보법 제22조의2)")

    # ── ④ 금지어 ─────────────────────────────────────────
    print("\n  ④ 금지어 — 표시광고법")
    # ★ **부정문은 세지 않습니다.**
    #
    #   「적중률이라는 말은 아예 쓰지 않소」 「예측 적중률이 아닙니다」 —
    #   이건 위반이 아니라 오히려 지켜 주는 문장입니다. 처음 판이 이걸
    #   여섯 개 다 걸었습니다. 도구가 지키는 문장을 위반으로 세면,
    #   고치라는 대로 고쳤을 때 **진짜로 위반이 됩니다.**
    ban = re.compile(r"적중률|과학적으로 (?:입증|증명)|통계학|"
                     r"반드시 (?:옵니다|됩니다)")
    #   부정은 앞에도 뒤에도 옵니다 — 「쓰지 않는다」 는 뒤, 「아무
    #   숫자도 안 띄우오. 적중률…」 은 앞입니다. 양쪽을 봅니다.
    NEG = re.compile(r"아니|않|안 쓰|안 쓴|못 쓰|없|말라|금지|"
                     r"쓰지|안 씁|피한|빼")
    hit = [m.group(0) for m in ban.finditer(t)
           if not NEG.search(t[max(0, m.start() - 40):m.start() + 44])]
    print("  %-24s %s" % ("화면의 금지어", "없음" if not hit else "★ %s" % hit[:3]))
    if hit:
        fail.append(("금지어", "표시광고법 위반. docs/11 §1"))

    # ── ⑤ 열쇠 ───────────────────────────────────────────
    print("\n  ⑤ 열쇠 — 열려 있으면 안 되는 자리")
    # ★ 열쇠 **이름**을 찾지 않습니다.
    #
    #   처음 판은 관리자에 `ADMIN_KEY` 라는 글자가 있는지 봤습니다.
    #   없어서 「열려 있음」 이라 했는데, 실제로는 퍼널과 **같은 열쇠**를
    #   일부러 쓰고 있었습니다 — 둘을 따로 두면 하나만 걸어 두고
    #   배포하는 날이 옵니다. 배포본에 물어 보니 401 이었습니다.
    #
    #   이름이 아니라 **문마다 지킴이를 부르는가**를 봅니다.
    #   퍼널은 events.py 가 냅니다 — 파일 이름이 길과 다릅니다.
    #   길로 찾으면 파일을 옮겨도 안 놓칩니다.
    for name, route in (("퍼널 API", "/v1/funnel"), ("관리자", "/v1/admin")):
        src = ""
        for f in (API / "routers").glob("*.py"):
            txt = f.read_text(encoding="utf-8")
            if route in txt:
                src = txt
                break
        # 퍼널은 events.py 안에서 이벤트 수집과 같이 삽니다. 수집 문은
        # 손님이 쓰는 문이라 안 잠급니다 — 조회 문만 셉니다.
        eps = len(re.findall(r"@router\.get", src))
        guards = len(re.findall(r"_guard\(", src)) - src.count("def _guard(")
        ok = eps > 0 and guards >= eps
        print("  %-24s %s (문 %d · 지킴 %d)"
              % (name, "잠김" if ok else "★ 열려 있음", eps, guards))
        if not ok:
            fail.append((name, "문 %d개 중 %d개만 지키고 있소" % (eps, guards)))

    # ── ⑥ 상시 고지 ──────────────────────────────────────
    print("\n  ⑥ 상시 고지 — docs/11 §3")
    check("오락 목적 고지", "오락" in t or "참고용" in t or "재미" in t,
          "점술은 오락·참고 목적임을 상시 밝혀야 다툼이 줄어듭니다")
    check("성향검사 상표 회피", "MBTI" not in t,
          "MBTI 는 등록상표입니다. 쓰면 안 됩니다", hard=True)

    # ── 사람이 해야 하는 것 ──────────────────────────────
    print("\n" + "-" * 76)
    print("  ※ 코드가 대신 못 하는 것 — 사람이 관공서에서")
    print("     · 사업자등록 (홈택스)")
    print("     · 통신판매업 신고 (정부24 · 구청)")
    print("     · 「성신당」 상표 검색·출원 (특허로) — 성심당과 한 글자 차이")
    print("     · 결제대행 계약·정산 계좌")

    print("\n" + "=" * 76)
    if not fail and not warn:
        print("  [OK] 팔아도 되는 자리는 다 준비됐소")
    else:
        print("  ★ 막는 것 %d · 봐야 할 것 %d" % (len(fail), len(warn)))
        for n, why in fail:
            print("     [막음] %-16s %s" % (n, why))
        for n, why in warn:
            print("     [주의] %-16s %s" % (n, why))
    print("=" * 76)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
