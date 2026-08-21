"""statement_log 에 chart_key 추가

Revision ID: 0002_statement_chart_key
Revises: 0001_initial
Create Date: 2026-08-21

왜
  chart_id 는 charts.id(UUID) 를 가리키는데, 응답이 들어올 때 charts 행이
  아직 없을 수 있습니다. 그러면 chart_id 가 NULL 로 남아 "어떤 사주에서
  이 문장이 먹혔는가" 를 영영 알 수 없게 됩니다.

  chart_key(생년월일시 해시)를 함께 남겨 그 연결을 잃지 않습니다.
  이 테이블이 서비스의 핵심 자산입니다.
"""
from alembic import op
import sqlalchemy as sa

revision = "0002_statement_chart_key"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def _has_column(bind, table: str, col: str) -> bool:
    return col in {c["name"] for c in sa.inspect(bind).get_columns(table)}


def upgrade() -> None:
    """
    ★ 이미 있으면 건너뜁니다.

    0001 은 Postgres 에서만 '그때의 고정 DDL' 을 씁니다. 그 밖의 방언에서는
    models.py 에서 **지금** 스키마를 만들기 때문에 chart_key 가 이미 들어
    있습니다. 그대로 add_column 하면 duplicate column 으로 막힙니다.
    """
    bind = op.get_bind()
    if _has_column(bind, "statement_log", "chart_key"):
        return
    op.add_column("statement_log", sa.Column("chart_key", sa.Text(), nullable=True))
    op.create_index("ix_stmt_chart_key", "statement_log", ["chart_key"])


def downgrade() -> None:
    bind = op.get_bind()
    if not _has_column(bind, "statement_log", "chart_key"):
        return
    op.drop_index("ix_stmt_chart_key", table_name="statement_log")
    op.drop_column("statement_log", "chart_key")
