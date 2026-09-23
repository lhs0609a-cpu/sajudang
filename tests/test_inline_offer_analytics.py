from datetime import datetime, timezone
import analytics


def test_offer_payload_is_numeric_and_position_bounded():
    for name in ('inline_offer_view', 'inline_offer_click'):
        cleaned = analytics._clean(dict(name=name, screen='c2', sid='x'*32, stage=2, question='private'))
        assert cleaned and cleaned['stage'] == 2 and 'question' not in cleaned
        assert analytics._clean(dict(name=name, screen='a1', sid='x'*32, stage=2)) is None
        assert analytics._clean(dict(name=name, screen='c2', sid='x'*32, stage=4)) is None


def test_offer_counts_deduplicate_and_do_not_invent_impressions(monkeypatch):
    def row(name, sid):
        return dict(name=name, sid=sid*32, stage=1, screen='c2', at=datetime.now(timezone.utc).isoformat())
    monkeypatch.setattr(analytics, '_rows', lambda: [row('inline_offer_view','a'),row('inline_offer_view','a'),row('inline_offer_click','a'),row('inline_offer_click','b')])
    first = analytics.funnel()['inline_offers'][0]
    assert first == dict(position=1, viewers=1, clickers=2, observed_clickers=1, click_rate=100.0)
