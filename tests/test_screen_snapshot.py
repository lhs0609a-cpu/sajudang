"""
찍어 둔 화면 글이 소스와 같은가 — 배포본의 연출 점수.

★ 배포 이미지에는 `apps/web` 이 없습니다. 그래서 fly 의 관리자 화면은
  「이 서버에서는 연출 점수를 못 재오」 로 끝났습니다. 손님이 "관리자
  페이지에서 각 페이지별로 점수 다 볼 수 있어야 한다" 고 했습니다.

  소스에서 읽은 글을 `seed/screen_text.json` 에 찍어 두고, 소스가 없는
  자리에서는 그걸로 잽니다. 찍어 둔 것은 **낡습니다** — 화면 글을
  고치고 안 찍으면 배포본은 옛 점수를 냅니다. 여기서 지문을 대 봅니다.
  어긋나면 `.\dev.ps1 drama` 를 한 번 돌리면 됩니다 (돌 때마다 찍습니다).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services" / "api"))

from engine import screenscan as S                     # noqa: E402


def test_찍어_둔_글이_있고_소스와_같다():
    assert S.SNAP.exists(), "seed/screen_text.json 이 없소 — .\dev.ps1 drama"
    snap = json.loads(S.SNAP.read_text(encoding="utf-8"))
    assert snap["_fingerprint"] == S.source_fingerprint(), (
        "화면 글을 고쳤는데 안 찍었소 — .\dev.ps1 drama 를 돌리시오")
    assert len(snap["screens"]) >= 20


def test_소스가_없어도_찍어_둔_글로_같은_점수를_낸다():
    """배포본 흉내 — apps/web 이 없는 것처럼 하고 잰다."""
    fresh = S.scan_all()
    S._screens.cache_clear()
    with mock.patch.object(S, "WEB", ROOT / "없는_자리"):
        assert S.source_mode() == "snapshot"
        assert S.has_source()
        rows = S.scan_all()
        summ = S.summary(rows)
    S._screens.cache_clear()
    assert summ["source"] == "snapshot" and summ["snapshot_at"]
    assert len(rows) == len(fresh)
    a = {r["id"]: r["total"] for r in fresh}
    b = {r["id"]: r["total"] for r in rows}
    assert a == b, "찍어 둔 글로 잰 점수가 소스로 잰 것과 다르오"
