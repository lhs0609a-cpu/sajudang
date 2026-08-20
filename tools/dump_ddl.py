"""
models.py 에서 DDL 을 뽑는다. 새 알렘빅 리비전을 쓸 때 참고용.

    python tools/dump_ddl.py [출력파일]

★ 뽑은 DDL 을 기존 마이그레이션에 덮어쓰지 마세요. 새 리비전으로 만드세요.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services" / "api"))

from sqlalchemy.dialects import postgresql          # noqa: E402
from sqlalchemy.schema import CreateIndex, CreateTable  # noqa: E402

import models                                        # noqa: E402


def main() -> int:
    d = postgresql.dialect()
    out = []
    for t in models.Base.metadata.sorted_tables:
        out.append(str(CreateTable(t).compile(dialect=d)).strip())
        for ix in sorted(t.indexes, key=lambda i: i.name):
            out.append(str(CreateIndex(ix).compile(dialect=d)).strip())
    sql = ";\n\n".join(out) + ";\n"
    if len(sys.argv) > 1:
        Path(sys.argv[1]).write_text(sql, encoding="utf-8")
        print("저장: %s (%d 문)" % (sys.argv[1], len(out)))
    else:
        print(sql)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
