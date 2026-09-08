import pytest
from engine.calendar import build_chart
from engine.features import build_features
from engine.editorial import build, ROLES, CONCERNS
from engine import guard

@pytest.mark.parametrize('known',[True,False])
def test_all_twenty_perspectives_cover_six_concerns(known):
    f=build_features(build_chart(1993,11,25,15 if known else None,0,'F',hour_known=known))
    assert len(ROLES)==20 and len(CONCERNS)==6
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
    assert len(questions)==120 and len(scenes)==6
    assert f.hour_known==known

def test_unrecognized_inputs_do_not_invent_content():
    assert build(None,'missing','money') is None
    assert build(None,'pungun','missing') is None
def test_each_character_and_concern_has_a_distinct_reviewed_question():
    from engine.editorial_questions import QUESTIONS, CONCERN_ORDER
    assert len(QUESTIONS)==20 and len(CONCERN_ORDER)==6
    all_questions=[q for row in QUESTIONS.values() for q in row]
    assert len(all_questions)==120 and len(set(all_questions))==120
    for row in QUESTIONS.values():assert len(row)==len(CONCERN_ORDER)
