"""초기 스키마 — docs/04_데이터베이스_설계서.md

Revision ID: 0001_initial
Create Date: 2026-08-20

★ 이 파일의 DDL 은 services/api/models.py 에서 뽑아 **고정**한 것입니다.
  모델을 고쳐도 이 마이그레이션은 바뀌지 않습니다. 변경은 새 리비전으로.

  뽑는 법:
      python tools/dump_ddl.py

주의
  - uuid 기본값은 파이썬 쪽(uuid4)에서 넣습니다. DB 의 gen_random_uuid() 를
    쓰려면 pgcrypto 를 켜고 server_default 를 따로 지정하세요.
  - email 은 citext 대신 text + unique 입니다. 대소문자 무시 유일성이
    필요하면 citext 확장을 켜고 타입을 바꾸는 리비전을 추가하세요.
"""
from alembic import op

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None

DDL = """CREATE TABLE cooldowns (
	user_id UUID NOT NULL, 
	kind TEXT NOT NULL, 
	target_hash TEXT NOT NULL, 
	until TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (user_id, kind, target_hash)
);

CREATE TABLE lenses (
	id TEXT NOT NULL, 
	name TEXT NOT NULL, 
	hanja TEXT, 
	school TEXT, 
	group_name TEXT, 
	archetype TEXT, 
	sex VARCHAR(1), 
	you_word TEXT, 
	call TEXT, 
	theme_color TEXT, 
	combine_axis TEXT, 
	focus TEXT[], 
	avoid_domains INTEGER[], 
	taboo TEXT[], 
	handoff JSONB, 
	opening_quote TEXT, 
	pages INTEGER, 
	price INTEGER, 
	released BOOLEAN NOT NULL, 
	sort_order INTEGER, 
	PRIMARY KEY (id)
);

CREATE TABLE notifications (
	id BIGSERIAL NOT NULL, 
	user_id UUID, 
	kind TEXT, 
	payload JSONB, 
	send_at TIMESTAMP WITH TIME ZONE, 
	sent_at TIMESTAMP WITH TIME ZONE, 
	opened_at TIMESTAMP WITH TIME ZONE, 
	PRIMARY KEY (id)
);

CREATE INDEX ix_notifications_pending ON notifications (user_id, send_at) WHERE sent_at IS NULL;

CREATE TABLE relay_log (
	id BIGSERIAL NOT NULL, 
	user_id UUID, 
	chart_id UUID, 
	rule_id TEXT, 
	from_lens TEXT, 
	to_lens TEXT, 
	shown_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	clicked BOOLEAN NOT NULL, 
	purchased BOOLEAN NOT NULL, 
	PRIMARY KEY (id)
);

CREATE INDEX ix_relay_rule_purchased ON relay_log (rule_id, purchased);

CREATE TABLE users (
	id UUID NOT NULL, 
	nickname TEXT, 
	email TEXT, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	last_seen_at TIMESTAMP WITH TIME ZONE, 
	deleted_at TIMESTAMP WITH TIME ZONE, 
	PRIMARY KEY (id), 
	UNIQUE (email)
);

CREATE TABLE charts (
	id UUID NOT NULL, 
	user_id UUID, 
	owner_label TEXT, 
	birth_year SMALLINT NOT NULL, 
	birth_month SMALLINT NOT NULL, 
	birth_day SMALLINT NOT NULL, 
	birth_hour SMALLINT, 
	birth_minute SMALLINT, 
	hour_known BOOLEAN NOT NULL, 
	sex VARCHAR(1) NOT NULL, 
	birth_city TEXT, 
	axis4 VARCHAR(4), 
	features JSONB NOT NULL, 
	engine_ver TEXT NOT NULL, 
	cache_key TEXT NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id), 
	UNIQUE (cache_key)
);

CREATE INDEX ix_charts_cache_key ON charts (cache_key);

CREATE INDEX ix_charts_features_gin ON charts USING gin (features);

CREATE INDEX ix_charts_user_id ON charts (user_id);

CREATE TABLE daily_limits (
	user_id UUID NOT NULL, 
	day DATE NOT NULL, 
	purchases INTEGER NOT NULL, 
	relays INTEGER NOT NULL, 
	visits INTEGER NOT NULL, 
	PRIMARY KEY (user_id, day), 
	FOREIGN KEY(user_id) REFERENCES users (id)
);

CREATE TABLE products (
	id TEXT NOT NULL, 
	name TEXT, 
	engine TEXT, 
	scope TEXT, 
	lens_id TEXT, 
	domain_ids INTEGER[], 
	needs_partner BOOLEAN NOT NULL, 
	needs_photo BOOLEAN NOT NULL, 
	guardrail TEXT, 
	price INTEGER, 
	cooldown_days INTEGER NOT NULL, 
	active BOOLEAN NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(lens_id) REFERENCES lenses (id)
);

CREATE TABLE relay_rules (
	id TEXT NOT NULL, 
	lens_id TEXT, 
	priority INTEGER NOT NULL, 
	condition JSONB NOT NULL, 
	reason_tpl TEXT, 
	quote_tpl TEXT, 
	active BOOLEAN NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(lens_id) REFERENCES lenses (id)
);

CREATE TABLE seals (
	user_id UUID NOT NULL, 
	lens_id TEXT NOT NULL, 
	got_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (user_id, lens_id), 
	FOREIGN KEY(user_id) REFERENCES users (id), 
	FOREIGN KEY(lens_id) REFERENCES lenses (id)
);

CREATE TABLE hooks (
	id UUID NOT NULL, 
	chart_id UUID, 
	lens_id TEXT, 
	concern TEXT NOT NULL, 
	segments JSONB NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(chart_id) REFERENCES charts (id), 
	FOREIGN KEY(lens_id) REFERENCES lenses (id)
);

CREATE TABLE purchases (
	id UUID NOT NULL, 
	user_id UUID, 
	product_id TEXT, 
	chart_id UUID, 
	tier TEXT, 
	amount INTEGER, 
	pg_tid TEXT, 
	status TEXT, 
	paid_at TIMESTAMP WITH TIME ZONE, 
	refunded_at TIMESTAMP WITH TIME ZONE, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id), 
	FOREIGN KEY(product_id) REFERENCES products (id)
);

CREATE INDEX ix_purchases_user_paid ON purchases (user_id, paid_at);

CREATE TABLE reports (
	id UUID NOT NULL, 
	chart_id UUID, 
	lens_id TEXT, 
	product_id TEXT, 
	tier TEXT, 
	concern TEXT, 
	unlocked TEXT[], 
	engine_ver TEXT, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(chart_id) REFERENCES charts (id), 
	FOREIGN KEY(lens_id) REFERENCES lenses (id), 
	FOREIGN KEY(product_id) REFERENCES products (id)
);

CREATE TABLE statement_log (
	id BIGSERIAL NOT NULL, 
	statement_id TEXT NOT NULL, 
	chart_id UUID, 
	user_id UUID, 
	lens_id TEXT, 
	concern TEXT, 
	stage TEXT, 
	day_gan VARCHAR(1), 
	strength TEXT, 
	top_ten_god TEXT, 
	weak_el VARCHAR(1), 
	strong_el VARCHAR(1), 
	flow TEXT, 
	axis4 VARCHAR(4), 
	answer SMALLINT, 
	answered_at TIMESTAMP WITH TIME ZONE, 
	shown_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(chart_id) REFERENCES charts (id)
);

CREATE INDEX ix_stmt_chart ON statement_log (chart_id);

CREATE INDEX ix_stmt_shown_at ON statement_log (shown_at);

CREATE INDEX ix_stmt_statement_answer ON statement_log (statement_id, answer);

CREATE INDEX ix_stmt_user_shown ON statement_log (user_id, shown_at);

CREATE TABLE report_cuts (
	report_id UUID NOT NULL, 
	seq INTEGER NOT NULL, 
	kind TEXT, 
	statement_id TEXT, 
	body JSONB, 
	locked BOOLEAN NOT NULL, 
	PRIMARY KEY (report_id, seq), 
	FOREIGN KEY(report_id) REFERENCES reports (id) ON DELETE CASCADE
);

CREATE TABLE reviews (
	id UUID NOT NULL, 
	user_id UUID, 
	report_id UUID, 
	lens_id TEXT, 
	rating SMALLINT, 
	body TEXT, 
	verified BOOLEAN NOT NULL, 
	visible BOOLEAN NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT ck_reviews_rating CHECK (rating BETWEEN 1 AND 5), 
	FOREIGN KEY(report_id) REFERENCES reports (id)
);
"""

TABLES = ['cooldowns', 'lenses', 'notifications', 'relay_log', 'users', 'charts', 'daily_limits', 'products', 'relay_rules', 'seals', 'hooks', 'purchases', 'reports', 'statement_log', 'report_cuts', 'reviews']


def upgrade() -> None:
    """
    Postgres 는 위에 **고정해 둔 DDL** 을 그대로 씁니다. 운영 스키마의
    authority 는 그 문자열입니다.

    그 밖의 방언(SQLite)은 models.py 에서 그때그때 만듭니다.
    위 DDL 은 UUID·JSONB·BIGSERIAL 을 쓰는 Postgres 문법이라 SQLite 가
    읽지 못합니다. models.py 가 방언 중립이라 같은 스키마가 나오고,
    create_all 이 ddl_if 를 알아서 지켜 GIN 같은 PG 전용 인덱스는
    건너뜁니다.
    """
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute(DDL)
        return

    import models
    models.Base.metadata.create_all(bind, checkfirst=False)


def downgrade() -> None:
    cascade = " CASCADE" if op.get_bind().dialect.name == "postgresql" else ""
    for t in reversed(TABLES):
        op.execute("DROP TABLE IF EXISTS %s%s" % (t, cascade))
