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
| `docs/16_신살인물_에셋발주서.md` | 신살 인물·에셋 |
| `docs/17_배포_운영_설계.md` | **배포·환경변수·CORS·상태 저장** |
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
  bank.py        훅 5단 조합 · 사주 4축(겹친 자리/어긋난 자리) · statement_id
  lens.py        캐릭터 렌즈 · 관점 · ★ 결합 축의 추가 입력 집계
  lens_cuts.py   ★ 관점 컷 — 그 캐릭터만 보는 자리. 축 셋을 곱한다
                 값이 오를수록 자기 몫 컷이 많다 (자기 몫 = 추가 입력 + 관점)
                 ★ OWN_FLOOR — 값 등급이 요구하는 관점 컷 수. 표는 여기 한 벌
  extras.py      ★ 추가 입력 — 상대 사주 · 현재 상황 · 혈액형 · 그림 · 패
                 저장하지 않습니다. 얼굴 사진은 여기 없습니다(생체인식정보)
  relay.py       릴레이 규칙 20개 평가 · ★ 재순위 · ★ 브레이크 하한 강제
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
                 lens_view.json  lens_cuts.json  extras.json  sinsal.json
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

### 초반을 고치기 전
```powershell
.\dev.ps1 funnel          # 어디서 나가는가 (FUNNEL_KEY 필요)
```
감으로 고치지 않는다. 고친 뒤 같은 명령으로 다시 본다.

★ 계측에 개인정보를 싣지 않는다. 화면 이름·사건 이름은 화이트리스트이고
`chart_id` 도 넣지 않는다 (생년월일시 해시 = 준식별자).

---

## 배포

```
프론트   https://sajudang-three.vercel.app   Vercel · main push 자동
API     https://sajudang-api.fly.dev        Fly nrt · fly deploy --remote-only
```

배포 전 반드시 `/health` 의 `store.durable` 이 true 인지 보세요.
false 면 브레이크가 풀린 채로 도는 것입니다. 상세는 docs/17.

---

## 현재 상태

| 항목 | 상태 |
|---|---|
| 만세력 (T1-2) | **완료** — sxtwl 절입 시각, 표준시 변천, 서머타임, 진태양시, 조자시, 대운수 정식 계산 |
| Feature Store (T1-4) | **완료** |
| 검증 (T1-3) | **테스트 446건 전량 통과 · skip 0.** 회귀 50건은 독립 계산(`crosscheck`)으로 채워 잠갔습니다 |
| 교차검증 | sxtwl 없는 독립 계산과 절입 1,452건 · 여덟 글자 전량 일치 (`.\dev.ps1 crosscheck`) |
| 분포·중복률 | 통과 — 훅 중복률 0.1% · 유료 컷 최다 점유 전부 2% 이하 |
| 릴레이 쏠림 | 규칙 20개 · 재순위(λ=0.5) — 최다 1순위 21.4% · 1순위·상위3 모두 **20/20 도달** |
| 추가 입력 | 결합 축 6종 구현 (axis4 · 출생지 · 혈액형 · 이미지 · 카드 · 상대 사주 · 현재 상황). 얼굴 사진만 보류 |
| 값 사다리 | **완료** — 관점 컷 92개. 여섯 등급이 전부 다른 분량 (19/17/15/13/12/11컷). 값 ↔ 컷수 상관 +0.984. 자기 몫 2 → 8컷 |
| 문장엔진 (T2) | **완료** — 훅 5단 · 가드 이중(조합+미들웨어) |
| API (T3-2) | **완료** — chart hook report relay feedback daily pay |
| 릴레이 (T3-3) | **완료** — 규칙 평가 · forced · 브레이크 하한 강제 |
| DB (T3-1) | 17테이블 · 리비전 3 · **SQLite 로 마이그레이션 왕복 검증 완료**. Postgres 실행은 아직 |
| 프론트 (T4) | **완료** — 28화면 · 고아 0 · 막다른 0 · 죽은 버튼 0 |
| 에셋 | 0/24 장면 · 0/20 캐릭터 (자리표시 SVG 로 동작) |
| 결제 (T5-1) | 토스 SDK 연동 완료(v2 standard · 결제창 → successUrl → 승인). **PG 키 없어 실거래만 미검증.** 키 없으면 503 |
| 계측 | **완료** — `/v1/events` · `/v1/funnel` · 화면별 도달·훅 단별 응답률. 개인정보 컬럼 없음 |
| 리텐션 (T5-2) | **완료** — 5층 트리거 · 하루 1건 · 회고 루프 (발송 채널 미연결) |

### ★ 다음 할 일

**만세력 앱 대조 20건.** 회귀 50건의 기대값은 독립 계산으로 채워
넣었지만, 그 두 계산은 **같은 유파를 공유합니다** — 조자시 정책과
절입 비교 기준. 그건 계산이 아니라 **선택**이라 바깥에서 봐야 압니다.

```powershell
.\dev.ps1 plan               # 무엇부터 볼지 (zi 10건 · jieqi 10건)
.\dev.ps1 sheet              # 대조표.md
# 만세력 앱 2종 이상에서 읽어 아래 형식으로 받아적고
#     jieqi-01  戊辰 甲寅 丁巳 己酉  1
.\dev.ps1 fill 받아적음.txt          # 대조만
.\dev.ps1 fill 받아적음.txt --write  # 맞으면 fixtures 에 써넣음
.\dev.ps1 engine-check
```
손으로 옮겨 적지 마세요. `fill` 이 대조까지 합니다. 확인한 건은
`needs_external_check` 표가 지워지고 `expected_source` 가 `만세력앱`
으로 바뀝니다. 유파가 갈리는 자리는 도구가 짚어 줍니다 — 다르다고
곧 버그가 아닙니다.

그 다음은 **에셋**(장면 0/24 · 캐릭터 0/20)과 **PG 키·알림 채널**입니다.

---

## 알려진 이슈

1. ~~절기가 근사 테이블~~ — **해결.** sxtwl 로 절입 시각까지 산출.
2. ~~대운수가 근사식~~ — **해결.** 인접 절입까지의 실제 일수 ÷ 3.
3. ~~회귀 50건 기대값 미입력~~ — **해결.** `tools/crosscheck.py` 의 독립
   계산(sxtwl 없이 Meeus 로 절입을 직접 품)으로 50건 전부 채웠고 회귀가
   잠겼습니다. **다만 유파 확인 20건이 남았습니다** — 두 계산이 같은
   조자시·절입 기준을 쓰기 때문입니다. `.\dev.ps1 plan` 참고.
4. ~~알렘빅 마이그레이션 미검증~~ — **해결.** 모델을 방언 중립으로 바꿔
   SQLite 로 `upgrade head → downgrade base → upgrade head` 를 돌립니다
   (`.\dev.ps1 migrate-sqlite`). Postgres 용 고정 DDL 은 그대로입니다.
   Postgres **실행** 검증은 아직입니다.
5. **결제 실거래 미검증** — PG 키가 없습니다. 키가 없으면 결제를 거절합니다.
6. **알림 발송 채널 미연결** — `scripts/notify.py` 는 예약만 만듭니다.
   ★ 붙이기 전에 정할 것: 일진은 **매일** 잡힙니다(1년 365건 중 352건).
   앱에서 보여줄 것인지 매일 밀어낼 것인지 결정해야 합니다.
7. **공감률이 아직 비어 있음** — 실응답 100건 전까지 화면에 안 나옵니다.
   참조 구현체의 해시로 만든 예시 숫자는 옮기지 않았습니다.
   나올 때는 **Wilson 하한**으로 나갑니다 (점추정 아님). 노출 수와
   응답률도 함께 내려보냅니다 — 100건을 먼저 넘는 문장은 가장 많이
   겹치는 문장이라 선택 편향이 있습니다. `repo.agreement()`.
11. **얼굴 사진(면상선생) 미구현** — 생체인식정보라 저장이 금지돼
    있습니다. 저장 없이 처리하는 설계를 먼저 정해야 합니다.
    `lens.BLOCKED_INPUTS` 가 이유를 들고 있고 테스트가 셉니다.
12. **시각 미상 비율이 아직 가정값(15%)** — `charts` 가 200건을 넘으면
    `tools/population.py` 가 실측으로 바꿔 씁니다. 어느 쪽을 썼는지
    도구가 찍고, `seed/relay_rules.json` 의 `reach_measured_with` 에
    남습니다.
8. **균시차 미반영** — 자시 경계 출생자 영향. 2차에서 검토.
9. **절입 비교 기준이 유파 선택** — 진태양시 보정 후 시각과 비교
   (`JIEQI_BASIS="corrected"`). 서울 기준 절입 직후 32분 구간에서
   표준시 비교 앱과 결과가 갈립니다. README 참고.
10. **에셋 0/24** — 자리표시 SVG. `public/scene/{id}/` 에 넣으면 자동 교체.

---

## 검사 명령

```powershell
.\dev.ps1 engine-check     # 테스트 + 교차검증 + 분포 + 중복률  ← 관문
.\dev.ps1 crosscheck       # sxtwl 없는 독립 계산과 대조
.\dev.ps1 dup              # 중복률 — ★ 가짓수보다 '최다 점유' 를 보세요
.\dev.ps1 ladder           # 값 사다리 — ★ 상관 말고 '옆 등급과 몇 컷 차' 를 보세요
.\dev.ps1 reach --write    # 릴레이 도달률 재기 — 규칙을 고쳤으면 다시
.\dev.ps1 screens          # 고아·막다른 화면·죽은 버튼
.\dev.ps1 plan             # 회귀 50건 — 무엇부터 (유파 20건이 남음)
.\dev.ps1 fill <파일>       # 받아적은 기대값 대조
.\dev.ps1 funnel           # 퍼널 — 어디서 나가는가
.\dev.ps1 migrate-sqlite   # 마이그레이션 왕복
```

측정 도구 (dev.ps1 을 안 거치고 직접)
```
tools/relay_spread.py      릴레이 쏠림 — 최다 1순위 · 도달 캐릭터 수
tools/probe_conditions.py  규칙 문턱을 정하기 **전에** 인구 비율 재보기
tools/axis_spread.py       성향 4글자 겹침 분포 · 깊은 해석 비율
tools/second_buy.py        두 번째 결제가 진짜 다른 상품인가
tools/population.py        도구들이 같은 인구를 보게 하는 자리
```

## 하지 말 것

- 브레이크·가드레일 제거
- 문장 뱅크를 클라이언트로 이동
- 적중률·과학적 입증 문구 추가
- 시각 미상인데 시주를 채우기
- 얼굴 사진을 DB에 저장 (생체인식정보)
- 실데이터 없이 공감률 숫자 표시
- 계측에 생년월일·이름·chart_id 싣기 (준식별자입니다)
- 퍼널 API 를 열쇠 없이 열어 두기
- 공유 payload 에 생년월일시·고을 넣기
- 신살로 질병·사고·재물을 단정하기 (docs/14 §7)
- 유입 화면에서 적중률·과학·통계 같은 말 쓰기
- 릴레이 규칙에 `always` 쓰기 — 누구에게나 걸리는 규칙은 추천이 아니라
  배경이라, 재순위에서 늘 꼴찌가 되어 그 캐릭터가 영영 안 팔립니다
- 근거 문구에 연산자·문턱값 쓰기 (`목 0.0 ≤ 1.0`) — 근거는 보이되
  규칙은 감춥니다
- 릴레이 응답에 `rule_id`·`priority`·`score` 싣기 (분기표입니다)
- 상대 사주·현재 상황을 DB에 저장하기 — 상대 사주는 **제3자의
  생년월일**이라 본인 동의가 없습니다. 계산하고 버립니다
- 맥락축에 자유 입력 받기 — 개인정보가 섞이고 가드를 우회합니다
- 공감률을 점추정으로 띄우기 — 하한으로 냅니다. 하한이 낮은 문장을
  **감추지도** 마세요. 감추면 남는 숫자가 전부 높아 보입니다
- 문장 가짓수만 보고 넉넉하다 판단하기 — 쏠림을 보세요
- **표시가와 청구가를 다르게 두기** — 릴레이 카드에 보인 값이 그대로
  청구됩니다 (`payments.price_of(tier, lens_id)`). 캐릭터 값이 곧
  「이 자리 하나」 값입니다. 카드는 4,900원인데 결제가 19,900원이던
  자리가 있었습니다
- **화면이 제 손으로 분량 적기** — 컷 수는 서버가 셉니다
  (`POST /v1/pay/tiers`). "평생운 18컷 · 25페이지"라 적혀 있었고
  실제로는 11컷이었습니다
- **비싼 캐릭터가 덜 주게 두기** — 값 ↔ 컷수 상관이 −0.419 였습니다.
  `tests/test_lens_cuts.py` 가 값 사다리를 지킵니다
- **값 등급이 여럿인데 같은 것을 주기** — 12,900·9,900·6,900·4,900이
  전부 10컷이던 자리가 있었습니다. 등급이 넷인데 상품이 하나면 그건
  값이 아니라 이름표입니다. `.\dev.ps1 ladder` 가 **옆 등급과 몇 컷
  차이인지**를 찍습니다. 0이면 두 등급이 같은 상품입니다
- **값이 요구하는 몫을 추가 입력에 지우기** — 손님이 안 적으면 안
  열립니다. 사다리는 **관점 컷이 혼자** 집니다 (`lens_cuts.OWN_FLOOR`)
- **서로에게서 나온 축을 곱하기** — `ilji_state` 는 `day_ji` 로 만든
  값이고 `flow` 는 십신을 묶은 값입니다. 이런 짝을 곱하면 가짓수가
  **종이 위에만** 있습니다. 뜻이 맞는 축 · 고른 축 · **서로 무관한 축**
  은 셋 다 다릅니다
- **추가 입력이 틀렸다고 리포트 전체를 막기** — 그 컷만 접고
  `extra_error` 로 말합니다. 값을 치른 사람입니다
- **관점 컷을 뜻 맞는 축 둘로만 만들기** — 축이 고르지 않으면 가짓수가
  있어도 쏠립니다(본문 17%). 세 번째로 **고른 축**을 곱하세요
- **근거 줄로 쏠림을 가리기** — dup_rate 가 본문만 따로 잽니다
- 서버가 파이썬 원문으로 대답하기 — 화면과 **같은 말투**로 거절합니다
