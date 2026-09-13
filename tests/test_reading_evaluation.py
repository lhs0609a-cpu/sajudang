from fastapi.testclient import TestClient
from main import app
from engine import interpretation, reading_evaluation as evaluation
import store


def test_opt_in_feedback_validates_version_and_rejects_payment_spoof(monkeypatch):
    client = TestClient(app)
    chart = client.post('/v1/chart', json={'year':1993, 'month':11, 'day':25,
        'hour':15, 'minute':30, 'hour_known':True, 'sex':'F', 'birth_city':'서울'}).json()['chart_id']
    request = dict(chart_id=chart, session_id='evaluation-test', lens_id='pungun',
        version=interpretation.VERSION, **{d:'yes' for d in evaluation.DIMENSIONS})
    recorded = []
    monkeypatch.setattr(evaluation, 'record', lambda *args: recorded.append(args))
    assert client.post('/v1/reading-evaluation', json={**request, 'verified_payment':True}).status_code == 422
    assert client.post('/v1/reading-evaluation', json={**request, 'version':1}).status_code == 409
    assert not recorded
    assert client.post('/v1/reading-evaluation', json=request).status_code == 200
    assert recorded[0][5] is False
    assert client.get('/v1/admin/reading-evaluation').status_code in (401, 403, 503)


def test_feedback_overwrites_without_storing_birth_or_identifiers(monkeypatch):
    saved = {}
    def put(key, value, ttl):
        assert ttl == 90 * 86400
        saved[key] = value
    monkeypatch.setattr(store, 'set_json', put)
    monkeypatch.setattr(store, 'scan', lambda prefix, limit: list(saved.items()))
    for value in ('yes', 'no'):
        evaluation.record('private-session', 'private-chart', 'pungun', 4,
            {d:value for d in evaluation.DIMENSIONS}, False)
    assert len(saved) == 1
    assert 'private-session' not in str(saved) and 'private-chart' not in str(saved)
    assert set(next(iter(saved.values()))) == {'lens_id', 'version', 'answers', 'verified_payment', 'at'}
    stats = evaluation.stats()
    assert stats['samples'] == 1 and stats['editions']['4']['paid_samples'] == 0
    assert all(row['no'] == 1 and row['yes'] == 0 for row in stats['editions']['4']['dimensions'].values())
