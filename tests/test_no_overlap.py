# -*- coding: utf-8 -*-
"""
글자가 겹칠 짜임이 남아 있지 않은가.

★ 손님이 본 것

    절기   입동(立冬) 절입 (그 마디로 넘어가는 시각) 1993-
    (계절이 바뀌는11:07:38:46 기준

  두 글줄이 서로 위에 그려졌다. 까닭 둘이 겹쳤다 —

    · `.calc .r .v { flex: 1 }` 은 min-width:auto 라 안엣것만큼 벌어진다
    · `.gl { white-space: nowrap }` — 문장 길이 풀이가 안 끊긴다

  둘이 만나면 칸이 화면 밖으로 벌어지고 그 자리에 다음 줄이 그려진다.

★ 정적으로 보는 검사다

  실제로 그려 보는 것이 아니라 **겹칠 수 있는 짜임**을 막는다.
  안 겹치는 것을 증명하지는 못한다 — 그건 눈으로 봐야 한다.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import overlap_audit as oa  # noqa: E402


def _scan():
    merged, where = {}, {}
    for f in sorted(oa.CSS.glob("*.css")):
        for sel, body in oa.rules(f.read_text(encoding="utf-8")):
            one = " ".join(body.split())
            for s in (x.strip() for x in sel.split(",")):
                if s:
                    merged.setdefault(s, "")
                    merged[s] += " " + one
                    where.setdefault(s, f.name)
    return merged, where


def test_text_cells_can_shrink():
    """문장이 든 flex 칸은 반드시 줄어들어야 한다."""
    import re
    merged, where = _scan()
    bad = [s for s, one in merged.items()
           if re.search(r"\bflex:\s*(1|auto)\b", one)
           and "min-width" not in one and s not in oa.OK_RIGID]
    assert not bad, "안 줄어드는 칸: %s" % bad


def test_sentences_are_allowed_to_wrap():
    """딱지가 아닌 곳에 nowrap 을 걸면 삐져나가 겹친다."""
    import re
    merged, _ = _scan()
    bad = [s for s, one in merged.items()
           if re.search(r"white-space:\s*nowrap", one)
           and not re.search(r"white-space:\s*normal", one)
           and not any(k in s for k in oa.OK_NOWRAP)]
    assert not bad, "안 끊기는 문장: %s" % bad


def test_gloss_wraps():
    """
    ★ 풀이는 문장이다.

      「(계절이 바뀌는 마디 스물넷 · 넘어가는 시각까지 셉니다)」 는
      딱지가 아니다. 안 끊기게 두면 셈 표를 통째로 벌린다.
    """
    css = (ROOT / "apps" / "web" / "styles" / "overrides.css").read_text(
        encoding="utf-8")
    i = css.rfind(".gl {")
    j = css.rfind("white-space: normal")
    assert j > 0, "풀이가 안 끊긴다"
    assert "margin-right" in css[j - 400:j + 400], \
        "풀이 뒤가 다음 글자에 붙는다"
