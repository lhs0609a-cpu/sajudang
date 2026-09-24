import pytest
from engine.calendar import build_chart
from engine.features import build_features
from engine.editorial import build, ROLES, CONCERNS
from engine import guard


def _concerns():
    """제품이 손님에게 열어 둔 고민 칸."""
    import typing
    from schemas.api import Concern
    return set(typing.get_args(Concern))

@pytest.mark.parametrize('known',[True,False])
def test_all_twenty_perspectives_cover_every_concern(known):
    """고민 칸 수를 **손으로 적지 않습니다** — 제품에서 받습니다.

    여섯이라 적어 두었더니 일곱째 칸(부동산)이 열린 뒤에도 자는 여섯만
    셌습니다. 그 사이 부동산은 스무 명이 같은 물음을 받고 있었소.
    """
    f=build_features(build_chart(1993,11,25,15 if known else None,0,'F',hour_known=known))
    assert len(ROLES)==20 and len(CONCERNS)==len(_concerns())
    questions=set(); scenes=set()
    for lens in ROLES:
        for concern in CONCERNS:
            item=build(f,lens,concern)
            assert item['version']==2 and item['observation']
            assert '맞는 경험이 없다면' in item['boundary']
            for key in ('question','action','scene','observation'):
                assert guard.check(item[key])[0]
            assert 'hour_known' not in item['observation']
            questions.add(item['question']);scenes.add(item['scene'])
    assert len(questions)==20*len(CONCERNS) and len(scenes)==len(CONCERNS)
    assert f.hour_known==known

def test_unrecognized_inputs_do_not_invent_content():
    assert build(None,'missing','money') is None
    assert build(None,'pungun','missing') is None
def test_each_character_and_concern_has_a_distinct_reviewed_question():
    from engine.editorial_questions import QUESTIONS, CONCERN_ORDER
    assert len(QUESTIONS)==20 and set(CONCERN_ORDER)==set(_concerns())
    all_questions=[q for row in QUESTIONS.values() for q in row]
    n=20*len(CONCERN_ORDER)
    assert len(all_questions)==n and len(set(all_questions))==n
    for row in QUESTIONS.values():assert len(row)==len(CONCERN_ORDER)
