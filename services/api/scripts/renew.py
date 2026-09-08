"""
달삯 갱신 — 손님이 없는 자리에서 도는 것

    python services/api/scripts/renew.py            # 무엇을 긁을지만 본다
    python services/api/scripts/renew.py --charge   # 실제로 긁는다

★ 왜 요청 안에서 안 긁는가
  리포트를 여는 길에 카드를 긁으면 두 가지가 어긋납니다 —
  손님이 안 오면 안 걷히고(그건 구독이 아닙니다), 오면 화면이
  결제 응답만큼 멈춥니다. 그래서 밖에서 돕니다.

★ 하루 한 번이면 됩니다.
  주기는 서른 날이고 늦어도 사흘(GRACE_DAYS)은 자격이 열려 있습니다.
  하루 걸러 돌아도 손님은 아무것도 못 느낍니다. 다만 **두 번 돌면
  두 번 긁히지 않는지**가 중요한데, 긁고 나서 period_end 를 옮기므로
  같은 날 다시 돌아도 `due()` 가 거짓이 됩니다.

★ 기본은 **안 긁습니다.** `--charge` 를 붙여야 돕니다. 돈이 오가는
  도구는 손이 미끄러졌을 때 아무 일도 안 일어나는 쪽이 맞습니다.

배포에서 어떻게 도는가는 docs/17 을 보세요.
"""
from __future__ import annotations

import argparse
import logging
import os
import sys
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

import store                                       # noqa: E402
from routers import subscription as sub_mod        # noqa: E402

log = logging.getLogger("renew")


def _fmt(iso):
    return (iso or "")[:16].replace("T", " ")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--charge", action="store_true",
                    help="실제로 긁는다. 안 붙이면 보기만 한다")
    args = ap.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(message)s")
    now = datetime.now(timezone.utc)

    # scan 은 (열쇠, 값) 짝을 돌려줍니다.
    rows = store.scan("sub:")
    if not rows:
        print("걸어 둔 카드가 없소.")
        return 0

    due, ending, dead, live = [], [], [], []
    for _k, s in rows:
        if not s:
            continue
        if s.get("status") == "dead":
            dead.append(s)
        elif sub_mod.due(s, now):
            due.append(s)
        elif s.get("ending"):
            ending.append(s)
        else:
            live.append(s)

    print("걸어 둔 카드 %d  ·  긁을 때가 된 것 %d  ·  그만두기 예약 %d  "
          "·  끝난 것 %d" % (len(rows), len(due), len(ending), len(dead)))

    # ── 그만두기를 눌렀고 기간도 끝난 것 — 열쇠를 버립니다 ──
    retired = 0
    for s in ending:
        ends = sub_mod._at(s.get("period_end"))
        if ends and ends <= now:
            if args.charge:
                sub_mod.retire(s)
            retired += 1
    if retired:
        print("  기간이 끝나 카드 열쇠를 버린 것 %d" % retired)

    if not due:
        print("오늘 긁을 것은 없소.")
        return 0

    ok = fail = 0
    for s in due:
        who = s.get("user_key", "?")
        if not args.charge:
            print("  [보기만] %s  %s원  기간끝 %s  실패 %d"
                  % (who, format(s.get("amount", 0), ","),
                     _fmt(s.get("period_end")), s.get("fails", 0)))
            continue
        r = sub_mod.renew(s, now)
        if r.get("ok"):
            ok += 1
            print("  [긁음]  %s  → 다음 %s" % (who, _fmt(r["period_end"])))
        else:
            fail += 1
            print("  [실패]  %s  %s  (%d번째)"
                  % (who, r.get("reason"), r.get("fails", 0)))

    if args.charge:
        print("긁음 %d · 실패 %d" % (ok, fail))
        if fail:
            # ★ 실패를 조용히 넘기지 않습니다. 실패한 채로 나흘이 지나면
            #   자격이 끊깁니다 — 손님은 왜 안 열리는지 모릅니다.
            print("★ 실패한 건은 사흘 안에 다시 겁니다 (GRACE_DAYS). "
                  "네 번 실패하면 그만 긁고 끊습니다.")
    else:
        print("실제로 긁으려면 --charge 를 붙이시오.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
