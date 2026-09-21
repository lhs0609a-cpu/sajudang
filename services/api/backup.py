"""
백업 — 볼륨이 날아가도 값을 치른 사람의 자격이 안 사라지게 (§29 · §30).

★ 무엇이 걸려 있나

  Fly 볼륨 한 장(`/data`)에 두 가지가 삽니다 —

      store.sqlite   **주문 · 자격 · 인장 · 구독 · 감사기록**
      app.sqlite     통계·문장 로그

  앞쪽이 날아가면 값을 치른 손님이 자기 리포트를 못 엽니다. 주문번호를
  들고 와도 소용없습니다 — 되찾을 원장 자체가 없으니까요.
  볼륨은 스냅샷이 돌지만 그건 Fly 쪽 일이고, 우리 손에 **우리가 떠 둔
  것**이 하나도 없었습니다.

★ 어떻게 뜨는가

  `sqlite3.Connection.backup()` — 온라인 백업 API 입니다.
  파일을 그냥 복사하면 쓰는 중에 뜬 판이 깨질 수 있습니다(WAL 이
  중간이면 반만 담깁니다). 이 API 는 잠금을 잡고 페이지 단위로
  옮기므로 **도는 중에 떠도 열리는 판**이 나옵니다.

★ 어디에 두는가

  같은 볼륨의 `/data/backup/` 입니다. 볼륨이 통째로 날아가면 이것도
  같이 날아갑니다 — 그건 **압니다.** 이 자리가 막는 것은 더 흔한
  사고입니다: 마이그레이션 실수, 잘못된 청소, 나쁜 배포.
  볼륨 밖으로 부치려면 저장소 열쇠가 필요하고 그건 사람이 정할
  일이라, 여기서는 **뜨는 것까지**만 합니다 (`BACKUP_DIR` 로 옮길 수 있음).

★ 이름에 사람 것을 안 넣습니다

  파일 이름은 날짜뿐입니다. 언제 것인지 말고는 아무것도 안 적습니다.
"""
from __future__ import annotations

import logging
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

log = logging.getLogger("backup")

# 이레 치를 굴립니다. 하루 한 번이면 한 주 안에 알아차릴 사고를 덮습니다.
KEEP_DAYS = int(os.getenv("BACKUP_KEEP", "7"))


def _targets() -> list[Path]:
    """떠야 할 판. 없는 것은 조용히 건너뜁니다."""
    out = []
    store_path = os.getenv("STORE_PATH", "").strip()
    if store_path:
        out.append(Path(store_path))
    url = os.getenv("DATABASE_URL", "")
    if url.startswith("sqlite:///"):
        out.append(Path(url.replace("sqlite:////", "/").replace("sqlite:///", "")))
    return [p for p in out if p.exists()]


def _dir() -> Path:
    d = Path(os.getenv("BACKUP_DIR", "").strip() or "/data/backup")
    d.mkdir(parents=True, exist_ok=True)
    return d


def run() -> dict:
    """한 번 뜹니다. 돌려주는 것은 무엇을 얼마나 떴는가."""
    day = datetime.now(timezone.utc).strftime("%Y%m%d")
    out: list[dict] = []
    try:
        dest_dir = _dir()
    except OSError as e:
        return {"ok": False, "why": "백업 자리를 못 만들었소: %s" % e, "files": []}

    for src in _targets():
        dest = dest_dir / ("%s.%s.sqlite" % (src.stem, day))
        try:
            # ★ 파일 복사가 아니라 온라인 백업 API 입니다.
            #   도는 중에 떠도 열리는 판이 나옵니다.
            with sqlite3.connect("file:%s?mode=ro" % src, uri=True) as s, \
                    sqlite3.connect(dest) as d:
                s.backup(d)
            out.append({"name": dest.name, "bytes": dest.stat().st_size})
        except Exception as e:                            # noqa: BLE001
            log.exception("백업 실패 %s", src.name)
            out.append({"name": dest.name, "error": "%s" % type(e).__name__})

    # 오래된 것 치우기 — 굴리지 않으면 볼륨이 백업으로 찹니다.
    dropped = 0
    try:
        keep = sorted(dest_dir.glob("*.sqlite"), reverse=True)
        by_stem: dict[str, int] = {}
        for f in keep:
            stem = f.name.split(".")[0]
            by_stem[stem] = by_stem.get(stem, 0) + 1
            if by_stem[stem] > KEEP_DAYS:
                f.unlink()
                dropped += 1
    except OSError:                                       # pragma: no cover
        log.exception("오래된 백업을 못 치웠소")

    ok = bool(out) and all("error" not in f for f in out)
    return {"ok": ok, "at": datetime.now(timezone.utc).isoformat(),
            "files": out, "dropped": dropped, "dir": str(dest_dir),
            "keep_days": KEEP_DAYS}


def status() -> dict:
    """마지막으로 언제 떴나 — 주인 화면이 보는 자리."""
    try:
        d = Path(os.getenv("BACKUP_DIR", "").strip() or "/data/backup")
        files = sorted(d.glob("*.sqlite"), reverse=True) if d.is_dir() else []
    except OSError:                                       # pragma: no cover
        files = []
    if not files:
        return {"have": False, "say": "아직 떠 둔 것이 없소."}
    newest = files[0]
    return {"have": True, "count": len(files), "newest": newest.name,
            "at": datetime.fromtimestamp(newest.stat().st_mtime,
                                         timezone.utc).isoformat()}
