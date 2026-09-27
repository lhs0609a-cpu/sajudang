from engine import bank
from engine.calendar import build_chart
from engine.features import build_features


def test_opening_checks_experience_instead_of_inventing_history():
    """
    첫 화면이 **지난 일을 지어내지 않는가.**

    ★ 이 검사는 여태 「물음표로 끝나는가」 로 그것을 재고 있었습니다
      (2026-09-25에 고침). 물음이면 지어낸 것이 아니라는 논리였고, 뜻은
      옳았습니다 — 다만 그 자로 재니 **35줄 전부가 물음**이 되었습니다.

      그 사이 손님이 가장 먼저 보는 글이 **숙제 검사**가 됐습니다 —
      「그대는 돈 계획을 세운 뒤 작게 실행할 한 가지도 정했소?」 「너 이거
      했니?」는 맞히는 게 아니라 안 한 일을 지적하는 것이오. 손님이
      짚었습니다: 「너무 내용만 길고 뭔소리인지 하나도 모르겠어… 이런
      사람이다, 이런 것 때문에 꼬였을 거다, 진짜 헉 소리 나게」 (docs/45).

    ★ 지어내지 않는 길은 둘입니다 — 이제 둘 다 받습니다.

          추측    「발품은 남들보다 더 팔았을 것이오」   ← 손님이 아니라 할 수 있소
          지금    「아닌 자리를 아니라고 끊지 못하오」   ← 셈이 말하는 상태요

      금하는 것은 **지난 일을 단정하는 꼴**입니다 — 「끊지 못했소」
      「접었소」 「잃었소」. 그건 사건이고, 사건은 여덟 글자에 없습니다
      (CLAUDE.md 「지나온 칸에 사건을 지어내기」).
    """
    import re

    #: 지난 일을 **단정**한 꼴. 「~것이오」(추측)는 뺍니다.
    past = re.compile(r"(았|었|였|했|왔|갔|뒀|췄|났)(소|네|오)[.!]?$")
    guess = re.compile(r"것이(오|네|요)[.!]?$|을 것|ㄹ 것")
    #: 첫 화면을 짓는 세 표 — 단정 · 인과 · 재해석. 셋 다 봅니다.
    #  (`STAB` 만 보다가 `EMPTY_SEAT` 에 과거형 아홉 줄이 남았습니다.)
    bad = []
    B = bank.bank()
    for name in ("STAB", "EMPTY_SEAT", "RELIEF"):
        rows = B[name]
        flat = ([(name, el, t) for c, r in rows.items() for el, t in r.items()]
                if name == "STAB" else
                [(name, k, t) for k, t in rows.items()])
        for where, key, text in flat:
            for s in re.split(r'(?<=\.)\s+', text):
                s = s.strip()
                if s and past.search(s) and not guess.search(s):
                    bad.append((where, key, s))
    assert not bad, "첫 화면이 지난 일을 단정하오: %s" % bad[:3]
    assert '자가진단' not in bank.bank()['IGKEY']['편인']['health']


def test_rejection_is_respected_for_every_hook_stage():
    f=build_features(build_chart(1993,11,25,None,0,'F',hour_known=False))
    for concern in bank.bank()['STAB']:
        for misses in (0,3):
            for segment in bank.build_hook(f,concern,misses=misses):
                assert '맞지 않는 해석' in segment['no']
                assert '아직 안 터진' not in segment['no']
                assert segment['statement_id'].endswith(':copy2')
                assert '그럴 줄 알았소' not in segment['yes']


def test_the_hook_crosses_two_axes_at_least_once():
    """
    훅이 축을 **맞붙이는가** — 하나씩 말하고 되풀이하지 않는가.

    ★ 손님이 짚었습니다 (2026-09-25) — 「이 사람에 대해 완벽하게 파악해서
      … 이런 것 때문에 꼬였을 거다, 진짜 헉 소리 나게」. 재 보니 이 집은
      축을 하나씩만 말하고 그것을 한 장에 다섯 번 되풀이했습니다 —
      없는 기운 4.3번 · 겪은 일 3.2번 · 때 3.0번. **교차는 한 번도**
      없었습니다 (docs/45 §0·§9③).

      교차 축 여덟을 3,000명에 대 보니 서로 다른 묶음이 553가지였고
      최다가 1.6%였습니다. 가장 센 것이 「물려받은 것 × 지금 쓰는 힘」
      (50짝 · 어긋남 56%)이오 — `bank.inherit_line`.

    ★ 새 점을 치는 것이 아닙니다. `f.ancestor` 와 `f.flow` 는 이미
      세어져 있었고, 한 번도 맞붙여 보지 않았을 뿐이오.
    """
    import re

    tag = re.compile(r"<[^>]+>")
    for concern in bank.bank()["STAB"]:
        for args in ((1993, 4, 5, 15, 0, "F"), (1982, 11, 8, 3, 40, "M"),
                     (2003, 9, 17, 7, 55, "F")):
            f = build_features(build_chart(*args, hour_known=True))
            got = [s for s in bank.build_hook(f, concern)
                   if 'class="inherit"' in s["html"]]
            assert got, "%s · %s — 교차 줄이 한 번도 안 섰소" % (concern, args[0])
            assert len(got) == 1, (
                "교차가 %d번 섰소 — 한 번이면 됩니다 (되풀이는 희석이오)"
                % len(got))
            # 물려받은 것과 지금 힘을 **둘 다** 대야 교차요.
            body = tag.sub("", got[0]["html"])
            assert "물려받은" in body and f.flow in body, body[:120]


def test_the_inherit_table_covers_every_group():
    """다섯 묶음이 다 차 있어야 50가지 짝이 덮입니다."""
    from engine.constants import TEN_GOD_GROUP
    tbl = bank.bank()["INHERIT"]
    cost = bank.bank()["INHERIT_COST"]
    for group in set(TEN_GOD_GROUP.values()):
        assert group in tbl, "INHERIT 에 %s 가 없소" % group
        assert group in cost, "INHERIT_COST 에 %s 가 없소" % group
        for key in ("got", "same", "off"):
            assert tbl[group].get(key), (group, key)
        assert "{now}" in tbl[group]["off"], (
            "%s · 어긋남 줄에 지금 쓰는 힘을 안 대오" % group)
