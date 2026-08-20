"""
마스터 시드 — seed/*.json → lenses / relay_rules 테이블.

    DATABASE_URL=... python -m scripts.seed

이미 있으면 갱신(upsert)합니다. 마스터 데이터는 시드 파일이 정본입니다.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import db          # noqa: E402
import models      # noqa: E402

SEED = Path(__file__).resolve().parents[3] / "seed"


def seed_lenses(s) -> int:
    data = json.loads((SEED / "lenses.json").read_text("utf-8"))
    for i, l in enumerate(data):
        s.merge(models.Lens(
            id=l["id"], name=l["name"], hanja=l.get("hanja"),
            group_name=l.get("group"), archetype=l.get("archetype"),
            sex=l.get("sex"), you_word=l.get("you_word"), call=l.get("call"),
            combine_axis=l.get("axis"), opening_quote=l.get("opening_quote"),
            price=l.get("price"), released=bool(l.get("released")),
            sort_order=i))
    return len(data)


def seed_relay_rules(s) -> int:
    data = json.loads((SEED / "relay_rules.json").read_text("utf-8"))["rules"]
    for r in data:
        s.merge(models.RelayRule(
            id=r["id"], lens_id=r["lens_id"], priority=r["priority"],
            condition=r["condition"], reason_tpl=r.get("reason"),
            quote_tpl=r.get("quote"), active=True))
    return len(data)


def main() -> int:
    if not db.HAS_DB:
        print("DATABASE_URL 이 없습니다. docker compose up -d postgres 후 다시 실행하세요.")
        return 1
    with db.session() as s:
        n1 = seed_lenses(s)
        n2 = seed_relay_rules(s)
    print("렌즈 %d · 릴레이 규칙 %d 적재" % (n1, n2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
