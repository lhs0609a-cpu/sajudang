"""
주인 자리 아이디·비밀번호 걸기.

    .\\dev.ps1 admin-pass                     물어보고 .env 에 씁니다
    .\\dev.ps1 admin-pass --print             .env 를 안 건드리고 한 줄만 찍습니다

★ 평문은 **어디에도 안 적힙니다**

  저장소에도, `.env` 에도, 화면에도 비밀번호 자체는 안 남습니다.
  남는 것은 PBKDF2-HMAC-SHA256 해시 한 줄뿐입니다. 그 줄로는
  비밀번호를 되짚을 수 없습니다.

★ `.env` 는 git 에 안 실립니다 (.gitignore). 배포에는 이렇게 겁니다 —

      fly secrets set ADMIN_EMAIL=... ADMIN_PASSWORD_HASH='...' -a sajudang-api

  작은따옴표를 빼면 셸이 `$` 를 변수로 읽어 해시가 잘립니다.
"""
from __future__ import annotations

import argparse
import getpass
import io
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services" / "api"))

import adminauth                                   # noqa: E402

ENV = ROOT / ".env"
KEYS = ("ADMIN_EMAIL", "ADMIN_PASSWORD_HASH")


def weak(email: str, password: str) -> list:
    """약한 자리를 짚어 준다. 막지는 않는다 — 정하는 것은 주인이다."""
    bad = []
    if password.lower() == email.lower():
        bad.append("비밀번호가 아이디와 같소 — 아이디를 아는 사람이 곧 문을 아오")
    if len(password) < 10:
        bad.append("열 자가 안 되오")
    if password.isdigit() or password.isalpha():
        bad.append("한 갈래 글자뿐이오 (숫자·글자·기호를 섞으시오)")
    return bad


def write_env(email: str, hashed: str) -> None:
    old = io.open(ENV, encoding="utf-8").read() if ENV.exists() else ""
    keep = [ln for ln in old.splitlines()
            if not ln.startswith(tuple(k + "=" for k in KEYS))]
    body = "\n".join(keep).rstrip()
    add = ("\n\n# ── 주인 자리 ────────────────────────────────────────\n"
           "# 비밀번호는 여기 없습니다. 해시만 있습니다.\n"
           "# 바꾸려면:  .\\dev.ps1 admin-pass\n"
           "ADMIN_EMAIL=%s\n"
           "ADMIN_PASSWORD_HASH=%s\n" % (email, hashed))
    io.open(ENV, "w", encoding="utf-8", newline="\n").write(
        (body + add).lstrip("\n"))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--email", help="주인 아이디 (이메일)")
    ap.add_argument("--print", dest="only_print", action="store_true",
                    help=".env 를 안 건드리고 걸 줄만 찍는다")
    a = ap.parse_args()

    email = (a.email or os.getenv("ADMIN_EMAIL") or "").strip()
    if not email:
        email = input("아이디(이메일): ").strip()
    if not email:
        print("아이디가 비었소.")
        return 1

    # ★ 화면에 안 찍힙니다. 셸 기록에도 안 남습니다.
    pw = getpass.getpass("비밀번호 (안 보이오): ")
    again = getpass.getpass("한 번 더: ")
    if pw != again:
        print("두 번이 다르오.")
        return 1

    for w in weak(email, pw):
        print("  ※ " + w)

    hashed = adminauth.make_hash(pw)
    assert adminauth.verify_hash(pw, hashed)

    if a.only_print:
        print()
        print("ADMIN_EMAIL=%s" % email)
        print("ADMIN_PASSWORD_HASH=%s" % hashed)
        return 0

    write_env(email, hashed)
    print()
    print("걸었소 — %s" % ENV)
    print("  아이디  %s" % email)
    print("  해시    %s…  (평문은 어디에도 안 남소)" % hashed[:34])
    print()
    print("배포에도 걸려면:")
    print("  fly secrets set ADMIN_EMAIL=%s "
          "ADMIN_PASSWORD_HASH='%s' -a sajudang-api" % (email, hashed))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
