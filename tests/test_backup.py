"""
백업 — 볼륨이 상해도 값을 치른 사람의 자격이 남는가.

★ 여기서 증명 못 하는 것
    볼륨이 **통째로** 날아가는 경우. 백업이 같은 볼륨에 살기 때문입니다.
    그건 압니다 — `backup.py` 머리말에 적혀 있고, 볼륨 밖으로 부치려면
    저장소 열쇠가 필요해 사람이 정할 일입니다.

★ 여기서 증명하는 것
    · 도는 중에 떠도 **열리는 판**이 나온다 (온라인 백업 API)
    · 뜬 판에 주문과 자격이 들어 있다
    · 이레 치만 굴린다
    · 열쇠 없이는 못 뜬다
    · 안 떠졌는데 떠진 척하지 않는다
"""
from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services" / "api"))

JOBKEY = "job-key-for-test-0001"


@pytest.fixture()
def env(tmp_path, monkeypatch):
    monkeypatch.setenv("STORE_PATH", str(tmp_path / "store.sqlite"))
    monkeypatch.setenv("BACKUP_DIR", str(tmp_path / "backup"))
    monkeypatch.setenv("RENEW_JOB_KEY", JOBKEY)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    for m in [k for k in list(sys.modules)
              if k in ("store", "backup", "db", "main")
              or k.startswith("routers")]:
        sys.modules.pop(m, None)
    return tmp_path


def test_뜬_판이_열리고_자격이_들어_있다(env):
    import backup
    import store
    store.set_json("order:oid-1", {"status": "paid", "amount": 9900,
                                   "tier": "all", "order_id": "oid-1"})
    store.set_json("orders:sess-1", ["oid-1"])

    got = backup.run()
    assert got["ok"], got
    assert got["files"], "아무것도 안 떴소"

    # ★ 뜬 판을 **실제로 열어** 봅니다. 파일이 생긴 것만으로는
    #   백업이 아닙니다 — 반만 담긴 판도 파일은 생깁니다.
    name = got["files"][0]["name"]
    with sqlite3.connect(Path(got["dir"]) / name) as db:
        rows = dict(db.execute("SELECT k, v FROM kv").fetchall()) \
            if db.execute("SELECT name FROM sqlite_master "
                          "WHERE type='table' AND name='kv'").fetchone() else {}
    assert rows, "뜬 판이 비었소"
    assert any("oid-1" in str(k) or "oid-1" in str(v) for k, v in rows.items()), \
        "주문이 안 담겼소"


def test_이레_치만_굴린다(env, monkeypatch):
    import backup
    monkeypatch.setattr(backup, "KEEP_DAYS", 2)
    d = Path(backup._dir())
    for day in range(20260101, 20260106):
        (d / ("store.%d.sqlite" % day)).write_bytes(b"x")
    got = backup.run()
    left = sorted(p.name for p in d.glob("store.*.sqlite"))
    assert len(left) <= 2, "안 굴렸소: %s" % left
    assert got["dropped"] >= 1


def test_이름에_사람_것이_없다(env):
    import backup
    got = backup.run()
    for f in got["files"]:
        assert "sess" not in f["name"] and "sjd_" not in f["name"]


def test_열쇠_없이는_못_뜬다(env):
    from fastapi.testclient import TestClient
    import main
    c = TestClient(main.app)
    assert c.post("/v1/jobs/backup").status_code == 403
    assert c.post("/v1/jobs/backup",
                  headers={"x-job-key": "wrong-key"}).status_code == 403


def test_열쇠가_맞으면_뜨고_상태가_남는다(env):
    from fastapi.testclient import TestClient
    import main
    import store
    store.set_json("order:oid-2", {"status": "paid", "amount": 1})
    c = TestClient(main.app)
    r = c.post("/v1/jobs/backup", headers={"x-job-key": JOBKEY})
    assert r.status_code == 200, r.text
    assert r.json()["ok"] is True
    assert store.get_json("job:backup-status"), "상태를 안 남겼소"


def test_못_떴으면_성공이라_안_한다(env, monkeypatch):
    """
    ★ 조용히 200 을 주면 백업이 없는 것보다 나쁩니다 —
      **있는 줄 알고** 지냅니다.
    """
    from fastapi.testclient import TestClient
    import backup
    import main
    monkeypatch.setattr(backup, "run",
                        lambda: {"ok": False, "why": "자리를 못 만들었소", "files": []})
    c = TestClient(main.app, raise_server_exceptions=False)
    r = c.post("/v1/jobs/backup", headers={"x-job-key": JOBKEY})
    assert r.status_code == 500, r.text


def test_예약이_걸려_있다():
    """돌릴 자리가 없으면 코드가 있어도 안 뜹니다."""
    wf = ROOT / ".github/workflows/backup.yml"
    assert wf.exists(), "백업을 돌릴 자리가 없소"
    text = wf.read_text(encoding="utf-8")
    assert "schedule" in text and "cron" in text
    assert "/v1/jobs/backup" in text


# ★ 검사 파일이 끝나면 **모듈을 치웁니다.**
#   `keyguard` 는 뜰 때 FUNNEL_KEY 를 한 번 읽어 박아 둡니다. 남겨 두면
#   다음 파일이 「열쇠 걸린 집」을 물려받아 엉뚱한 자리가 깨집니다.
@pytest.fixture(autouse=True)
def _evict_modules():
    yield
    for m in [k for k in list(sys.modules)
              if k in ("store", "payments", "db", "main", "analytics",
                       "throttle", "audit", "errors", "backup")
              or k.startswith("routers")]:
        sys.modules.pop(m, None)
