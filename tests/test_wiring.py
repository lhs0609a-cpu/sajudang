"""
배선 검사 — 명식이 실제로 문장까지 도달하는가, 그리고 감사에서 나온 버그 재발 방지.

여기 있는 테스트는 전부 **실제로 났던 버그**에서 나왔습니다.
지우지 마세요.
"""
from __future__ import annotations

import random
from datetime import date, timedelta

import pytest

import store
from engine import bank
from engine.calendar import build_chart
from engine.constants import ELEMENT_OF_GAN, HIDDEN, ten_god
from engine.features import build_features
from engine.report import build_report


def people(n=200, seed=13, hour_known=True):
    rnd = random.Random(seed)
    out = []
    for _ in range(n):
        c = build_chart(rnd.randint(1950, 2010), rnd.randint(1, 12),
                        rnd.randint(1, 28),
                        rnd.randint(0, 23) if hour_known else None,
                        rnd.randint(0, 59) if hour_known else None,
                        rnd.choice("FM"), hour_known)
        out.append((c, build_features(c)))
    return out


# ══════════════════════════════════════════════════════════
# 1. 대운 순행/역행 — 리포트가 거짓말하지 않는가
#    (버그: start_age 증가로 방향을 추정해 항상 '순행' 이라고 적었다.
#     300건 중 152건이 틀렸다.)
# ══════════════════════════════════════════════════════════
def test_features_carry_daeun_direction():
    for c, f in people(60):
        assert f.forward == c.forward


def test_report_states_the_real_daeun_direction():
    wrong = 0
    for c, f in people(80):
        rep = build_report(f, "cid", "pungun", "all", "love")
        cut = next(x for x in rep["cuts"] if x["id"] == "daeun_map")
        said_forward = "순행" in cut["source"]
        if said_forward != c.forward:
            wrong += 1
    assert wrong == 0, "리포트가 대운 방향을 %d건 틀리게 적었습니다" % wrong


def test_both_directions_actually_occur():
    fwd = [c.forward for c, _ in people(200)]
    assert 0 < sum(fwd) < len(fwd), "순행/역행이 한쪽으로만 나옵니다"


# ══════════════════════════════════════════════════════════
# 2. 훅 캐시 키 — 남의 이름이 새지 않는가
#    (버그: chart_id 는 생년월일시 해시라 같은 날 같은 시에 태어난 사람끼리
#     공유된다. 키에 이름이 없어 뒷사람이 앞사람 이름이 박힌 훅을 받았다.)
# ══════════════════════════════════════════════════════════
def test_hook_cache_key_separates_names():
    a = store.k_hook("chart", "love", "INFP", "pungun", "서연")
    b = store.k_hook("chart", "love", "INFP", "pungun", "민준")
    c = store.k_hook("chart", "love", "INFP", "pungun", "")
    assert a != b and a != c and b != c


def test_hook_cache_key_stable_for_same_name():
    assert (store.k_hook("chart", "love", "INFP", "pungun", "서연")
            == store.k_hook("chart", "love", "INFP", "pungun", " 서연 "))


def test_name_actually_reaches_the_hook():
    _, f = people(1)[0]
    assert "서연" in bank.build_hook(f, "love", name="서연")[0]["html"]
    assert "서연" not in bank.build_hook(f, "love", name="민준")[0]["html"]


# ══════════════════════════════════════════════════════════
# 3. 대운 진입 전 — 들어가지도 않은 대운을 '지금' 이라고 말하지 않는가
# ══════════════════════════════════════════════════════════
def test_daeun_started_flag():
    for c, f in people(60):
        assert f.daeun_started == (f.age >= f.daeun[0]["start_age"])


def test_report_does_not_claim_an_unentered_daeun():
    # 대운수가 큰 아이를 만든다 (올해 태어난 사람은 어느 대운에도 안 들어갔다)
    this_year = date.today().year
    c = build_chart(this_year, 6, 15, 10, 0, "F")
    f = build_features(c)
    assert f.daeun_started is False
    rep = build_report(f, "cid", "pungun", "all", "love")
    cut = next(x for x in rep["cuts"] if x["id"] == "daeun_now")
    assert "아직 첫 대운에 들지 않았소" in cut["html"]
    assert "지금은" not in cut["html"]


# ══════════════════════════════════════════════════════════
# 4. 동률 처리 — 임의로 고르고 단정하지 않는가
#    (실측: 주도 십신 43%, 최약 오행 8.8% 가 동률)
# ══════════════════════════════════════════════════════════
def test_top_ten_god_tie_flag_is_honest():
    for c, f in people(120):
        mx = max(f.ten_gods.values())
        tied = sum(1 for v in f.ten_gods.values() if v == mx) > 1
        assert f.top_ten_god_tied == tied


def test_top_ten_god_prefers_the_month_branch_on_a_tie():
    """동률이면 월령(월지 본기)의 십신이 이긴다 — 임의 순서가 아니라."""
    checked = 0
    for c, f in people(300):
        if not f.top_ten_god_tied:
            continue
        mx = max(f.ten_gods.values())
        winners = {k for k, v in f.ten_gods.items() if v == mx}
        wol = ten_god(HIDDEN[c.month_pillar.ji][0][0], f.day_gan)
        if wol in winners:
            assert f.top_ten_god == wol
            checked += 1
    assert checked > 0, "월령이 후보에 든 동률 사례가 하나도 없었습니다"


def test_top_ten_god_is_always_a_max():
    for c, f in people(150):
        assert f.ten_gods[f.top_ten_god] == max(f.ten_gods.values())


def test_weak_elements_lists_every_tie():
    for c, f in people(200):
        mn = min(f.elements.values())
        assert set(f.weak_els) == {k for k, v in f.elements.items() if v == mn}
        assert f.weak_el == f.weak_els[0]


def test_report_mentions_every_tied_weak_element():
    found = False
    for c, f in people(300):
        if len(f.weak_els) <= 1:
            continue
        rep = build_report(f, "cid", "pungun", "free", "love")
        cut = next(x for x in rep["cuts"] if x["id"] == "lack")
        assert "둘 다 없는 자리요" in cut["html"]
        found = True
        break
    assert found, "최약 오행 동률 사례를 찾지 못했습니다"


# ══════════════════════════════════════════════════════════
# 5. 배선 — 명식이 바뀌면 문장이 바뀌는가
# ══════════════════════════════════════════════════════════
# 문장 선택에 실제로 쓰이는 값. 일간과 계절이 여기 들어오면서
# 같은 문장을 받는 사람 수가 크게 줄었습니다 (아래 테스트 참고).
HOOK_KEYS = ("weak_el", "top_ten_god", "strength", "flow", "day_gan")

import re as _re
_nums = _re.compile(r"[0-9.]+")


def _sentences(f, concern="love"):
    """숫자를 뺀 문장 — '어떤 문장이 뽑혔는가' 만 남긴다."""
    return tuple(_nums.sub("#", s["html"]) for s in bank.build_hook(f, concern))


def _hook_key(f):
    return tuple(getattr(f, x) for x in HOOK_KEYS) + (bank.born_season(f),)


def test_bank_sentence_choice_is_fully_determined_by_seven_values():
    """
    **어떤 문장이 뽑히는가** 는 이 일곱 값으로 완전히 결정된다.
        고민 · 약오행 · 주도십신 · 신강약 · 흐름 · 일간 · 태어난 계절

    일지·대운·용신·신살은 아직 문장 '선택' 에 관여하지 않는다.
    축을 더 넣어 개인화를 깊게 하면 이 테스트가 깨진다 — 깨지는 게 진전이다.
    """
    seen = {}
    for c, f in people(400):
        k = _hook_key(f)
        ids = tuple(s["statement_id"] for s in bank.build_hook(f, "love"))
        if k in seen:
            assert seen[k] == ids, "같은 키인데 문장 id 가 다릅니다: %s" % (k,)
        else:
            seen[k] = ids


def test_day_master_changes_the_first_thing_they_read():
    """
    ★ 0단은 사람이 맨 처음 읽는 문장입니다.

    전에는 일간이 근거 줄에만 적히고 본문에는 안 쓰였습니다. 일간이
    다른 사람이 첫 화면에서 같은 말을 듣고 있었습니다.
    """
    bodies = {}
    for c, f in people(400):
        seg0 = bank.build_hook(f, "love")[0]
        bodies.setdefault(f.day_gan, set()).add(_nums.sub("#", seg0["html"]))
    assert len(bodies) >= 8, "일간 표본이 모자랍니다: %s" % sorted(bodies)
    # 일간이 다르면 0단 문장도 달라야 한다
    one_per_gan = {g: sorted(v)[0] for g, v in bodies.items()}
    assert len(set(one_per_gan.values())) == len(one_per_gan),         "일간이 다른데 0단이 같습니다"


def test_season_changes_the_sequence_stage():
    seasons = {}
    for c, f in people(400):
        seg = [s for s in bank.build_hook(f, "love") if s["stage"] == "2"][0]
        seasons.setdefault(bank.born_season(f), set()).add(
            _nums.sub("#", seg["html"]))
    assert set(seasons) == {"봄", "여름", "가을", "겨울"}, sorted(seasons)
    first = {k: sorted(v)[0] for k, v in seasons.items()}
    assert len(set(first.values())) == 4, "계절이 다른데 2단이 같습니다"


def test_adding_axes_actually_reduced_shared_hooks():
    """
    축을 늘린 것이 실제로 효과가 있었는가 — 숫자로 붙들어 둡니다.
    이 값이 다시 나빠지면(같은 문장을 받는 사람이 늘면) 여기가 잡습니다.
    """
    import hashlib
    from collections import Counter
    seen = Counter()
    n = 0
    for c, f in people(600):
        body = "|".join(_nums.sub("#", s["html"])
                        for s in bank.build_hook(f, "love"))
        seen[hashlib.sha256(body.encode()).hexdigest()] += 1
        n += 1
    alone = sum(1 for v in seen.values() if v == 1)
    ratio = alone / len(seen)
    assert ratio >= 0.75, "혼자만 받는 훅이 %.1f%% 로 떨어졌습니다" % (100 * ratio)


def test_rendered_hook_still_carries_the_persons_own_numbers():
    """
    뽑힌 문장이 같아도, 그 문장을 감싸는 근거에는 그 사람 값이 실려야 한다.
    (일간 오행 · 흐름 오행 · 오행 수치 · 십신 개수 · 신강약 점수)

    같은 키를 가진 두 사람에게서 실제로 근거가 갈리는 사례가 나와야 한다.
    안 나오면 명식이 화면에 전혀 실리지 않는다는 뜻이다.
    """
    seen = {}
    differed = 0
    for c, f in people(400):
        k = tuple(getattr(f, x) for x in HOOK_KEYS)
        raw = tuple(s["html"] + (s["source"] or "")
                    for s in bank.build_hook(f, "love"))
        if k in seen and seen[k] != raw:
            differed += 1
        seen.setdefault(k, raw)
    assert differed > 0, "모든 근거가 똑같습니다 — 명식이 안 실린 것입니다"


def test_day_stem_reaches_the_screen():
    """일간(그 사람 자신)은 최소한 근거 칩과 3단 설명에는 나와야 한다."""
    _, f = people(1)[0]
    segs = bank.build_hook(f, "love")
    joined = " ".join((s["html"] + (s["source"] or "")) for s in segs)
    assert f.day_gan in joined or ELEMENT_OF_GAN[f.day_gan] + "일간" in joined


def test_different_charts_can_share_a_hook():
    """
    8글자가 달라도 네 값이 같으면 훅이 같아진다.
    개인화의 한계를 드러내는 테스트다. 통과한다고 좋은 게 아니라,
    이 사실을 알고 있자는 뜻이다.
    """
    seen = {}
    collisions = 0
    for c, f in people(400):
        k = tuple(getattr(f, x) for x in HOOK_KEYS)
        gz = tuple(p.gz for p in c.pillars)
        if k in seen and seen[k] != gz:
            collisions += 1
        seen.setdefault(k, gz)
    # 8글자가 다른데 뽑히는 문장이 같은 사람이 실제로 존재한다
    assert collisions > 0
    # 문서화용 — 400명 중 몇 명이 남의 훅과 겹치는가
    assert collisions < 400


def test_hour_changes_the_reading():
    """시주를 넣고 빼면 결과가 달라진다 — 그러니 '모르오' 를 함부로 권하면 안 된다."""
    changed = 0
    rnd = random.Random(21)
    for _ in range(60):
        y, m, d = rnd.randint(1960, 2005), rnd.randint(1, 12), rnd.randint(1, 28)
        fk = build_features(build_chart(y, m, d, 14, 0, "F", True))
        fu = build_features(build_chart(y, m, d, None, None, "F", False))
        if tuple(getattr(fk, x) for x in HOOK_KEYS) != \
           tuple(getattr(fu, x) for x in HOOK_KEYS):
            changed += 1
    assert changed > 0


# ══════════════════════════════════════════════════════════
# 6. 시각 미상 — 없는 것을 채우지 않는가
# ══════════════════════════════════════════════════════════
def test_hour_unknown_never_invents_a_pillar():
    for c, f in people(40, seed=5, hour_known=False):
        assert len(f.pillars) == 3
        assert all(p["label"] != "시주" for p in f.pillars)
        assert f.correction["hour_used"] is False
        assert sum(f.ten_gods.values()) == 5
