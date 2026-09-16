# -*- coding: utf-8 -*-
"""강조 넷이 **어느 화면에** 걸려 있는가.

    python tools/skim_where.py

★ 손님이 시킨 것

  "사람들이 전체 글 다 안 읽을거니까 중요한 워딩이나 그런것들 밑줄치고,
   강조표시해주고 그것만 읽어도 전체적으로 다 이해가 되게끔 해."

  `engine/skim` 이 그걸 합니다 — 굵게 · 형광펜 · 밑줄 · 수.
  이 자는 그 층이 **어디까지 갔는지**만 봅니다. 만들어 놓고 한
  자리에만 걸어 두면, 나머지 화면은 크기가 하나뿐인 글입니다.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services" / "api"))
sys.path.insert(0, str(ROOT / "tools"))

from engine import dramaturgy as D          # noqa: E402
from engine import screenscan as SS         # noqa: E402

MARKS = (
    ("굵게", re.compile(r"<b[ >]")),
    ("형광펜", re.compile(r"<mark[ >]")),
    ("밑줄", re.compile(r"<u[ >]")),
    ("수", re.compile(r'class="nu[" ]')),
)


def main() -> int:
    # ★ 화면 글은 **태그를 걷어낸 뒤**라 여기서 굵게를 못 셉니다.
    #   화면이 제 손으로 쓴 굵은 글씨는 `screenscan` 이 이미 세어
    #   자리표에 담아 둡니다(여섯째 칸). 그걸 빌려 씁니다 — 안 그러면
    #   「a1 은 굵게 0」 이라는 거짓말이 나옵니다.
    pairs = dict(SS._screens())
    text = {k: v[0] for k, v in pairs.items()}
    own_b = {k: (v[5] if len(v) > 5 else 0) for k, v in pairs.items()}
    # ★ 형광펜·밑줄도 같은 까닭으로 **원문에서** 셉니다.
    #   화면 글은 태그를 걷어낸 뒤라, 여기서 세면 손으로 칠한 것이
    #   통째로 0 으로 나옵니다 — 굵게에서 한 번 겪은 자리요.
    import give_take as GT
    raw = GT.raw_chunks()
    own = {k: (len(re.findall(r"<mark[ >]", v)),
               len(re.findall(r"<u[ >]", v))) for k, v in raw.items()}
    eng = SS._engine_text()
    for sid, html in eng.items():
        text[sid] = (SS.wrap_engine(text.get(sid, ""), html)
                     if sid in SS.ENGINE_MID
                     else html + chr(10) + text.get(sid, ""))
    print("=" * 74)
    print("  강조 넷이 어느 화면에 걸려 있는가")
    print("=" * 74)
    print("  %-5s %-10s %6s %6s %6s %6s %6s   %s"
          % ("화면", "이름", "자", "굵게", "형광펜", "밑줄", "수", ""))
    thin = []
    for sid in SS.KO:
        if sid not in text:
            continue
        h = text[sid]
        n = len(D.plain(h))
        got = [len(rx.findall(h)) for _, rx in MARKS]
        got[0] += own_b.get(sid, 0)      # 화면이 제 손으로 쓴 굵은 글씨
        got[1] += own.get(sid, (0, 0))[0]
        got[2] += own.get(sid, (0, 0))[1]
        note = ""
        if n > 300 and got[1] == 0:
            note = "← 형광펜 없음"
            thin.append(sid)
        print("  %-5s %-10s %6d %6d %6d %6d %6d   %s"
              % (sid, SS.KO[sid][:10], n, got[0], got[1], got[2], got[3], note))
    print()
    print("-" * 74)
    if thin:
        print("  ★ 형광펜이 한 줄도 없는 자리: %s" % " · ".join(thin))
        print("     훑어읽는 손님에게 이 화면은 **크기가 하나뿐인 글**이오.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
