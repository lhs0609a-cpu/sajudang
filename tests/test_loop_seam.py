"""
루프 이음새 — 배경이 다시 돌 때 튀는가.

★ 왜 이 검사가 생겼나 (2026-09-06)

  배경 영상은 전부 `loop` 로 **영원히** 돕니다. 5초짜리면 한 시간에
  720번 되도는데, 손님이 실제로 보는 것은 「5초짜리 그림」이 아니라
  **이음새 720번**입니다.

  발주서(docs/10 §7)에 「루프는 첫·끝 프레임 일치」라고 적혀 있었지만
  **재는 자리가 없어서** 안 지켜졌습니다. 들어온 열둘을 재보니 이어지는
  것이 하나도 없었습니다 — 넷은 첫·끝이 12.9~34.8이나 벌어져 툭 끊겼고,
  나머지 여덟은 되감겨 있어 5초마다 시간이 거꾸로 흘렀습니다(오르던
  불티가 내려앉음).

★ 왜 여기서 픽셀을 안 재나

  이음새는 눈으로만 잽니다 — ffmpeg 으로 프레임을 뽑아 픽셀을 대 보는
  일입니다. 테스트가 매번 돌릴 수 있는 값이 아니고, ffmpeg 이 없는
  자리에서는 **건너뛰게** 됩니다. 이 저장소는 skip 0 입니다.

  그래서 재는 것은 도구가 하고(`tools/loop_seam.py`), 그 결과를
  `seed/loop_seam.json` 에 찍어 둡니다. 여기서는 **디스크의 클립이
  찍힌 그것인지**만 봅니다. ffmpeg 없이 돌고, 안 구운 클립을 새로
  넣으면 걸립니다.

    .\\dev.ps1 loop              # 재기
    .\\dev.ps1 loop --fix --all  # 고리로 다시 굽기 (기록도 같이 갱신)
    .\\dev.ps1 loop --record     # 재기만 하고 기록 갱신
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RECORD = ROOT / "seed" / "loop_seam.json"

# ★ 클립을 찾는 규칙은 **도구가 갖고 있습니다.** 여기 베껴 두면 둘이
#   갈라집니다 — `greet` 를 도구에 넣었는데 검사는 못 보던 자리가
#   그렇게 생깁니다. 이름 짓기까지 통째로 빌려 씁니다.
#   (`clips()` 는 경로만 훑습니다. ffmpeg 을 안 부릅니다)
sys.path.insert(0, str(ROOT / "tools"))
from loop_seam import clips  # noqa: E402

HOWTO = "  .\\dev.ps1 loop --fix --all   (또는 이미 맞으면 --record)"


def _record() -> dict:
    return json.loads(RECORD.read_text("utf-8"))


def _on_disk() -> dict:
    """디스크에 있는 배경 클립 — 이름 → 확장자 뗀 경로(글자).

    ★ `with_suffix("")` 로 자른 값에 다시 붙이면 안 됩니다.
      `clip.side.mp4` → `clip.side` → `with_suffix(".webm")` 는 `.side` 를
      갈아 끼워 `clip.webm` 이 됩니다. 글자로 자르고 글자로 붙입니다.
    """
    return {name: str(f)[: -len(f.suffix)] for name, f in clips()}


def _sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def test_record_exists():
    assert RECORD.exists(), (
        "seed/loop_seam.json 이 없습니다. 배경이 이어지는지 아무도 안 봤다는 뜻입니다.\n"
        + HOWTO)


def test_every_clip_on_disk_was_measured():
    """
    ★ **새로 넣은 클립이 여기서 걸립니다.** 발주가 되감아 보내거나
      이음새를 안 맞춰 보내는 것이 기본값이라, 넣고 그냥 배포하면
      그 화면만 5초마다 끊깁니다.
    """
    disk = _on_disk()
    seen = _record()["clips"]
    fresh = sorted(set(disk) - set(seen))
    assert not fresh, (
        "고리를 안 구운 클립: %s\n%s" % (fresh, HOWTO))


def test_record_matches_the_files_on_disk():
    """기록이 낡으면 아무것도 지켜 주지 않습니다."""
    disk = _on_disk()
    seen = _record()["clips"]
    gone = sorted(set(seen) - set(disk))
    assert not gone, ("기록에는 있는데 파일이 없는 클립: %s\n%s" % (gone, HOWTO))

    moved = []
    for name, stem in disk.items():
        # 기록에 없는 것은 위 검사가 말합니다. 여기서 터지면 안 됩니다.
        for ext, want in seen.get(name, {}).get("files", {}).items():
            f = Path(stem + "." + ext)
            if not f.exists():
                moved.append("%s/%s 없음" % (name, ext))
            elif _sha(f) != want["sha256"]:
                moved.append("%s/%s 바뀜" % (name, ext))
    assert not moved, ("잰 뒤에 바뀐 클립: %s\n%s" % (moved, HOWTO))


def test_no_clip_jumps_at_the_seam():
    """첫 프레임과 끝 프레임이 벌어져 있으면 5초마다 툭 끊깁니다."""
    rec = _record()
    ok = rec["seam_ok"]
    jumps = {n: c["seam"] for n, c in rec["clips"].items() if c["seam"] > ok}
    assert not jumps, (
        "이음새가 벌어진 클립 (문턱 %s): %s\n%s" % (ok, jumps, HOWTO))


def test_no_static_scene_runs_backwards():
    """
    ★ 되감기는 **미는 장면(Dolly)에만** 허용합니다.

      가만히 있는 장면을 되감으면 오르던 불티가 내려앉고 피던 연기가
      빨려 들어갑니다. 이음새는 없어지는데 5초마다 시간이 거꾸로
      흐릅니다 — 손님이 「뭔가 이상하다」고 느끼는 자리입니다.

      미는 장면은 겹쳐 넘길 수가 없어(첫머리와 끝자락의 배율이 다름)
      되감는 것이 답입니다. 그래서 여기만 열어 둡니다.
    """
    back = sorted(n for n, c in _record()["clips"].items()
                  if c["mode"] == "pingpong" and not c["dolly"])
    assert not back, (
        "가만히 있는 장면인데 되감겨 있습니다: %s\n%s" % (back, HOWTO))
