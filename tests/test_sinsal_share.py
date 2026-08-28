"""
신살 · 궁위 · 분석지 · 공유 테스트.

여기서 지키는 것
    · 신살 표가 유파 확정값 그대로인가 (손으로 검산한 값과 대조)
    · 공유 링크에 생년월일시가 절대 새지 않는가
    · 분석지가 흐린 부분(단서)을 숨기지 않는가
    · 유입 화면이 적중률 같은 말을 쓰지 않는가
"""
from __future__ import annotations

import json
import random

import pytest
from fastapi.testclient import TestClient

import store
from engine import guard, sinsal
from engine.calendar import build_chart
from engine.features import build_features
from engine.summary import build_summary, share_payload
from main import app

BIRTH = {"year": 1993, "month": 5, "day": 15, "hour": 10, "minute": 20,
         "hour_known": True, "sex": "F", "birth_city": "서울"}


@pytest.fixture()
def client():
    store.clear_all()
    return TestClient(app)


@pytest.fixture(scope="module")
def f():
    return build_features(build_chart(1993, 5, 15, 10, 20, "F"))


# ══════════════════════════════════════════════════════════
# 신살 — 손으로 검산한 값과 대조
# ══════════════════════════════════════════════════════════
def test_cheoneul_table_matches_the_classic_verse():
    """가결: 甲戊庚牛羊 乙己鼠猴鄉 丙丁猪雞位 壬癸兔蛇藏 六辛逢馬虎"""
    assert sinsal.CHEONEUL["甲"] == sinsal.CHEONEUL["戊"] == sinsal.CHEONEUL["庚"] == "丑未"
    assert sinsal.CHEONEUL["乙"] == sinsal.CHEONEUL["己"] == "子申"
    assert sinsal.CHEONEUL["丙"] == sinsal.CHEONEUL["丁"] == "亥酉"
    assert sinsal.CHEONEUL["壬"] == sinsal.CHEONEUL["癸"] == "卯巳"
    assert sinsal.CHEONEUL["辛"] == "寅午"


def test_gongmang_is_the_empty_pair_of_the_decade():
    # 甲子순 → 戌亥 / 甲戌순 → 申酉 / 甲寅순 → 子丑
    assert sinsal.gongmang("甲", "子") == "戌亥"
    assert sinsal.gongmang("甲", "戌") == "申酉"
    assert sinsal.gongmang("甲", "寅") == "子丑"
    assert sinsal.gongmang("丙", "申") == "辰巳"


def test_gongmang_pair_is_never_in_the_same_decade():
    for g in "甲乙丙丁戊己庚辛壬癸":
        for j in "子丑寅卯辰巳午未申酉戌亥":
            # 60갑자에 없는 조합은 건너뛴다
            if ("甲乙丙丁戊己庚辛壬癸".index(g) % 2) != ("子丑寅卯辰巳午未申酉戌亥".index(j) % 2):
                continue
            gm = sinsal.gongmang(g, j)
            assert len(gm) == 2 and j not in gm


def test_known_chart_sinsal(f):
    """1993-05-15 10:20 여 · 癸酉 丁巳 丙申 癸巳 (일간 丙)"""
    keys = {s["key"] for s in f.sinsal}
    assert "cheoneul" in keys      # 丙 → 亥酉, 년지 酉
    assert "taegeuk" in keys       # 丙 → 卯酉, 년지 酉
    assert "munchang" in keys      # 丙 → 申, 일지 申
    assert "amrok" in keys         # 丙 → 申, 일지 申
    assert f.gongmang == "辰巳"


def test_sinsal_kinds_are_labelled(f):
    for s in f.sinsal:
        assert s["kind"] in ("길신", "살", "특수")
        assert s["at"] and all(a in ("년주", "월주", "일주", "시주") for a in s["at"])


def test_helpers_point_at_a_real_pillar(f):
    for h in f.helpers:
        assert h["pillar"] in ("년주", "월주", "일주", "시주")
        assert h["who"] and h["kind"]


def test_ancestor_reads_the_year_pillar(f):
    a = f.ancestor
    assert a["pillar"] == f.pillars[0]["gz"]
    assert a["stance"] in ("돕는 쪽", "짐이 되는 쪽", "크게 관여하지 않는 쪽")


def test_palaces_mark_the_missing_hour():
    fu = build_features(build_chart(1986, 6, 21, None, None, "F", hour_known=False))
    hour = next(p for p in fu.palaces if p["pillar"] == "시주")
    assert hour.get("unknown") is True
    assert hour["gz"] is None


def test_every_stem_and_branch_produces_sinsal_without_crashing():
    rnd = random.Random(4)
    for _ in range(300):
        c = build_chart(rnd.randint(1930, 2060), rnd.randint(1, 12),
                        rnd.randint(1, 28), rnd.randint(0, 23), 0,
                        rnd.choice("FM"))
        assert isinstance(sinsal.find(c), list)


# ══════════════════════════════════════════════════════════
# 가드 — 명리 용어를 잡아먹지 않는가
# ══════════════════════════════════════════════════════════
@pytest.mark.parametrize("term", ["암록", "암록(暗祿)", "청암거사", "천을귀인",
                                  "태극귀인", "백호대살", "괴강", "공망"])
def test_guard_lets_myeongri_terms_through(term):
    ok, hits = guard.check(term)
    assert ok, "%s 이 가드에 걸립니다: %s" % (term, hits)


@pytest.mark.parametrize("bad", ["위암 진단이 나오오", "폐암이 오오",
                                 "암에 걸리오", "당뇨가 오오", "치매가 오오"])
def test_guard_still_blocks_real_disease_claims(bad):
    ok, _ = guard.check(bad)
    assert not ok


def test_all_seed_text_passes_guard():
    """시드 문장이 가드에 걸리면 화면에서 통째로 사라진다. 실제로 그런 적 있다."""
    from pathlib import Path
    seed = Path(__file__).resolve().parents[1] / "seed"

    def walk(o):
        if isinstance(o, str):
            yield o
        elif isinstance(o, dict):
            for v in o.values():
                yield from walk(v)
        elif isinstance(o, list):
            for v in o:
                yield from walk(v)

    bad = []
    for name in ("bank", "sinsal", "lenses", "meta", "ilgan"):
        d = json.loads((seed / (name + ".json")).read_text("utf-8"))
        for t in walk(d):
            ok, hits = guard.check(t)
            if not ok:
                bad.append((name, t[:50], hits))
    assert not bad, bad


# ══════════════════════════════════════════════════════════
# 분석지
# ══════════════════════════════════════════════════════════
def test_summary_has_every_section(f):
    sm = build_summary(None, f, "love", "INFP", "pungun", "서연")
    ids = [s["id"] for s in sm["sections"]]
    assert ids == ["pillars", "balance", "sequence", "when", "helper", "root", "need"]
    assert len(sm["three_lines"]) == 3
    assert sm["headline"]


def test_summary_never_hides_the_caveats():
    """때를 모르면 그 사실이 분석지에 반드시 남아야 한다."""
    fu = build_features(build_chart(1986, 6, 21, None, None, "F", hour_known=False))
    sm = build_summary(None, fu, "work")
    joined = " ".join(sm["caveats"])
    assert "세 기둥" in joined
    assert any("무엇이 일어난다고 말하지 않" in c for c in sm["caveats"])


def test_summary_passes_guard(f):
    sm = build_summary(None, f, "love", "INFP")
    for sec in sm["sections"]:
        ok, hits = guard.check(sec["html"])
        assert ok, (sec["id"], hits)


# ══════════════════════════════════════════════════════════
# 공유 — 생일이 새면 안 된다
# ══════════════════════════════════════════════════════════
def test_share_payload_carries_no_birth_data(f):
    sm = build_summary(None, f, "love", "INFP", "pungun", "서연")
    for reveal in ("full", "light"):
        p = share_payload(sm, reveal)
        blob = json.dumps(p, ensure_ascii=False)
        for leak in ("1993", "05-15", "서울", "10:20", "birth"):
            assert leak not in blob, "%s 가 공유 payload 에 있습니다" % leak
        assert "correction" not in p


def test_light_share_hides_the_pillars(f):
    sm = build_summary(None, f, "love")
    light = share_payload(sm, "light")
    full = share_payload(sm, "full")
    assert "pillars" not in light
    assert "pillars" in full


def test_share_endpoint_roundtrip(client):
    cid = client.post("/v1/chart", json=BIRTH).json()["chart_id"]
    r = client.post("/v1/share", json={
        "chart_id": cid, "concern": "love", "name": "서연",
        "from_name": "서연", "reveal": "full"}).json()
    assert r["path"].startswith("/s/")
    assert "생년월일" in " ".join(r["excludes"])

    got = client.get("/v1/share/" + r["token"]).json()
    blob = json.dumps(got, ensure_ascii=False)
    for leak in ("1993", "05-15", "서울"):
        assert leak not in blob
    assert got["from_name"] == "서연"


def test_share_counts_opens(client):
    cid = client.post("/v1/chart", json=BIRTH).json()["chart_id"]
    tok = client.post("/v1/share", json={
        "chart_id": cid, "concern": "love"}).json()["token"]
    assert client.post("/v1/share/%s/open" % tok).json()["views"] == 1
    assert client.post("/v1/share/%s/open" % tok).json()["views"] == 2


def test_unknown_share_token_is_404(client):
    assert client.get("/v1/share/nope").status_code == 404
    assert client.post("/v1/share/nope/open").status_code == 404


def test_share_rejects_bad_reveal(client):
    cid = client.post("/v1/chart", json=BIRTH).json()["chart_id"]
    r = client.post("/v1/share", json={
        "chart_id": cid, "concern": "love", "reveal": "everything"})
    assert r.status_code == 400


# ══════════════════════════════════════════════════════════
# 유입 화면 — 의심을 이기려고 거짓을 보태지 않는가
# ══════════════════════════════════════════════════════════
def test_referral_landing_makes_no_accuracy_claim():
    """
    ★ 이 검사가 문장의 **위치**를 보고 있었습니다.

      여섯 문답이 `s/[token]` 안에 갇혀 있던 시절의 검사입니다. 그 문장은
      이 서비스에서 가장 잘 쓰인 카피인데 **공유 링크로 온 사람만** 봤고,
      검색·광고로 직접 들어온 사람은 한 번도 못 만났습니다. 그래서
      components/Doubts.tsx 로 빼서 골목(a1)과 글자 서는 동안(a6)에도
      씁니다.

      검사는 자리를 따라갑니다 — 다만 **유입 화면이 그것을 실제로 그리는지**
      도 같이 봅니다. 안 그러면 컴포넌트만 있고 화면에는 안 걸린 상태를
      통과시킵니다.
    """
    from pathlib import Path
    root = Path(__file__).resolve().parents[1] / "apps" / "web"
    d = root / "app" / "s" / "[token]"
    landing = chr(10).join(f.read_text(encoding="utf-8")
                        for f in sorted(d.glob("*.tsx")))
    doubts = (root / "components" / "Doubts.tsx").read_text(encoding="utf-8")
    src = landing + chr(10) + doubts

    for banned in ("적중률", "과학적", "통계학", "입증", "보장"):
        assert banned not in src or "쓰지 않" in src, banned
    # 의심 항목이 실제로 들어 있는가
    assert "맞히는 집이 아니라" in src
    assert "127.5" in src
    assert "100건" in src
    # 그리고 유입 화면이 그것을 **그리는가**
    assert "<Doubts" in landing, "여섯 문답이 유입 화면에 안 걸려 있습니다"


def test_the_doubts_reach_people_who_came_in_directly():
    """
    ★ 골목(a1)에서도 이 여섯 문답을 만나야 합니다.

      전에는 검색·광고로 직접 들어온 사람이 의심을 안은 채 일곱 화면을
      통과해야 했습니다. 가장 센 설득 자산이 그 사람들에게만 안 보였습니다.
    """
    from pathlib import Path
    root = Path(__file__).resolve().parents[1] / "apps" / "web"
    entry = (root / "app" / "page.tsx").read_text(encoding="utf-8")
    assert "<Doubts" in entry, "직접 들어온 사람은 여섯 문답을 못 봅니다"
