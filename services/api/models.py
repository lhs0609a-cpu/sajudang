"""
DB 모델 — docs/04_데이터베이스_설계서.md 그대로.

★ statement_log 가 이 서비스의 핵심 자산입니다. 인덱스를 빠뜨리지 마세요.
  이 테이블이 가장 커집니다.

개인정보 (docs/04 §10)
    얼굴 사진은 **생체인식정보** — DB 에 저장하지 않습니다. 컬럼 자체가 없습니다.
    상대 생년월일은 해시(target_hash)로만 남깁니다.
"""
from __future__ import annotations

import uuid
from datetime import datetime, date

from sqlalchemy import (
    JSON, BigInteger, Boolean, CheckConstraint, Date, DateTime, ForeignKey,
    Index, Integer, SmallInteger, String, Text, Uuid, func, text,
)
from sqlalchemy.dialects.postgresql import ARRAY as PG_ARRAY
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


# ── 방언에 안 묶이는 타입 ──────────────────────────────────
#
# 운영은 Postgres 지만 SQLite 로도 떠야 합니다. 그래야
#   · 마이그레이션을 실제로 돌려 볼 수 있고 (안 그러면 영영 미검증)
#   · Postgres 없이도 statement_log · 회고 루프 · 계측이 살아 있습니다.
#
# Postgres 로 붙으면 예전과 똑같은 타입이 나갑니다. SQLite 에서만 갈아탑니다.
#   JSONB → JSON (TEXT 로 저장) · UUID → CHAR(32) · ARRAY → JSON 목록

JSONB_OR_JSON = JSON().with_variant(JSONB, 'postgresql')

# ★ SQLite 는 INTEGER PRIMARY KEY 만 자동증가시킵니다. BIGINT 로 두면
#   id 가 NULL 로 들어가 INSERT 가 통째로 막힙니다. PG 에서는 그대로 BIGINT.
BIGSERIAL = BigInteger().with_variant(Integer, 'sqlite')


def _arr(inner):
    # PG 에서는 진짜 배열, 그 밖에서는 JSON 목록
    return JSON().with_variant(PG_ARRAY(inner), 'postgresql')


def _uuid_pk():
    return mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)


def _ts():
    return mapped_column(DateTime(timezone=True), server_default=func.now())


# ══════════════════════════════════════════════════════════
# 사용자
# ══════════════════════════════════════════════════════════
class User(Base):
    __tablename__ = "users"
    id: Mapped[uuid.UUID] = _uuid_pk()
    nickname: Mapped[str | None] = mapped_column(Text)      # 본명 아니어도 됨
    email: Mapped[str | None] = mapped_column(Text, unique=True)
    created_at: Mapped[datetime] = _ts()
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class DailyLimit(Base):
    """사용자별 하루 결제·릴레이 상한. 브레이크의 영속 기록."""
    __tablename__ = "daily_limits"
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id"), primary_key=True)
    day: Mapped[date] = mapped_column(Date, primary_key=True)
    purchases: Mapped[int] = mapped_column(Integer, default=0)
    relays: Mapped[int] = mapped_column(Integer, default=0)
    visits: Mapped[int] = mapped_column(Integer, default=0)


# ══════════════════════════════════════════════════════════
# 명식
# ══════════════════════════════════════════════════════════
class Chart(Base):
    __tablename__ = "charts"
    id: Mapped[uuid.UUID] = _uuid_pk()
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id"))
    owner_label: Mapped[str | None] = mapped_column(Text)   # 나 / 어머니 / 상대
    birth_year: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    birth_month: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    birth_day: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    birth_hour: Mapped[int | None] = mapped_column(SmallInteger)   # NULL = 시각 미상
    birth_minute: Mapped[int | None] = mapped_column(SmallInteger)
    hour_known: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    sex: Mapped[str] = mapped_column(String(1), nullable=False)
    birth_city: Mapped[str | None] = mapped_column(Text)
    axis4: Mapped[str | None] = mapped_column(String(4))
    features: Mapped[dict] = mapped_column(JSONB_OR_JSON, nullable=False)
    # ★ 만세력을 고치면 기존 명식 결과가 달라진다. 재계산 대상 특정용.
    engine_ver: Mapped[str] = mapped_column(Text, nullable=False)
    cache_key: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    created_at: Mapped[datetime] = _ts()

    __table_args__ = (
        Index("ix_charts_user_id", "user_id"),
        Index("ix_charts_cache_key", "cache_key"),
        # GIN 은 Postgres 전용. SQLite 에서는 이 인덱스를 만들지 않습니다.
        Index("ix_charts_features_gin", "features",
              postgresql_using="gin").ddl_if(dialect="postgresql"),
    )


# ══════════════════════════════════════════════════════════
# 마스터 — 렌즈 · 상품 · 릴레이 규칙
# ══════════════════════════════════════════════════════════
class Lens(Base):
    __tablename__ = "lenses"
    id: Mapped[str] = mapped_column(Text, primary_key=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    hanja: Mapped[str | None] = mapped_column(Text)
    school: Mapped[str | None] = mapped_column(Text)
    group_name: Mapped[str | None] = mapped_column(Text)
    archetype: Mapped[str | None] = mapped_column(Text)
    sex: Mapped[str | None] = mapped_column(String(1))
    you_word: Mapped[str | None] = mapped_column(Text)
    call: Mapped[str | None] = mapped_column(Text)
    theme_color: Mapped[str | None] = mapped_column(Text)
    combine_axis: Mapped[str | None] = mapped_column(Text)
    focus: Mapped[list | None] = mapped_column(_arr(Text))
    avoid_domains: Mapped[list | None] = mapped_column(_arr(Integer))
    taboo: Mapped[list | None] = mapped_column(_arr(Text))   # ★ 절대 출력 금지
    handoff: Mapped[dict | None] = mapped_column(JSONB_OR_JSON)
    opening_quote: Mapped[str | None] = mapped_column(Text)
    pages: Mapped[int | None] = mapped_column(Integer)
    price: Mapped[int | None] = mapped_column(Integer)
    released: Mapped[bool] = mapped_column(Boolean, default=False)
    sort_order: Mapped[int | None] = mapped_column(Integer)


class Product(Base):
    """신상품 출시 = INSERT 한 줄. 코드 수정 없이 SKU 를 늘린다."""
    __tablename__ = "products"
    id: Mapped[str] = mapped_column(Text, primary_key=True)
    name: Mapped[str | None] = mapped_column(Text)
    engine: Mapped[str | None] = mapped_column(Text)   # solo|scope|dyad|selection|external
    scope: Mapped[str | None] = mapped_column(Text)    # lifetime|year|month|day|range
    lens_id: Mapped[str | None] = mapped_column(Text, ForeignKey("lenses.id"))
    domain_ids: Mapped[list | None] = mapped_column(_arr(Integer))
    needs_partner: Mapped[bool] = mapped_column(Boolean, default=False)
    needs_photo: Mapped[bool] = mapped_column(Boolean, default=False)
    guardrail: Mapped[str | None] = mapped_column(Text)  # standard|reunion|health|child
    price: Mapped[int | None] = mapped_column(Integer)
    cooldown_days: Mapped[int] = mapped_column(Integer, default=0)   # 재회 = 7
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class RelayRule(Base):
    __tablename__ = "relay_rules"
    id: Mapped[str] = mapped_column(Text, primary_key=True)
    lens_id: Mapped[str | None] = mapped_column(Text, ForeignKey("lenses.id"))
    priority: Mapped[int] = mapped_column(Integer, nullable=False)
    condition: Mapped[dict] = mapped_column(JSONB_OR_JSON, nullable=False)
    reason_tpl: Mapped[str | None] = mapped_column(Text)
    quote_tpl: Mapped[str | None] = mapped_column(Text)
    active: Mapped[bool] = mapped_column(Boolean, default=True)


# ══════════════════════════════════════════════════════════
# 훅 · 리포트
# ══════════════════════════════════════════════════════════
class Hook(Base):
    __tablename__ = "hooks"
    id: Mapped[uuid.UUID] = _uuid_pk()
    chart_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("charts.id"))
    lens_id: Mapped[str | None] = mapped_column(Text, ForeignKey("lenses.id"))
    concern: Mapped[str] = mapped_column(Text, nullable=False)
    segments: Mapped[dict] = mapped_column(JSONB_OR_JSON, nullable=False)
    created_at: Mapped[datetime] = _ts()


class Report(Base):
    __tablename__ = "reports"
    id: Mapped[uuid.UUID] = _uuid_pk()
    chart_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("charts.id"))
    lens_id: Mapped[str | None] = mapped_column(Text, ForeignKey("lenses.id"))
    product_id: Mapped[str | None] = mapped_column(Text, ForeignKey("products.id"))
    tier: Mapped[str | None] = mapped_column(Text)
    concern: Mapped[str | None] = mapped_column(Text)
    unlocked: Mapped[list | None] = mapped_column(_arr(Text))
    engine_ver: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = _ts()


class ReportCut(Base):
    __tablename__ = "report_cuts"
    report_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("reports.id", ondelete="CASCADE"),
        primary_key=True)
    seq: Mapped[int] = mapped_column(Integer, primary_key=True)
    kind: Mapped[str | None] = mapped_column(Text)
    statement_id: Mapped[str | None] = mapped_column(Text)
    body: Mapped[dict | None] = mapped_column(JSONB_OR_JSON)
    locked: Mapped[bool] = mapped_column(Boolean, default=False)


# ══════════════════════════════════════════════════════════
# ★ statement_log — 가장 중요한 테이블
# ══════════════════════════════════════════════════════════
class StatementLog(Base):
    """
    문장이 노출된 사실과 응답을 남긴다.

    조건 스냅샷(day_gan, strength, …)이 있어야
    "어떤 사주에서 이 문장이 잘 먹히는지" 를 나중에 분석할 수 있다.
    응답 100건 미만이면 공감률을 화면에 띄우지 않는다. (거짓 광고)
    """
    __tablename__ = "statement_log"
    id: Mapped[int] = mapped_column(BIGSERIAL, primary_key=True, autoincrement=True)
    statement_id: Mapped[str] = mapped_column(Text, nullable=False)
    chart_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("charts.id"))
    # 캐시 키(생년월일시 해시). charts 행이 아직 없어도 어떤 명식이었는지
    # 잃지 않기 위해 원문 그대로 남긴다. 이게 없으면 hit율 분석이 불가능해진다.
    chart_key: Mapped[str | None] = mapped_column(Text)
    user_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True))
    lens_id: Mapped[str | None] = mapped_column(Text)
    concern: Mapped[str | None] = mapped_column(Text)
    stage: Mapped[str | None] = mapped_column(Text)
    # 조건 스냅샷
    day_gan: Mapped[str | None] = mapped_column(String(1))
    strength: Mapped[str | None] = mapped_column(Text)
    top_ten_god: Mapped[str | None] = mapped_column(Text)
    weak_el: Mapped[str | None] = mapped_column(String(1))
    strong_el: Mapped[str | None] = mapped_column(String(1))
    flow: Mapped[str | None] = mapped_column(Text)
    axis4: Mapped[str | None] = mapped_column(String(4))
    # 응답
    answer: Mapped[int | None] = mapped_column(SmallInteger)   # 1 그렇다 / 0 아니다
    answered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    shown_at: Mapped[datetime] = _ts()

    __table_args__ = (
        Index("ix_stmt_statement_answer", "statement_id", "answer"),
        Index("ix_stmt_chart", "chart_id"),
        Index("ix_stmt_chart_key", "chart_key"),
        Index("ix_stmt_shown_at", "shown_at"),
        Index("ix_stmt_user_shown", "user_id", "shown_at"),
    )


# ══════════════════════════════════════════════════════════
# 릴레이 · 쿨다운
# ══════════════════════════════════════════════════════════
class RelayLog(Base):
    __tablename__ = "relay_log"
    id: Mapped[int] = mapped_column(BIGSERIAL, primary_key=True, autoincrement=True)
    user_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True))
    chart_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True))
    rule_id: Mapped[str | None] = mapped_column(Text)
    from_lens: Mapped[str | None] = mapped_column(Text)
    to_lens: Mapped[str | None] = mapped_column(Text)
    shown_at: Mapped[datetime] = _ts()
    clicked: Mapped[bool] = mapped_column(Boolean, default=False)
    purchased: Mapped[bool] = mapped_column(Boolean, default=False)

    __table_args__ = (Index("ix_relay_rule_purchased", "rule_id", "purchased"),)


class Cooldown(Base):
    """재회 7일 쿨다운 등. target_hash = 상대 생년월일 해시 (원본 저장 금지)."""
    __tablename__ = "cooldowns"
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    kind: Mapped[str] = mapped_column(Text, primary_key=True)
    target_hash: Mapped[str] = mapped_column(Text, primary_key=True)
    until: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


# ══════════════════════════════════════════════════════════
# 결제 · 인장 · 후기
# ══════════════════════════════════════════════════════════
class Purchase(Base):
    __tablename__ = "purchases"
    id: Mapped[uuid.UUID] = _uuid_pk()
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id"))
    product_id: Mapped[str | None] = mapped_column(Text, ForeignKey("products.id"))
    chart_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True))
    tier: Mapped[str | None] = mapped_column(Text)
    amount: Mapped[int | None] = mapped_column(Integer)
    pg_tid: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str | None] = mapped_column(Text)  # pending|paid|refunded|failed
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    refunded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    __table_args__ = (Index("ix_purchases_user_paid", "user_id", "paid_at"),)


class Seal(Base):
    """인장 수집."""
    __tablename__ = "seals"
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id"), primary_key=True)
    lens_id: Mapped[str] = mapped_column(Text, ForeignKey("lenses.id"), primary_key=True)
    got_at: Mapped[datetime] = _ts()


class Review(Base):
    """verified=false 후기에는 '결제 확인됨' 배지를 붙이지 않는다. (표시광고법)"""
    __tablename__ = "reviews"
    id: Mapped[uuid.UUID] = _uuid_pk()
    user_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True))
    report_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("reports.id"))
    lens_id: Mapped[str | None] = mapped_column(Text)
    rating: Mapped[int | None] = mapped_column(SmallInteger)
    body: Mapped[str | None] = mapped_column(Text)
    verified: Mapped[bool] = mapped_column(Boolean, default=False)
    visible: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = _ts()

    __table_args__ = (
        CheckConstraint("rating BETWEEN 1 AND 5", name="ck_reviews_rating"),
    )


# ══════════════════════════════════════════════════════════
# 리텐션
# ══════════════════════════════════════════════════════════
class Notification(Base):
    """하루 1건 제한 — 여러 트리거가 겹치면 우선순위 높은 것 하나만."""
    __tablename__ = "notifications"
    id: Mapped[int] = mapped_column(BIGSERIAL, primary_key=True, autoincrement=True)
    user_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True))
    kind: Mapped[str | None] = mapped_column(Text)   # daily|month|year|birthday|turning|lookback|new_lens
    payload: Mapped[dict | None] = mapped_column(JSONB_OR_JSON)
    send_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    opened_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # 미발송 건만 훑는 부분 인덱스 — 스케줄러가 이걸로 긁는다
    __table_args__ = (
        # 부분 인덱스도 PG 에서만. SQLite 에서는 전체 인덱스로 갑니다.
        Index("ix_notifications_pending", "user_id", "send_at",
              postgresql_where=text("sent_at IS NULL")),
    )


# ══════════════════════════════════════════════════════════
# 계측 — 어디서 나가는지
# ══════════════════════════════════════════════════════════
class Event(Base):
    """
    익명 사건 기록. **사람을 식별할 것이 하나도 없습니다.**

    없는 컬럼이 곧 약속입니다 — 생년월일시·이름·고을·이메일·IP·chart_id.
    chart_id 는 생년월일시 해시라 같은 생일이면 같은 값이 나옵니다.
    그래서 여기 두지 않습니다 (docs/11).

    sid 는 브라우저가 만든 난수입니다. 지우면 끝나고, 사람과 안 이어집니다.
    """
    __tablename__ = "events"
    id: Mapped[int] = mapped_column(BIGSERIAL, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)     # screen|hook_answer|…
    screen: Mapped[str] = mapped_column(Text, nullable=False)   # a1|a3|d2|…
    sid: Mapped[str] = mapped_column(Text, nullable=False)      # 익명 세션 열쇠
    stage: Mapped[int | None] = mapped_column(SmallInteger)     # 훅 몇 번째 단
    ms: Mapped[int | None] = mapped_column(Integer)             # 머문 시간
    n: Mapped[int | None] = mapped_column(Integer)
    yes: Mapped[int | None] = mapped_column(SmallInteger)       # 1=그렇소 0=아니오
    at: Mapped[datetime] = _ts()

    __table_args__ = (
        Index("ix_events_sid", "sid"),
        Index("ix_events_name_screen", "name", "screen"),
        Index("ix_events_at", "at"),
    )
