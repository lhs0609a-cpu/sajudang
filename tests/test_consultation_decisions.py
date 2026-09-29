"""Paid-value regressions: changed answers must change advice, not just labels."""
from datetime import date
from itertools import product

import pytest

from engine import character_consultation as cc, consultation, guard
from engine.consultation_decisions import READINGS, ACTIONS
from engine.calendar import build_chart
from engine.features import build_features
from engine.practice import build
from engine.report import build_report


@pytest.mark.parametrize('lens_id', cc.INTERVIEWS)
def test_every_answer_has_distinct_substantive_advice(lens_id):
    row = cc.INTERVIEWS[lens_id]
    assert len(READINGS[lens_id]) == len(row[2])
    assert len(ACTIONS[lens_id]) == len(row[4])
    readings, actions, reviews = set(), set(), set()
    for fourth, fifth in product(row[2], row[4]):
        topic = {'choice4': fourth['id'], 'choice5': fifth['id']}
        result = cc.enrich_practice(build('work'), lens_id, topic)
        readings.add(result['specialist_verdict'])
        # Rest preference intentionally overrides all activity choices.
        if lens_id != 'dongja' or fourth['id'] == 'a':
            actions.add(result['specialist_action'])
            reviews.add(result['specialist_review'])
        for field in ('specialist_verdict', 'specialist_action', 'specialist_review'):
            assert guard.check(result[field])[0], (lens_id, topic, field)
            assert len(result[field]) >= 20
        assert result['steps'][1] == result['specialist_action']
        assert result['steps'][2] == result['specialist_review']
        assert '사주 계산으로 확인한 사실이 아니오' in result['source']
    assert len(readings) == len(row[2])
    assert len(actions) == len(row[4])
    assert len(reviews) == len(row[4])


def test_no_contact_and_rest_are_not_undermined_by_generic_exercises():
    blocked = cc.enrich_practice(build('love'), 'yeondam', {'choice4':'d', 'choice5':'e'})
    assert '다른 계정이나 지인' in blocked['specialist_action']
    assert all('연락이 없어서 서운했어' not in line for line in blocked['steps'])
    rest = cc.enrich_practice(build('work'), 'dongja', {'choice4':'d', 'choice5':'a'})
    assert '쉬는 것으로' in rest['specialist_action']
    assert '한 통만 보내시오' not in ' '.join(rest['steps'])


def test_positive_answers_do_not_force_a_problem():
    solved = cc.enrich_practice(build('work'), 'eunbyeol', {'choice4':'a', 'choice5':'a'})
    assert '유지' in solved['specialist_action']
    assert '반대로 행동할 필요는 없소' in solved['specialist_review']
    stable = cc.enrich_practice(build('work'), 'nopa', {'choice4':'a', 'choice5':'e'})
    assert '끝낼 필요는 없소' in stable['specialist_review']


@pytest.mark.parametrize('invalid', ['z', '', '<script>', None, 3])
def test_unknown_answer_cannot_select_a_branch(invalid):
    with pytest.raises(cc.CharacterConsultationError):
        cc.render('pungun', {'choice4':invalid, 'choice5':'a'})


@pytest.fixture(scope='module')
def features():
    return build_features(build_chart(1993, 11, 25, None, None, 'F', hour_known=False),
                          as_of=date(2026, 9, 29))


@pytest.mark.parametrize('lens_id', cc.INTERVIEWS)
def test_same_decision_reaches_brief_paid_method_and_practice(features, lens_id):
    row = cc.INTERVIEWS[lens_id]
    topic = {'choice4':row[2][-1]['id'], 'choice5':row[4][-1]['id']}
    result = cc.enrich_practice(build('work'), lens_id, topic)
    brief = cc.brief(lens_id, topic)['html']
    method = consultation.render(lens_id, 'work', features, topic)
    for field in ('specialist_verdict', 'specialist_action'):
        assert result[field] in brief
        assert result[field] in method
    assert result['specialist_review'] in method
    assert '그대의 답으로 마무리하시오' not in method


def test_mbti_does_not_append_conflicting_tasks(features):
    topic = {'choice':'a','choice2':'a','choice3':'a','choice4':'d','choice5':'e'}
    report = build_report(features, 'decision-test', 'yeondam', 'all', 'love',
                          axis4='INFP', extras={'topic':topic})
    assert report['practice']['version'] == 4
    assert 'mbti' not in report['practice']
    assert report['practice']['specialist_review'] == report['practice']['steps'][2]
    assert any('답변으로 좁힌 첫 해석' in cut['html'] for cut in report['cuts'])


def test_missing_answers_keep_the_original_general_practice():
    base = build('work')
    assert cc.enrich_practice(base, 'pungun', None) is base
    assert cc.enrich_practice(base, 'pungun', {'choice4':'a'}) is base
    assert cc.enrich_practice(None, 'pungun', {'choice4':'a','choice5':'a'}) is None
