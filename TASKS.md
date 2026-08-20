# TASKS.md · Claude Code 작업 지시서

각 태스크를 **그대로 복사해서** 터미널의 Claude Code에 붙여넣으세요.
순서대로 진행합니다. 앞 단계가 끝나야 뒤가 의미 있습니다.

---

## 사전 준비

```bash
mkdir sajudang && cd sajudang
git init

# 문서·시드·참조 구현체를 배치
mkdir -p docs seed reference tools
cp ~/Downloads/사주당_개발문서/*.md         docs/
cp ~/Downloads/사주당_개발문서/CLAUDE.md    ./
cp ~/Downloads/사주당_개발문서/seed/*.json  seed/
cp ~/Downloads/sajudang.html                reference/

claude
```

---

# PHASE 1 · 계산엔진 (1~2주)

> **여기가 틀리면 전부 무의미합니다. 다른 걸 먼저 하지 마세요.**

### T1-1 · 프로젝트 스캐폴드

```
docs/02_프로그램명세서.md 를 읽고 모노레포 스캐폴드를 만들어줘.

- services/api  : FastAPI, Python 3.11, poetry
- apps/web      : Next.js 14 App Router, TypeScript
- 공통 타입은 packages/shared-types 에 두고 Pydantic ↔ TS 동기화
- docker-compose 로 postgres 15 + redis 를 띄울 수 있게
- Makefile 에 dev / test / seed 타깃

아직 로직은 만들지 말고 구조와 설정만.
```

### T1-2 · 만세력 ★ 최우선

```
docs/05_계산엔진_사양서.md 를 처음부터 끝까지 읽고
services/api/engine/calendar.py 를 구현해줘.

필수 요구사항:
1. sxtwl 로 24절기 절입 "시각"까지 산출. 근사 테이블 절대 사용 금지.
2. 한국 표준시 변천 4구간 (1908/1912/1954/1961)
3. 서머타임 12구간
4. 진태양시 = (출생지경도 - 표준자오선) * 4분
5. 보정 후 날짜가 넘어가면 일주를 바꿀 것
6. hour_known=False 이면 시주를 None 으로 두고 3주만 반환
7. 자시 정책은 "조자시"로 확정하고 상수로 분리 (나중에 바꿀 수 있게)
8. 일주는 율리우스 일수 기준, 1900-01-01 = 甲戌

함수 시그니처:
  def build_chart(year, month, day, hour, minute, sex, hour_known, city) -> Chart

reference/sajudang.html 의 calc() 함수를 참고하되,
절기·대운수 근사식은 반드시 정식 계산으로 교체할 것.
```

### T1-3 · 검증 ★ UI 전에 반드시

```
tests/test_calendar.py 를 만들어줘.

1. tests/fixtures/charts.json 에 고정 케이스 50건을 만들 것
   - 절입일 전후 ±2일 출생자 10건
   - 2월 1~7일 출생자 10건
   - 자시(23~01시) 출생자 10건
   - 1954~1961년생 5건
   - 서머타임 12구간에서 각 1건씩
   - 일반 케이스 3건
   (기대값은 비워두고, 내가 기존 만세력 앱으로 채우겠다)

2. tools/distribution.py 를 만들어줘
   - 무작위 3,000명 생성
   - 일간 10종 / 십신 10종 / 흐름 5종 / 신강약 분포 출력
   - 어느 값이든 0% 면 에러로 종료 (도달 불가 분기 탐지)
```

### T1-4 · Feature Store

```
docs/05 의 3~8장을 보고 services/api/engine/features.py 를 만들어줘.

- 오행 분포 (지장간 가중 1.0 / 1.0 / 0.3 / 0.2)
- 신강약 (득령 25 + 득지 18 + 비율)  ← 임계값을 상수로 분리
- 용신 (억부법)
- 십신 (일간 제외 천간 3 + 지지 본기 4)
- 대운 (순행/역행, 대운수는 절입일 기준 정식 계산)
- 파생: strong_el, weak_el, gap, flow, flow_el, ilji_chung

flow 판정에서 일간 오행을 반드시 제외할 것.
빼지 않으면 신강 사주가 전부 비겁으로 몰린다.
(참조 구현체에서 실제로 발생했던 버그)

hour_known=False 이면 3주로만 집계.
```

---

# PHASE 2 · 문장엔진 (1주)

### T2-1 · 뱅크 로더

```
seed/bank.json 을 읽어 훅 5단을 조합하는
services/api/engine/bank.py 를 만들어줘.

산출식은 CLAUDE.md 의 "훅 5단 산출식" 그대로.

각 문장에 statement_id 를 부여할 것.
형식: {stage}:{key1}:{key2}  예) stab:love:토

주의: 2.5단(어긋남)은 axis4 가 있고 불일치가 있을 때만 포함.
불일치 0개면 그 단을 아예 넣지 않는다.
```

### T2-2 · 금지어 필터 ★

```
seed/guard.json 을 읽어 출력을 검사하는
services/api/engine/guard.py 를 만들어줘.

- check(text) -> (ok: bool, hits: list[str])
- sanitize(text) -> text  (replacements 적용)
- 위반 시 로그를 남길 것 (나중에 프롬프트 개선에 씀)

모든 API 응답이 이걸 통과하도록 FastAPI 미들웨어로 붙여줘.
```

### T2-3 · 중복률 측정

```
tools/dup_rate.py 를 만들어줘.

- 무작위 3,000명 × 무작위 고민 × 무작위 성향4글자
- 훅 5단 텍스트를 생성해 숫자를 제거한 뒤 유니크 수를 센다
- 단계별 / 전체 중복률 출력
- 목표: 전체 15% 이하

현재 참조 구현체 실측: 성향 입력 시 2.0%, 미입력 시 35.6%
```

---

# PHASE 3 · API (1주)

### T3-1 · DB

```
docs/04_데이터베이스_설계서.md 대로 alembic 마이그레이션을 만들어줘.
seed/*.json 을 lenses / relay_rules 테이블에 넣는 시드 스크립트도.

statement_log 는 인덱스를 빠뜨리지 말 것. 이 테이블이 가장 커진다.
```

### T3-2 · 엔드포인트

```
docs/02 의 5장 API 명세대로 라우터를 구현해줘.

POST /v1/chart     명식 산출 (Redis 캐시, 키는 입력 해시)
POST /v1/hook      훅 5단
POST /v1/report    리포트 (tier 별 잠금 차등)
POST /v1/relay     릴레이 추천
POST /v1/feedback  응답 기록 → statement_log
GET  /v1/daily     오늘의 일진

문장 원문은 절대 응답에 넣지 말고 렌더된 HTML만 내려보낼 것.
```

### T3-3 · 릴레이 엔진

```
seed/relay_rules.json 을 읽어 조건을 평가하는
services/api/engine/relay.py 를 만들어줘.

- priority 내림차순, 이미 읽은/거절한 렌즈 제외, 상위 3개 반환
- forced: 노파·연담 다음엔 청동자를 강제로 앞에 붙임
- breaks 를 반드시 적용:
    세션당 릴레이 2명 (Redis)
    하루 결제 2건
    재회 7일 쿨다운
    하루 3회 접속 시 만류 플래그

브레이크는 설정으로 끌 수 없게 하드하게 넣어줘.
```

---

# PHASE 4 · 프론트 (2~3주)

### T4-1 · 디자인 토큰

```
reference/sajudang.html 의 :root CSS 변수를 추출해
apps/web/styles/tokens.css 로 만들어줘.

--c (캐릭터 테마색)는 런타임에 JS로 교체되어야 한다.
로판 팔레트: 배경 #0C0A12 계열, 강조 로즈골드 #E5B87A / 로즈 #D98BA5 / 라벤더 #A896D4
```

### T4-2 · 진입 플로우

```
reference/sajudang.html 의 a1~a7 화면을 Next.js 컴포넌트로 옮겨줘.

a1 골목(계절 4종) → a2 이름 → a3 생년월일·성별 → a4 때
→ a4b 성향 4글자 → a5 고민 → a6 명식 세우기 → a7 훅 5단

주의:
- a4 "모르오" 는 눈에 띄게. 여기서 막히면 그대로 이탈한다.
- a4b 도 선택 사항. "모르오 · 사주만으로 보겠소" 버튼 유지.
- 계산은 /v1/chart 호출로 대체 (클라 계산 제거)
- 진입 서사 중에는 상단바를 숨기되, a2~a5 에는 "건너뛰기"를 둔다
```

### T4-3 · 나머지 화면

```
reference/sajudang.html 의 나머지 20개 화면을 옮겨줘.
b1~b4, c1~c5, d0~d3, h1, g1~g3, f2, r1

옮긴 뒤 반드시 확인:
- 고아 화면 0 (어디서도 못 가는 화면)
- 막다른 화면 0 (나갈 수 없는 화면)
- 죽은 버튼 0 (onclick 없는 버튼)
```

### T4-4 · 장면 컴포넌트

```
docs/10_에셋_제작발주서.md 를 보고
apps/web/components/scene/ 에 24개 장면 컴포넌트를 만들어줘.

에셋이 아직 없으니 reference/sajudang.html 의 SVG 를 그대로 쓰고,
/scene/{id}/ 에 파일이 있으면 그걸 우선 사용하는 폴백 구조로.

prefers-reduced-motion 이면 poster 정지 이미지로 대체할 것.
```

---

# PHASE 5 · 결제·운영 (1주)

### T5-1 · 결제

```
토스페이먼츠를 붙여줘. 티어 3종 + 구독.
결제 완료 시 reports.unlocked 를 갱신하고 seals 에 인장을 추가.
환불 처리 경로도 만들어둘 것.
```

### T5-2 · 리텐션

```
docs/01 의 5장 리텐션 5층대로 notifications 스케줄러를 만들어줘.

일진(매일) / 절입일 월운 / 입춘 세운 / 생일 / 분기점 / 반기 회고

하루 1건 제한. 여러 트리거가 겹치면 우선순위 높은 것 하나만.
회고 루프는 statement_log 에서 6개월 전 answer=1 문장을 꺼내 쓸 것.
```

---

# 자주 쓰는 지시

```
# 엔진 수정 후
pytest tests/ && python tools/distribution.py

# 문장 추가 후
python tools/dup_rate.py

# 배포 전 점검
"docs/11_법무_컴플라이언스.md 의 체크리스트를 코드베이스 전체에 대해 확인해줘"

# 화면 추가 후
"화면 연결 그래프를 그려서 고아·막다른 화면·죽은 버튼이 있는지 확인해줘"
```

---

# 착수 순서 요약

```
1주차   T1-1 T1-2        스캐폴드 + 만세력
2주차   T1-3 T1-4        검증 + Feature Store   ← 여기 통과 전엔 UI 금지
3주차   T2-1 T2-2 T2-3   문장엔진 + 가드
4주차   T3-1 T3-2 T3-3   DB + API
5~7주차 T4-1 ~ T4-4      프론트
8주차   T5-1 T5-2        결제 + 리텐션
```

**2주차 검증을 통과하지 못하면 3주차로 넘어가지 마세요.**
사주 8글자가 한 글자라도 기존 만세력과 다르면, 그 위에 쌓는 모든 것이 무의미합니다.
