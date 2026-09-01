# CLAUDE.md

성신당(星辰堂) — 웹/모바일 사주 서비스. 이 파일은 Claude Code가 매 세션 처음 읽는 컨텍스트입니다.

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
엔진    sxtwl (24절기) + 자체 명리 로직
DB     PostgreSQL 15 · Redis
결제    토스페이먼츠
```

모바일 앱은 만들지 않습니다. 반응형 웹 → 필요 시 WebView.

---

## 디렉토리

```
/services/api/engine/
  calendar.py    ★ 만세력. 05번 문서대로.
  features.py    Feature Store 산출
  bank.py        문장 뱅크 조합
  lens.py        캐릭터 렌즈
  relay.py       릴레이 규칙 평가
  guard.py       ★ 금지어 필터
/services/api/routers/
  chart.py  hook.py  report.py  relay.py  feedback.py  daily.py
/apps/web/app/
  (entry)/  lobby/  report/  pay/  relay/  daily/  me/
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
```bash
pytest tests/test_calendar.py   # 고정 케이스 50건 전량
python tools/distribution.py    # 3,000명 분포 — 0%인 값이 있으면 도달 불가 분기
```

### 문장을 추가한 뒤
```bash
python tools/dup_rate.py        # 임의 2인 중복률. 목표 15% 이하
```

### 새 기능을 붙이기 전
`docs/11_법무_컴플라이언스.md` 의 금지 목록을 먼저 확인한다.

---

## 현재 상태

| 항목 | 상태 |
|---|---|
| 계산 로직 | 설계 완료, 구현 필요 (sxtwl 미연결) |
| 문장 뱅크 | 완료 (`seed/bank.json`) |
| 렌즈 20인 | 완료 (`seed/lenses.json`) |
| 릴레이 규칙 | 10개 (30개까지 확장 예정) |
| 화면 | 참조 구현체에 27개 |
| DB | 스키마 설계 완료, 미구축 |
| 결제 | 미연동 |
| 에셋 | 0/24 장면, 0/20 캐릭터 |

---

## 알려진 이슈

1. **절기가 근사 테이블** — ±1일 오차. sxtwl 로 교체 필수. (최우선)
2. **대운수가 근사식** — `(day%3)+3`. 절입일 기준 정식 계산으로 교체.
3. **회고 루프가 고정 문장** — `statement_log` 붙으면 해결.
4. **공감률이 예시 데이터** — 실데이터 100건 전까지 노출 금지.
5. **균시차 미반영** — 자시 경계 출생자 영향. 2차에서 검토.

---

## 하지 말 것

- 브레이크·가드레일 제거
- 문장 뱅크를 클라이언트로 이동
- 적중률·과학적 입증 문구 추가
- 시각 미상인데 시주를 채우기
- 얼굴 사진을 DB에 저장 (생체인식정보)
- 실데이터 없이 공감률 숫자 표시
