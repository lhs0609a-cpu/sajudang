import pytest
from fastapi.testclient import TestClient
from main import app


@pytest.mark.parametrize('origin', ['https://saju.megaload.co.kr', 'https://sajudang-three.vercel.app'])
@pytest.mark.parametrize('path', ['/v1/chart', '/v1/hook', '/v1/report', '/v1/pay/prepare'])
def test_production_browser_can_preflight(origin, path):
    response = TestClient(app).options(path, headers={
        'Origin': origin, 'Access-Control-Request-Method': 'POST',
        'Access-Control-Request-Headers': 'content-type',
    })
    assert response.status_code == 200
    assert response.headers['access-control-allow-origin'] == origin


@pytest.mark.parametrize('origin', ['https://saju.megaload.co.kr.example.com', 'https://untrusted.vercel.app'])
def test_unrelated_origins_remain_disallowed(origin):
    response = TestClient(app).options('/v1/chart', headers={
        'Origin': origin, 'Access-Control-Request-Method': 'POST',
    })
    assert response.status_code == 400
    assert 'access-control-allow-origin' not in response.headers
