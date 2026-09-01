"""
퍼널을 본다 — 어디서 나가는가.

    python tools/funnel.py                       # 실서버
    python tools/funnel.py http://localhost:8000 # 로컬

    FUNNEL_KEY 환경변수가 있어야 합니다. 없으면 서버가 막습니다.
    (퍼널 숫자는 영업 정보라 열어 두지 않습니다)

읽는 법
    직전대비   바로 앞 화면에서 몇 %가 넘어왔는가 — 여기가 낮으면 그 화면이 문제
    첫화면대비 처음 온 사람 중 몇 %가 여기까지 왔는가
    이탈       그 화면에서 몇 명을 잃었는가 — 절대수. 고칠 순서를 여기서 정합니다
"""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request

BASE = (sys.argv[1] if len(sys.argv) > 1
        else os.getenv("API_BASE", "https://sajudang-api.fly.dev")).rstrip("/")
KEY = os.getenv("FUNNEL_KEY", "").strip()

BAR = "█"


def fetch() -> dict:
    req = urllib.request.Request(BASE + "/v1/funnel",
                                 headers={"X-Funnel-Key": KEY})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.load(r)


def main() -> int:
    if not KEY:
        print("FUNNEL_KEY 가 없습니다.")
        print()
        print("  서버에 걸기:   fly secrets set FUNNEL_KEY=아무거나긴문자열")
        print("  여기서 쓰기:   $env:FUNNEL_KEY='같은문자열'")
        return 1
    try:
        f = fetch()
    except urllib.error.HTTPError as e:
        if e.code == 401:
            print("열쇠가 맞지 않습니다. 서버에 건 FUNNEL_KEY 와 같은지 보세요.")
        elif e.code == 503:
            print("서버에 FUNNEL_KEY 가 안 걸려 있습니다.")
            print("  fly secrets set FUNNEL_KEY=아무거나긴문자열")
        else:
            print("HTTP %s" % e.code)
        return 1
    except Exception as e:                      # noqa: BLE001
        print("못 불러왔습니다: %s" % e)
        return 1

    steps = f["steps"]
    top = steps[0]["sessions"] if steps else 0
    print("=" * 72)
    print("  성신당 퍼널   %s" % BASE)
    print("  사건 %s건 · 사람 %s명" % (
        format(f["total_events"], ","), format(f["sessions"], ",")))
    print("=" * 72)

    if not top:
        print()
        print("  아직 아무도 안 왔습니다. 숫자가 쌓이면 여기가 채워집니다.")
        return 0

    print()
    print("  %-4s %-20s %6s %8s %9s %6s" %
          ("화면", "", "사람", "직전대비", "첫화면대비", "이탈"))
    print("  " + "-" * 68)
    worst = None
    for st in steps:
        w = int(round(28.0 * st["sessions"] / top))
        prev = st["from_prev"]
        print("  %-4s %-20s %6d %7s%% %8s%% %6s  %s" % (
            st["screen"], st["label"], st["sessions"],
            prev if prev is not None else "  -",
            st["from_top"] if st["from_top"] is not None else "  -",
            st["lost"] if st["lost"] is not None else "-",
            BAR * w))
        if st["lost"] and (worst is None or st["lost"] > worst["lost"]):
            worst = st

    if worst:
        print()
        print("  ★ 가장 많이 잃는 자리 — %s %s   %d명 (직전대비 %s%%)"
              % (worst["screen"], worst["label"], worst["lost"],
                 worst["from_prev"]))
        print("    여기부터 고치는 게 순서입니다.")

    hook = f.get("hook") or []
    if hook:
        print()
        print("  훅 단별 — 초반이 어디서 끊기는가")
        print("  %-4s %6s %6s %9s %9s" % ("단", "보임", "답함", "응답률", "그렇소"))
        print("  " + "-" * 40)
        for h in hook:
            print("  %-4s %6d %6d %8s%% %8s%%" % (
                h["stage"], h["shown"], h["answered"],
                h["answer_rate"] if h["answer_rate"] is not None else "  -",
                h["yes_rate"] if h["yes_rate"] is not None else "  -"))
        print()
        print("  응답률이 낮은 단 = 거기서 창을 닫습니다.")
        print("  '그렇소' 가 낮은 단 = 안 맞는 문장입니다. 둘은 고치는 법이 다릅니다.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
