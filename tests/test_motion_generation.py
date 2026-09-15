"""The media queue must preserve source identity and avoid duplicate paid jobs."""
import importlib.util
import json
from pathlib import Path

import httpx
import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("generate_motion", ROOT / "tools/generate_motion.py")
M = importlib.util.module_from_spec(spec)
spec.loader.exec_module(M)


def jobs():
    return json.loads(M.PLAN.read_text(encoding="utf8"))["jobs"]


def test_all_current_sources_exist_and_match_production_list():
    rows = jobs()
    assert len({j["id"] for j in rows}) == len(rows)
    assert len([j for j in rows if j["id"].startswith("char-")]) == 19
    assert not any("pungun" in j.get("source", "") for j in rows), "User requested the original Pungun artwork and animation be retained"
    for job in rows:
        M.source(job)


def test_a_recorded_submission_is_not_submitted_again(tmp_path):
    row = jobs()[0]
    state = {row["id"]: {"fingerprint": M.fingerprint(row), "status": "submission_unconfirmed"}}
    def forbidden(request):
        pytest.fail("Duplicate generation request")
    with httpx.Client(transport=httpx.MockTransport(forbidden)) as client:
        M.submit(client, [row], state, tmp_path / "jobs.json")


def test_timeout_keeps_the_unconfirmed_submission_record(tmp_path):
    row = jobs()[0]
    state = {}
    def timeout(request):
        raise httpx.ReadTimeout("mock timeout")
    with httpx.Client(transport=httpx.MockTransport(timeout)) as client:
        with pytest.raises(httpx.ReadTimeout):
            M.submit(client, [row], state, tmp_path / "jobs.json")
    saved = json.loads((tmp_path / "jobs.json").read_text(encoding="utf8"))
    assert saved[row["id"]]["status"] == "submission_unconfirmed"


def test_revised_prompt_requires_a_distinct_job(tmp_path):
    row = jobs()[0]
    state = {row["id"]: {"fingerprint": M.fingerprint(row)}}
    revised = {**row, "prompt": row["prompt"] + " New motion."}
    with httpx.Client(transport=httpx.MockTransport(lambda request: pytest.fail("Unexpected request"))) as client:
        with pytest.raises(ValueError, match="Job changed"):
            M.submit(client, [revised], state, tmp_path / "jobs.json")


def test_credentials_are_never_sent_to_a_foreign_queue_host():
    with pytest.raises(ValueError):
        M.queue_url("https://example.com/status")
