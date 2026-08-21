"""계측 events 테이블

Revision ID: 0003_events
Revises: 0002_statement_chart_key
Create Date: 2026-08-21

왜
  어디서 나가는지 몰라서 초반을 고칠 수가 없었습니다. 화면별 도달과
  훅 단별 응답률을 세려면 남길 자리가 있어야 합니다.

★ 사람을 식별할 컬럼이 하나도 없습니다.
  생년월일시·이름·고을·이메일·IP 는 물론이고 chart_id 도 없습니다.
  chart_id 는 생년월일시 해시라 같은 생일이면 같은 값이 나옵니다 —
  그 자체가 준식별자입니다. sid 는 브라우저가 만든 난수입니다. (docs/11)
"""
from alembic import op
import sqlalchemy as sa

revision = "0003_events"
down_revision = "0002_statement_chart_key"
branch_labels = None
depends_on = None


def _has_table(bind, name: str) -> bool:
    return name in sa.inspect(bind).get_table_names()


def upgrade() -> None:
    bind = op.get_bind()
    # 0001 이 SQLite 에서는 models.py 로 지금 스키마를 통째로 만들기 때문에
    # 이 테이블이 이미 있을 수 있습니다.
    if _has_table(bind, "events"):
        return

    big = sa.BigInteger().with_variant(sa.Integer, "sqlite")
    op.create_table(
        "events",
        sa.Column("id", big, primary_key=True, autoincrement=True),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("screen", sa.Text(), nullable=False),
        sa.Column("sid", sa.Text(), nullable=False),
        sa.Column("stage", sa.SmallInteger()),
        sa.Column("ms", sa.Integer()),
        sa.Column("n", sa.Integer()),
        sa.Column("yes", sa.SmallInteger()),
        sa.Column("at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_events_sid", "events", ["sid"])
    op.create_index("ix_events_name_screen", "events", ["name", "screen"])
    op.create_index("ix_events_at", "events", ["at"])


def downgrade() -> None:
    bind = op.get_bind()
    if not _has_table(bind, "events"):
        return
    op.drop_index("ix_events_at", table_name="events")
    op.drop_index("ix_events_name_screen", table_name="events")
    op.drop_index("ix_events_sid", table_name="events")
    op.drop_table("events")
