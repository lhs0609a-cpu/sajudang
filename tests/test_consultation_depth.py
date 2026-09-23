from datetime import date
import pytest

from engine import consultation, free_depth, guard, character_consultation
from engine.calendar import build_chart
from engine.features import build_features
from engine.editorial import ROLES, CONCERNS
from engine.practice import build as practice
from engine.report import build_report, _plain


@pytest.fixture(scope='module')
def features():
    return build_features(build_chart(1993, 11, 25, None, None, 'F', hour_known=False),
                          as_of=date(2026, 9, 21))


@pytest.mark.parametrize('concern', CONCERNS)
def test_each_character_has_a_distinct_complete_method(features, concern):
    bodies = []
    for character in ROLES:
        body = consultation.render(character, concern, features)
        assert guard.check(body)[0]
        assert all(heading in body for heading in ('선택이 갈리는 기준', '실제로 꺼내 볼 말', '고쳐 읽어야 할 때'))
        assert len(_plain(body)) > 450
        bodies.append(body)
    assert len(set(bodies)) == 20


@pytest.mark.parametrize('character', ROLES)
def test_method_is_delivered_once_and_paid_body_does_not_leak(features, character):
    free = build_report(features, 'depth-test', character, 'free', 'work')
    paid = build_report(features, 'depth-test', character, 'all', 'work')
    assert sum('consultation-method' in row['html'] for row in paid['cuts']) == 1
    if character != 'dongja':
        assert all('consultation-method' not in row['html'] for row in free['cuts'])
        assert any('free-depth-essay' in row['html'] for row in free['cuts'])
    assert all('여덟 글자' not in row['html'] for row in free['cuts'])


def test_flow_and_concern_change_free_depth():
    assert len({free_depth.depth_html(flow) for flow in free_depth.FLOW}) == 5
    assert len({free_depth.scene_html(concern) for concern in CONCERNS}) == 6
    for flow in free_depth.FLOW:
        assert guard.check(free_depth.depth_html(flow))[0]
    for concern in CONCERNS:
        assert guard.check(free_depth.scene_html(concern))[0]
        action = practice(concern)
        assert len(action['steps']) == 3
        assert all(guard.check(step)[0] for step in action['steps'])


def test_method_evidence_tracks_calculation(features):
    before = consultation.render('pungun', 'work', features)
    other = build_features(build_chart(1988, 5, 3, None, None, 'F', hour_known=False),
                           as_of=date(2026, 9, 21))
    after = consultation.render('pungun', 'work', other)
    assert before != after


def test_all_twenty_characters_have_distinct_deep_interviews():
    assert set(character_consultation.INTERVIEWS) == set(ROLES)
    signatures = set()
    for character, row in character_consultation.INTERVIEWS.items():
        assert len(row[2]) >= 4 and len(row[4]) >= 4
        assert len(row[5]) >= 25 and len(row[6]) >= 25 and len(row[7]) >= 25
        spec = character_consultation.enrich_spec({"id":"work","title":"t","q":"q","options":[]}, character, "work")
        assert spec["q4"] and spec["q5"] and spec["character_axis"]
        topic = {"choice4": row[2][0]["id"], "choice5": row[4][0]["id"]}
        body = character_consultation.render(character, topic, name=character)
        assert "날카로운 판정" in body and "지금 할 한 가지" in body
        assert row[2][0]["label"] in body and row[4][0]["label"] in body
        assert guard.check(body)[0]
        signatures.add((spec["q4"], spec["q5"], row[5], row[7]))
    assert len(signatures) == 20


def test_character_answers_change_the_delivered_consultation(features):
    row = character_consultation.INTERVIEWS['wolha']
    first = {"choice4": row[2][0]["id"], "choice5": row[4][0]["id"]}
    second = {"choice4": row[2][-1]["id"], "choice5": row[4][-1]["id"]}
    assert consultation.render('wolha', 'love', features, first) != consultation.render('wolha', 'love', features, second)
