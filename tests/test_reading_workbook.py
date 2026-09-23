import pytest
from engine import guard, free_depth, practice
from engine.reading_workbook import ANGLES, GUIDES
from engine.report import _plain


@pytest.mark.parametrize('flow', ANGLES)
@pytest.mark.parametrize('concern', GUIDES)
def test_every_flow_and_concern_has_complete_free_help(flow, concern):
    essay=free_depth.scene_html(concern,flow)
    action=practice.build(concern,flow)
    assert len(_plain(essay)) > 650
    assert guard.check(essay)[0]
    for key in ['focus','example','decision','trap','review']:
        assert len(action[key]) > 45
        assert guard.check(action[key])[0]
    assert action['example'] not in essay  # The exercise adds value after the explanation.
    assert len(set(action['steps']))==3


def test_exercises_change_with_both_topic_and_flow():
    for concern in GUIDES:
        assert len({practice.build(concern,flow)['focus'] for flow in ANGLES})==5
    for flow in ANGLES:
        assert len({practice.build(concern,flow)['example'] for concern in GUIDES})==6
