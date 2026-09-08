from datetime import datetime, timedelta, timezone
import pytest
from fastapi.testclient import TestClient
from main import app
import store
from routers import subscription


@pytest.fixture
def client(monkeypatch):
    store.clear_all()
    monkeypatch.setenv('RENEW_JOB_KEY','scheduler-test-key')
    return TestClient(app)


def test_job_rejects_missing_or_wrong_key_without_charging(client, monkeypatch):
    monkeypatch.setattr(subscription,'renew',lambda *a:pytest.fail('unauthorized charge'))
    for headers in ({},{'x-job-key':'wrong'}):
        assert client.post('/v1/jobs/renew-subscriptions',headers=headers).status_code==403


def test_job_only_renews_due_records_and_retires_ended_cards(client,monkeypatch):
    now=datetime.now(timezone.utc)
    for sid,days,ending in [('due',-1,False),('future',2,False),('ended',-1,True)]:
        subscription._save({'session_id':sid,'user_key':subscription._user_key(sid),
            'status':'active','period_end':(now+timedelta(days=days)).isoformat(),
            'ending':ending,'billing_key':'encrypted-test-only','fails':0})
    charged=[]
    monkeypatch.setattr(subscription,'renew',lambda sub,now:charged.append(sub['session_id']) or {'ok':True})
    r=client.post('/v1/jobs/renew-subscriptions',headers={'x-job-key':'scheduler-test-key'})
    assert r.status_code==200
    assert charged==['due']
    assert r.json()['renewed']==1 and r.json()['retired']==1
    assert subscription._load('ended')['billing_key']==''
    assert store.get_json('job:renewal-status')['more'] is False


def test_missing_job_configuration_fails_closed(client,monkeypatch):
    monkeypatch.delenv('RENEW_JOB_KEY')
    assert client.post('/v1/jobs/renew-subscriptions',headers={'x-job-key':'scheduler-test-key'}).status_code==403
