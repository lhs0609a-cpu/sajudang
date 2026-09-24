"""Commercial characters expose an introduction, never their full free chapters."""
from datetime import date
import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'services/api'))
from engine.calendar import build_chart
from engine.features import build_features
from engine.report import build_report
from engine.report import _teaser, _plain
from engine.editorial import ROLES

def test_pattern_preview_starts_with_actual_analysis():
    body = ('<p class="tale">여기까지가 <b>센 것</b>이오.</p>'
            '<p class="cnt">세 가지 중 하나가 걸렸소.</p>'
            '<p class="bite"><b>관계의 짜임</b> — 맡은 책임에 비해 나를 위한 몫은 작아지기 쉽소. '
            '이어서 그 관계와 대응을 자세히 살펴보겠소.</p>')
    teaser = _teaser(body, 'concern_pattern')
    assert teaser.startswith('관계의 짜임')
    assert '여기까지' not in teaser
    assert teaser.removesuffix(' —') in _plain(body)
    assert len(teaser) < len(_plain(body)) * 0.5

@pytest.fixture(scope='module')
def chart_features():
    return build_features(build_chart(1993, 11, 25, 15, 55, 'M', city='서울'), as_of=date(2026, 9, 21))

@pytest.mark.parametrize('lens_id', [key for key in ROLES if key != 'dongja'])
@pytest.mark.parametrize('concern', ['money', 'work', 'love', 'people', 'dir', 'health'])
def test_commercial_character_stops_before_deep_reading(chart_features, lens_id, concern):
    free = build_report(chart_features, 'scope-test', lens_id, 'free', concern, 'INTJ')
    paid = build_report(chart_features, 'scope-test', lens_id, 'all', concern, 'INTJ')
    # ★ 「어떤 사람인가」 가 무료에 섭니다 (2026-09-24) — 알아봐 준 적
    #   없는 집에 값을 치를 까닭이 없소. 깊이는 그대로 값 뒤에 있습니다.
    assert {c['id'] for c in free['cuts']} <= {'chart', 'portrait', 'spine', 'topic_ask', 'spine_depth', 'spine_scene', 'lens_bridge', 'solace', 'closing_cut'}
    assert {'spine_depth', 'spine_scene'} <= {c['id'] for c in free['cuts']}
    assert sum(len(_plain(c['html'])) for c in free['cuts'] if c['id'] in {'spine_depth', 'spine_scene'}) > 200
    assert free['cuts'] and free['locked']
    assert not paid['locked']
    paid_ids = {c['id'] for c in paid['cuts']}
    for cut in free['locked']:
        assert cut['id'] in paid_ids
        assert 'html' not in cut
        assert len(cut.get('teaser') or '') < cut['chars']

@pytest.mark.parametrize('concern', ['money', 'work', 'love', 'people', 'dir', 'health'])
def test_free_only_character_is_not_turned_into_paywall(chart_features, concern):
    free = build_report(chart_features, 'scope-test', 'dongja', 'free', concern)
    assert not free['sells']
    assert not free['locked']
    assert len(free['cuts']) > 2
