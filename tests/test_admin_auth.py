# -*- coding: utf-8 -*-
"""
주인 문 — 아이디와 비밀번호.

★ 왜 문을 하나 더 내는가

  여태 주인 화면은 `FUNNEL_KEY` 한 줄이었습니다. 그건 **기계를 위한
  열쇠**입니다 — 도구가 머리표에 실어 보내는 난수지요. 사람이 스물네
  자를 외워 칠 수는 없어서 어딘가에 적어 두게 되고, 적어 둔 것은
  새어 나갑니다.

★ 지키는 자리는 하나입니다

  문은 둘이되(`x-funnel-key` · `x-admin-token`) 판정은
  `keyguard.require_admin` 한 곳입니다. 두 곳에서 지키면 한쪽만
  고치는 날이 오고, 그날 열린 쪽은 아무도 모릅니다.

★ 평문은 어디에도 없습니다

  저장소에도 `.env` 에도 서버에도 비밀번호 자체는 없습니다.
  PBKDF2-HMAC-SHA256 해시 한 줄뿐입니다.
"""
import sys
from pathlib import Path

import pytest
from fastapi import HTTPException

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services" / "api"))

import adminauth                       # noqa: E402
import keyguard                        # noqa: E402
import store                           # noqa: E402

PW = "lhs0609c@naver.com"
EMAIL = "lhs0609c@naver.com"


@pytest.fixture
def gate(monkeypatch):
    """아이디 문만 걸린 집."""
    monkeypatch.setattr(adminauth, "ADMIN_EMAIL", EMAIL)
    monkeypatch.setattr(adminauth, "ADMIN_PASSWORD_HASH",
                        adminauth.make_hash(PW))
    monkeypatch.setattr(keyguard, "FUNNEL_KEY", "")
    yield


# ── 해시 ──────────────────────────────────────────────────
def test_hash_never_contains_the_password():
    h = adminauth.make_hash(PW)
    assert PW not in h, "해시에 평문이 섞였소"
    assert h.startswith("pbkdf2_sha256$")


def test_same_password_hashes_differently_each_time():
    """소금이 매번 새로 뽑혀야 새어 나간 표로 되짚지 못합니다."""
    assert adminauth.make_hash(PW) != adminauth.make_hash(PW)


def test_verify_accepts_only_the_real_password():
    h = adminauth.make_hash(PW)
    assert adminauth.verify_hash(PW, h)
    assert not adminauth.verify_hash(PW + "x", h)
    assert not adminauth.verify_hash("", h)


def test_broken_hash_never_opens():
    """꼴이 깨져 있으면 **틀린 것으로** 봅니다. 열지 않습니다."""
    for bad in ("", "x", "md5$1$a$b", "pbkdf2_sha256$notanum$a$b"):
        assert not adminauth.verify_hash(PW, bad)


# ── 로그인 ────────────────────────────────────────────────
def test_login_and_session(gate):
    tok = adminauth.login(EMAIL, PW)
    assert len(tok) >= 32
    assert adminauth.session_of(tok)["email"] == EMAIL
    adminauth.logout(tok)
    assert adminauth.session_of(tok) is None


def test_login_rejects_wrong_password(gate):
    with pytest.raises(adminauth.AuthError):
        adminauth.login(EMAIL, "nope")


def test_login_rejects_wrong_id(gate):
    with pytest.raises(adminauth.AuthError):
        adminauth.login("someone@else.com", PW)


def test_error_does_not_say_which_half_was_wrong(gate):
    """
    「그런 아이디 없소」 라 말하면 아이디부터 캐냅니다. 두 경우가
    같은 말을 해야 합니다.
    """
    def msg(email, pw):
        try:
            adminauth.login(email, pw)
        except adminauth.AuthError as e:
            return str(e)
        return ""
    a = msg(EMAIL, "nope")
    store.delete(adminauth._throttle_key(EMAIL.lower()))
    b = msg("someone@else.com", PW)
    assert a == b, "어느 쪽이 틀렸는지 흘리오"


def test_too_many_knocks_locks_the_door(gate):
    who = "knocker@x.com"
    store.delete(adminauth._throttle_key(who))
    for _ in range(adminauth.TRY_MAX):
        with pytest.raises(adminauth.AuthError):
            adminauth.login(who, "nope")
    # 이제는 **맞는 비밀번호로도** 안 열립니다 — 그게 잠금입니다
    with pytest.raises(adminauth.AuthError) as e:
        adminauth.login(who, "nope")
    assert "5분" in str(e.value)
    store.delete(adminauth._throttle_key(who))


# ── 문지기 ────────────────────────────────────────────────
def test_guard_takes_either_door(gate):
    tok = adminauth.login(EMAIL, PW)
    keyguard.require_admin(None, tok)          # 사람 문
    with pytest.raises(HTTPException) as e:
        keyguard.require_admin(None, None)
    assert e.value.status_code == 401
    adminauth.logout(tok)


def test_guard_takes_the_machine_key(monkeypatch):
    monkeypatch.setattr(keyguard, "FUNNEL_KEY", "k" * 24)
    keyguard.require_admin("k" * 24, None)
    with pytest.raises(HTTPException) as e:
        keyguard.require_admin("wrong", None)
    assert e.value.status_code == 401


def test_guard_closes_when_no_door_is_set(monkeypatch):
    """둘 다 안 걸어 두었으면 **닫습니다.** 열린 쪽이 기본이면 안 됩니다."""
    monkeypatch.setattr(keyguard, "FUNNEL_KEY", "")
    monkeypatch.setattr(adminauth, "ADMIN_EMAIL", "")
    monkeypatch.setattr(adminauth, "ADMIN_PASSWORD_HASH", "")
    with pytest.raises(HTTPException) as e:
        keyguard.require_admin(None, None)
    assert e.value.status_code == 503


# ── 저장소에 평문이 없는가 ────────────────────────────────
def test_repo_holds_no_plaintext_password():
    """
    ★ 저장소에는 해시도 평문도 없습니다. `.env` 는 git 에 안 실립니다.
      누가 편하다고 소스에 박아 넣으면 여기서 걸립니다.
    """
    bad = []
    mark = "ADMIN_PASSWORD_HASH="
    algo = "pbkdf2_" + "sha256$"       # 이 파일이 스스로 걸리지 않게 나눠 적소
    for pat in ("*.py", "*.ts", "*.tsx", "*.ps1", "*.json", "*.md"):
        for f in ROOT.rglob(pat):
            if any(p in f.parts for p in
                   ("node_modules", ".git", ".venv", "__pycache__", ".next")):
                continue
            if f.name == Path(__file__).name:
                continue
            try:
                src = f.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                continue
            if mark in src and algo in src:
                bad.append(str(f.relative_to(ROOT)))
    assert not bad, "저장소에 비밀번호 해시가 박혔소: %s" % bad
