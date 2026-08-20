# 사주당 四柱堂

> 스무 명의 캐릭터가 같은 사주를 각자의 관점으로 해석하고,
> **사주 조건이 다음 캐릭터를 추천**하는 연쇄 구조의 사주 서비스.
> 포지션은 "맞히는 집"이 아니라 **"근거 대는 집"**.

세션 컨텍스트는 `CLAUDE.md`, 작업 지시서는 `TASKS.md`, 설계 문서는 `docs/` 에 있습니다.

---

## 지금 어디까지 되어 있나

| 단계 | 상태 |
|---|---|
| T1-1 스캐폴드 | ✅ 모노레포 · FastAPI · Next.js 14 · docker-compose |
| T1-2 만세력 | ✅ sxtwl 절입 시각 · 표준시 변천 · 서머타임 · 진태양시 · 조자시 · 대운수 정식 계산 |
| T1-3 검증 | ⚠️ 불변식·API·엔진 테스트 113건 통과 / **회귀 50건은 기대값 미입력 (skip)** |
| T1-4 Feature Store | ✅ 오행·신강약·용신·십신·대운·파생값 |
| T2-1 뱅크 로더 | ✅ 훅 5단 조합 · statement_id 부여 |
| T2-2 금지어 필터 | ✅ 조합 단계 + 전 응답 미들웨어 (이중) |
| T2-3 중복률 | ✅ **2.2%** (목표 15% 이하) |
| T3-1 DB | ⚠️ 모델 16테이블 · 알렘빅 초기 리비전 · 시드 스크립트 — **Postgres 미기동으로 실행 검증 안 됨** |
| T3-2 엔드포인트 | ✅ chart · hook · report · relay · feedback · daily · pay |
| T3-3 릴레이 엔진 | ✅ 규칙 평가 · forced · 브레이크 하드코딩 |
| T4-1 디자인 토큰 | ✅ 로판 팔레트 · 일간 10색 · 참조 CSS 이식 |
| T4-2~3 화면 | ✅ **28화면 · 고아 0 · 막다른 0 · 죽은 버튼 0** |
| T4-4 장면 | ✅ 24종 컴포넌트 + 폴백 (에셋 0/24, 자리표시 SVG) |
| T5-1 결제 | ⚠️ 토스페이먼츠 연동 코드 완성 — **PG 키 없어 실거래 검증 안 됨** |
| T5-2 리텐션 | ✅ 5층 트리거 · 하루 1건 · 우선순위 · 회고 루프 |

**다음에 할 일**: 회귀 케이스 50건의 기대값 채우기. 아래 "2주차 관문" 참고.

---

## 배포

| | |
|---|---|
| 저장소 | https://github.com/lhs0609a-cpu/sajudang |
| 프론트 | https://sajudang-three.vercel.app |

`main` 에 push 하면 Vercel 이 자동 배포합니다. (Root Directory `apps/web`, npm workspaces)

### ⚠ 지금 배포본은 명식을 세우지 못합니다

프론트만 올라가 있고 **계산 API 는 아직 어디에도 없습니다.**
`NEXT_PUBLIC_API_BASE` 가 없으면 화면 상단에 그 사실을 알리는 띠가 뜹니다
(조용히 실패하지 않게). 화면·서사·릴레이 UI 는 볼 수 있습니다.

FastAPI 는 `sxtwl`(C++ 확장)이 필요해 Vercel 서버리스에 맞지 않습니다.
컨테이너 호스팅(Render·Railway·Fly·AWS ECS)에 `services/api` 를 올린 뒤:

```bash
# Vercel 환경변수 등록 후 재배포
vercel env add NEXT_PUBLIC_API_BASE production   # 예: https://api.sajudang.com
vercel --prod
```

API 쪽에는 CORS 허용 출처에 배포 도메인을 넣어야 합니다
(`services/api/main.py` 의 `allow_origins`).

### 배포 보호

Vercel 팀 프로젝트는 기본으로 로그인해야 열립니다(Vercel Authentication).
공개 사이트로 쓰려고 껐습니다. 다시 잠그려면
Vercel 대시보드 → Project → Settings → Deployment Protection 에서 켜세요.

---

## 개발 환경

### 왜 Python 3.11 인가

`sxtwl`(24절기 정밀 계산)은 **3.12 이상용 휠이 없습니다.** 3.14 에서는
소스 빌드가 필요하고 MSVC 없이는 실패합니다. 3.11 을 씁니다.

### ★ 구글 드라이브 위에서 개발할 때

이 저장소는 구글 드라이브 폴더에 있습니다. 드라이브 마운트는 파일 쓰기가
로컬 대비 **약 170배 느립니다**(파일당 약 2초).

- **venv** 는 `%USERPROFILE%\.venvs\sajudang` — 드라이브 밖입니다.
- **node_modules** 도 드라이브 밖에 두고 **정션(junction)으로 연결**합니다.
  `.\dev.ps1 web-setup` 이 알아서 만듭니다. 3만 개 파일을 드라이브에 풀면
  동기화가 끝나지 않습니다.
- `.gitignore` 에 둘 다 들어 있습니다.

### 설치

```powershell
pip install uv          # 없으면
.\dev.ps1 setup         # Python 3.11 venv + 의존성
.\dev.ps1 web-setup     # node_modules 정션 + npm install
```

`Makefile` 도 있지만 Windows 에는 make 가 없습니다. `dev.ps1` 을 쓰세요.

---

## 자주 쓰는 명령

```powershell
.\dev.ps1 test           # 테스트 전량
.\dev.ps1 engine-check   # ★ 2주차 관문
.\dev.ps1 dist           # 분포 검증 (3,000명)
.\dev.ps1 dup            # 훅 중복률
.\dev.ps1 screens        # 화면 연결 그래프 — 고아·막다른·죽은 버튼
.\dev.ps1 sheet          # 회귀 케이스 대조표 → 대조표.md
.\dev.ps1 api            # http://localhost:8000/docs
.\dev.ps1 web            # http://localhost:3000
```

```powershell
# 명식 하나 뽑아보기
curl -X POST http://localhost:8000/v1/chart -H "Content-Type: application/json" `
  -d '{"year":1993,"month":5,"day":15,"hour":10,"minute":20,"hour_known":true,"sex":"F","birth_city":"서울"}'
```

---

## ★ 2주차 관문 — 여기 통과 전엔 UI 를 믿지 마세요

```powershell
.\dev.ps1 engine-check
```

1. `pytest` — 불변식 + API + 결제/리텐션 113건, **회귀 50건**
2. `tools/distribution.py` — 3,000명 분포에 0% 인 값이 없을 것
3. `tools/dup_rate.py` — 중복률 15% 이하 (현재 2.2%)

지금 회귀 50건은 기대값이 비어 있어 skip 됩니다. 채우는 법:

```powershell
.\dev.ps1 sheet          # 대조표.md 생성
```

대조표의 `입력` 열을 **기존 만세력 앱 2종 이상**에 그대로 넣고, 나온 값을
`tests/fixtures/charts.json` 의 `expected` 에 옮겨 적으세요.
`?` 가 하나라도 남아 있으면 그 케이스는 skip 됩니다.

> 사주 8글자가 한 글자라도 기존 만세력과 다르면, 그 위에 쌓는 모든 것이
> 무의미합니다.

---

## 아직 검증되지 않은 것

정직하게 적어 둡니다. 코드는 있지만 **실제로 돌려보지 못한 것**들입니다.

| 항목 | 왜 |
|---|---|
| 알렘빅 마이그레이션 | 이 환경에 Postgres 가 없습니다. DDL 은 models.py 에서 뽑아 고정했으나 실행 검증은 안 됐습니다. |
| 토스페이먼츠 실거래 | PG 키가 없습니다. 키가 없으면 결제를 **거절**하도록 해 두었습니다(503). 성공한 척하지 않습니다. |
| 알림 발송 | `scripts/notify.py` 는 예약만 만듭니다. 실제 발송 채널(푸시·메일)은 미연결. |
| 회귀 50건 | 외부 만세력 대조가 필요합니다. |
| 에셋 24종 | 0/24. 자리표시 SVG 로 돌아갑니다. |

---

## 계산 정책 — 확정값

바꾸면 **기존 사용자의 결과가 달라집니다.** 변경 시 마이그레이션 계획 먼저.

| 항목 | 값 | 위치 |
|---|---|---|
| 자시 | **조자시** (23:00~23:59 → 익일 일주) | `engine/calendar.py: ZI_POLICY` |
| 절입 비교 기준 | **진태양시 보정 후 시각** | `engine/calendar.py: JIEQI_BASIS` |
| 대운수 나머지 | **반올림**, 최소 1 | `engine/calendar.py: DAEUN_ROUNDING` |
| 지장간 배분·가중 | docs/05 §3 표 (본기 1.0 / 중기 0.3 / 여기 0.2) | `engine/constants.py: HIDDEN` |
| 신강약 임계 | 신강 ≥ 20 / 신약 ≤ −10 | `engine/constants.py` |
| 표준시·서머타임 | IANA `Asia/Seoul` (문서의 손표와 교차검증) | `engine/timezone_kr.py` |
| 균시차 | 미반영 (2차 검토) | docs/05 §1-5 |
| 지원 범위 | 1900~2100년 | `engine/solar_terms.py` |
| 공감률 노출 하한 | **응답 100건** | `repo.py: MIN_RESPONSES_TO_SHOW` |
| 브레이크 | 세션 릴레이 2 · 하루 결제 2 · 재회 7일 · 3회 만류 | `engine/relay.py: BREAKS()` |

### 절입 비교 기준에 대하여

절입 시각은 특정 순간이므로, 출생 시각과 절입 시각을 **같은 프레임**에서
비교해야 합니다. 이 엔진은 문서(docs/05 §1-4)와 참조 구현체를 따라
**진태양시로 보정한 시각**을 기준으로 비교합니다. 서울은 −32.1분이므로
공표 절입 시각 직후 32분 안에 태어난 사람은 아직 전월(전년)로 잡힙니다.

표준시 그대로 비교하는 만세력 앱과는 **이 구간에서만** 결과가 갈립니다.
`JIEQI_BASIS = "standard"` 로 바꾸면 그쪽 방식이 됩니다.
회귀 케이스를 채울 때 대조 앱이 어느 방식인지 확인하세요.

---

## 브레이크 — 지우지 마세요

```
세션당 릴레이 2명 / 하루 결제 2건 / 재회 7일 쿨다운
거절한 캐릭터 재권유 없음 / 무거운 리포트 뒤 무료 캐릭터 강제
하루 3회 접속 시 만류 문구
```

- 판정은 **전부 서버**에서 합니다. 프론트는 표시만 합니다.
- `engine/relay.py: BREAKS()` 가 시드 값에 **하한을 강제**합니다.
  `seed/relay_rules.json` 을 고쳐 느슨하게 만들 수 없습니다.
- 테스트가 이걸 지키고 있습니다: `tests/test_bank.py::test_breaks_cannot_be_loosened_by_seed`

매출 최적화 요청이 와도 이 값들은 유지합니다.

---

## 디렉토리

```
CLAUDE.md            세션 컨텍스트
TASKS.md             작업 지시서
dev.ps1 / Makefile   개발 명령
alembic.ini          마이그레이션
docs/                설계 문서 00~13
seed/                bank · lenses · relay_rules · guard · ilgan · meta
reference/
  sajudang.html      동작하는 참조 구현체 (문서와 어긋나면 이게 정답)
services/api/
  main.py            FastAPI + 가드 미들웨어
  store.py           Redis(없으면 메모리) 캐시·카운터
  db.py  models.py   SQLAlchemy · 16테이블
  repo.py            statement_log 기록·집계
  payments.py        토스페이먼츠
  guard_middleware.py 전 응답 금지어 검사 (안전망)
  routers/           chart hook report relay feedback daily pay
  migrations/        알렘빅
  scripts/           seed.py  notify.py
  engine/
    constants.py     ★ 명리 상수 — 확정값
    timezone_kr.py   표준시 변천 · 서머타임
    solar_terms.py   ★ 24절기 (sxtwl)
    calendar.py      ★ 만세력
    features.py      ★ Feature Store
    bank.py          훅 5단 조합
    lens.py          캐릭터 렌즈
    relay.py         릴레이 · 브레이크
    report.py        리포트 컷 · tier 잠금
    daily.py         오늘의 일진
    retention.py     리텐션 5층
    guard.py         금지어 필터
apps/web/            Next.js 14 App Router — 28화면
  lib/               api · store(zustand) · lenses
  components/        Shell · Chart · HookSegments · Narration · scene/
  app/               (진입) lobby report/[id] pay relay daily me
packages/shared-types/  Pydantic ↔ TS 공용 타입
tools/               distribution · dup_rate · make_fixtures
                     fixture_sheet · screen_graph · dump_ddl
tests/               불변식 · 문장엔진 · API · 결제/리텐션 · 회귀
```

---

## 하지 말 것

- 브레이크·가드레일 제거
- 문장 뱅크를 클라이언트로 이동
- 적중률·과학적 입증 문구 추가
- 시각 미상인데 시주를 채우기
- 얼굴 사진을 DB에 저장 (생체인식정보)
- 실데이터 없이 공감률 숫자 표시
