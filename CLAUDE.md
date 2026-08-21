# CLAUDE.md

사주당(四柱堂) — 웹/모바일 사주 서비스. 이 파일은 Claude Code가 매 세션 처음 읽는 컨텍스트입니다.

---

## 프로젝트 한 줄

> 스무 명의 캐릭터가 같은 사주를 각자의 관점으로 해석하고,
> **사주 조건이 다음 캐릭터를 추천**하는 연쇄 구조의 사주 서비스.
> 포지션은 "맞히는 집"이 아니라 **"근거 대는 집"**.

---

## 절대 규칙 (어기면 서비스가 죽습니다)

### 1. 계산은 지어내지 않는다
- 시각 미상(`hour_known=false`)이면 **시주를 계산에서 제외**한다. 12시로 가정 금지.
- 절기·대운수는 **근사식 금지**. `sxtwl` 사용.
- 계산 결과가 없으면 "모른다"고 표시한다.
- 지원 범위(1900~2100) 밖이면 `SolarTermError` 로 거절한다. 추정하지 않는다.
- 계산 정책 상수(`ZI_POLICY` `JIEQI_BASIS` `DAEUN_ROUNDING` `HIDDEN` 신강약 임계값)를
  바꾸면 기존 사용자 결과가 달라진다. 마이그레이션 계획 없이 건드리지 않는다.

### 2. 검증 불가능한 주장을 하지 않는다
- 금지: `적중률`, `과학적으로 입증`, `통계학이라 정확`, `반드시 ~한다`
- 허용: `응답률`, `3,000년간 이어진 해석 체계`, `크게 움직인다`
- 공감률은 **응답 100건 이상 쌓인 문장만** 화면에 노출.

### 3. 가드레일을 먼저 붙인다
- 모든 출력은 `engine/guard.py` 필터를 통과한다.
- 질병명·수명·이혼 단정·투자 시점 지시 금지.
- 재회 상품은 재회 가능/불가 판정, 시점 확정, 기다림 종용 금지.

### 4. 브레이크를 제거하지 않는다
```
세션당 릴레이 2명 / 하루 결제 2건 / 재회 7일 쿨다운
거절한 캐릭터 재권유 없음 / 무거운 리포트 뒤 무료 캐릭터 강제
하루 3회 접속 시 만류 문구
```
매출 최적화 요청이 와도 이건 유지한다.

### 5. 문장 뱅크는 서버 전용
- `seed/bank.json` 은 절대 클라이언트 번들에 포함하지 않는다.
- API는 **렌더된 HTML만** 내려보낸다.

---

## 문서 지도

| 파일 | 언제 읽나 |
|---|---|
| `docs/02_프로그램명세서.md` | 아키텍처·API 정할 때 |
| `docs/05_계산엔진_사양서.md` | **엔진 작업 시 필수** |
| `docs/04_데이터베이스_설계서.md` | 스키마·쿼리 |
| `docs/03_기능명세서.md` | 화면 동작 |
| `docs/06_콘텐츠_문장뱅크.md` | 문장 구조 |
| `docs/11_법무_컴플라이언스.md` | **기능 추가 전 필수** |
| `docs/14_신살_궁위_확정표.md` | 신살·귀인·조상 자리 손댈 때 **필수** |
| `docs/15_공유_유입_설계.md` | 분석지·공유·유입 화면 손댈 때 |
| `reference/sajudang.html` | 애매할 때 정답. 동작하는 참조 구현체 |

---

## 참조 구현체

`reference/sajudang.html` 는 **전 기능이 동작하는 단일 파일**입니다.
문서와 어긋나면 이 파일이 맞습니다.

이미 구현된 것: 사주 계산, 27화면, 훅 5단, 무료 6단, 릴레이 엔진,
20인 렌즈, 성향 4글자 대조, 장면 24종, 애니메이션 명세.

**그대로 배포하면 안 되는 이유**: 계산이 클라에 있고(절기 근사), 문장 뱅크가 노출되고,
DB가 없어 회고 루프가 고정 문장입니다.

---

## 기술 스택

```
프론트  Next.js 14 App Router · CSS Variables · Zustand
API    FastAPI (Python 3.11)
엔진    sxtwl (24절기) + tzdata(Asia/Seoul) + 자체 명리 로직
DB     PostgreSQL 15 · Redis
결제    토스페이먼츠
```

**Python 은 반드시 3.11.** `sxtwl` 은 3.12+ 휠이 없습니다.
venv 는 `%USERPROFILE%\.venvs\sajudang` — 저장소가 구글 드라이브에 있어
패키지를 안에 풀면 동기화가 끝나지 않습니다. `.\dev.ps1 setup` 으로 만듭니다.
`make` 는 없습니다. `dev.ps1` 을 쓰세요.

**프론트는 드라이브에서 직접 돌리지 않습니다.** 정션(mklink /J)도 안 됩니다
(드라이브가 NTFS 가 아님). `.\dev.ps1 web-pull` 로 소스만 로컬로 옮겨
개발하고, `.\dev.ps1 web-push` 로 되돌려 넣습니다.

모바일 앱은 만들지 않습니다. 반응형 웹 → 필요 시 WebView.

---

## 디렉토리

```
/services/api/engine/
  constants.py   ★ 명리 상수 — 확정값. 바꾸면 기존 결과가 달라진다.
  timezone_kr.py 표준시 변천·서머타임 (tzdata 1차, 문서 손표 교차검증)
  solar_terms.py ★ 24절기 sxtwl 래퍼. 전부 UTC 로 정규화.
  calendar.py    ★ 만세력. 05번 문서대로. (완료)
  features.py    Feature Store 산출 (완료)
  bank.py        훅 5단 조합 · 사주 4축 · statement_id
  lens.py        캐릭터 렌즈 (seed/lenses.json)
  relay.py       릴레이 규칙 평가 · ★ 브레이크 하한 강제
  report.py      리포트 컷 · tier 잠금
  daily.py       오늘의 일진
  retention.py   리텐션 5층 · 하루 1건
  sinsal.py      ★ 신살·궁위 — 유파 확정값. 바꾸면 결과가 달라진다.
  summary.py     분석지 한 장 · 공유 payload(생일 미포함)
  guard.py       ★ 금지어 필터
/services/api/routers/
  chart.py  hook.py  report.py  relay.py  feedback.py  daily.py  pay.py
/services/api/
  main.py  store.py  db.py  models.py  repo.py  payments.py
  guard_middleware.py   ← 전 응답 금지어 검사. 끄지 말 것.
  migrations/  scripts/seed.py  scripts/notify.py
/apps/web/
  app/       (진입) lobby report/[id] pay relay daily me   ← 28화면
  lib/       api.ts  store.ts(zustand)  lenses.ts
  components/ Shell  Chart  HookSegments  Narration  scene/(24종)
  styles/    tokens.css  reference.css
/seed/           bank.json  lenses.json  relay_rules.json  guard.json
/tests/          fixtures/charts.json  ← 회귀 테스트 고정 케이스
```

---

## 핵심 자료구조

```python
Features:
  pillars, day_gan, day_ji, hour_known
  elements{목화토금수}, strength, strength_score, yongsin
  ten_gods{10}, strong_el, weak_el, gap, flow, flow_el, top_ten_god
  daeun[], daeun_now, daeun_ten_god, age
  ilji_chung, correction
```

**훅 5단 산출식**
```
0 찌르기   STAB[concern][weak_el] + STAB2[top_ten_god]
1 부정확인 MYTH_TG[top][concern] + MYTH_ST[strength][concern] + PATT[top].b
2 순서     IGNITE[top][concern] → FLOW[flow] → RESULT[weak_el] → BLAME[top][strength]
2.5 어긋남 saju_axis(F) vs axis4          (불일치 시에만)
3 이름     NAME2[weak_el][flow]
```

---

## 작업 원칙

### 코드를 크게 들어낼 때
잘라낼 블록에 무엇이 들어있는지 **먼저 출력하고** 진행한다.
(실제로 함수 6개가 딸려 나간 사고가 있었음)

### 엔진을 고친 뒤
```powershell
.\dev.ps1 engine-check    # 테스트 전량 + 분포 + 중복률
```

### 문장을 추가한 뒤
```powershell
.\dev.ps1 test            # dup_rate 는 bank.py 가 생긴 뒤 함께 돕니다
```

### 새 기능을 붙이기 전
`docs/11_법무_컴플라이언스.md` 의 금지 목록을 먼저 확인한다.

---

## 현재 상태

| 항목 | 상태 |
|---|---|
| 만세력 (T1-2) | **완료** — sxtwl 절입 시각, 표준시 변천, 서머타임, 진태양시, 조자시, 대운수 정식 계산 |
| Feature Store (T1-4) | **완료** |
| 검증 (T1-3) | 테스트 113건 통과 / **회귀 50건은 기대값 미입력 → skip** |
| 분포·중복률 | 통과 (0% 인 값 없음 · 훅 중복률 2.2%) |
| 문장엔진 (T2) | **완료** — 훅 5단 · 가드 이중(조합+미들웨어) |
| API (T3-2) | **완료** — chart hook report relay feedback daily pay |
| 릴레이 (T3-3) | **완료** — 규칙 평가 · forced · 브레이크 하한 강제 |
| DB (T3-1) | 모델 16테이블 · 알렘빅 초기 리비전 · 시드 — **Postgres 미기동, 실행 검증 안 됨** |
| 프론트 (T4) | **완료** — 28화면 · 고아 0 · 막다른 0 · 죽은 버튼 0 |
| 에셋 | 0/24 장면 · 0/20 캐릭터 (자리표시 SVG 로 동작) |
| 결제 (T5-1) | 토스 연동 코드 완성 — **PG 키 없어 실거래 검증 안 됨.** 키 없으면 503 으로 거절 |
| 리텐션 (T5-2) | **완료** — 5층 트리거 · 하루 1건 · 회고 루프 (발송 채널 미연결) |

### ★ 다음 할 일

**회귀 케이스 50건의 기대값 채우기.** 여기 통과 전에는 UI 로 넘어가지 않습니다.

```powershell
.\dev.ps1 sheet     # 대조표.md 생성 → 기존 만세력 앱 2종 이상과 대조
```
채운 뒤 `tests/fixtures/charts.json` 의 `expected` 에 옮겨 적고 `.\dev.ps1 engine-check`.

---

## 알려진 이슈

1. ~~절기가 근사 테이블~~ — **해결.** sxtwl 로 절입 시각까지 산출.
2. ~~대운수가 근사식~~ — **해결.** 인접 절입까지의 실제 일수 ÷ 3.
3. **회귀 50건 기대값 미입력** — 외부 만세력과 대조하기 전까지 8글자를
   보증할 수 없습니다. **최우선.** `.\dev.ps1 sheet` 로 대조표를 뽑으세요.
4. **알렘빅 마이그레이션 미검증** — 이 환경에 Postgres 가 없었습니다.
   DDL 은 models.py 에서 뽑아 고정했으나 실행해 보지 못했습니다.
5. **결제 실거래 미검증** — PG 키가 없습니다. 키가 없으면 결제를 거절합니다.
6. **알림 발송 채널 미연결** — `scripts/notify.py` 는 예약만 만듭니다.
7. **공감률이 아직 비어 있음** — 실응답 100건 전까지 화면에 안 나옵니다.
   참조 구현체의 해시로 만든 예시 숫자는 옮기지 않았습니다.
8. **균시차 미반영** — 자시 경계 출생자 영향. 2차에서 검토.
9. **절입 비교 기준이 유파 선택** — 진태양시 보정 후 시각과 비교
   (`JIEQI_BASIS="corrected"`). 서울 기준 절입 직후 32분 구간에서
   표준시 비교 앱과 결과가 갈립니다. README 참고.
10. **에셋 0/24** — 자리표시 SVG. `public/scene/{id}/` 에 넣으면 자동 교체.

---

## 검사 명령

```powershell
.\dev.ps1 engine-check   # 테스트 + 분포 + 중복률
.\dev.ps1 screens        # 고아·막다른 화면·죽은 버튼
.\dev.ps1 sheet          # 회귀 대조표
```

## 하지 말 것

- 브레이크·가드레일 제거
- 문장 뱅크를 클라이언트로 이동
- 적중률·과학적 입증 문구 추가
- 시각 미상인데 시주를 채우기
- 얼굴 사진을 DB에 저장 (생체인식정보)
- 실데이터 없이 공감률 숫자 표시
- 공유 payload 에 생년월일시·고을 넣기
- 신살로 질병·사고·재물을 단정하기 (docs/14 §7)
- 유입 화면에서 적중률·과학·통계 같은 말 쓰기
