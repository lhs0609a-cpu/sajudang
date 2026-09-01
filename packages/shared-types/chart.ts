/**
 * Pydantic(services/api/schemas) ↔ TS 공용 타입.
 * 스키마를 고치면 양쪽을 함께 고친다. (자동 생성은 T3 에서 검토)
 */
export type Sex = "M" | "F";
export type Strength = "신강" | "중화" | "신약";
export type Flow = "비겁" | "식상" | "재성" | "관성" | "인성";
export type Element = "목" | "화" | "토" | "금" | "수";

export interface ChartRequest {
  year: number;
  month: number;
  day: number;
  hour: number | null;
  minute: number | null;
  hour_known: boolean;
  sex: Sex;
  birth_city: string;
}

export interface Pillar {
  gan: string;
  ji: string;
  label: string;
  gz: string;
}

export interface Daeun {
  index: number;
  gz: string;
  gan: string;
  ji: string;
  start_age: number;
  ten_god: string;
}

export interface Correction {
  std_label: string;
  std_deg: number;
  dst: boolean;
  city: string;
  lon: number;
  lon_min: number;
  before: string;
  after: string;
  day_shift: number;
  zi_policy: string;
  jieqi_basis: string;
  jieqi_name: string;
  jieqi_at_kst: string;
  hour_used: boolean;
  boundary_note: string | null;
}

/** 명식에서 성립한 신살 하나 */
export interface SinsalHit {
  key: string;
  name: string;
  hanja: string;
  kind: "길신" | "살" | "특수";
  at: string[];      // 앉은 기둥
  target: string;    // 어느 지지에서 성립했는가
}

/** 길신이 앉은 자리를 궁위로 읽은 것 — 누가 돕는가 */
export interface Helper {
  sinsal: string;
  hanja: string;
  pillar: string;
  ji: string;
  who: string;
  age: string;
  kind: string;
  ten_god_group: string;
}

/** 년주 = 조상 자리 */
export interface Ancestor {
  pillar: string;
  gan_ten_god: string;
  ji_ten_god: string;
  elements: string[];
  yongsin: string;
  supports_yongsin: boolean;
  stance: "돕는 쪽" | "짐이 되는 쪽" | "크게 관여하지 않는 쪽";
  good_sinsal: string[];
  bad_sinsal: string[];
  inherited: string;
}

/** 네 기둥의 궁위 */
export interface Palace {
  pillar: string;
  gz: string | null;
  who: string;
  also: string;
  age: string;
  ten_god: string | null;
  unknown?: boolean;
}

export interface Features {
  pillars: Pillar[];          // 시각 미상이면 3개
  day_gan: string;
  day_ji: string;
  hour_known: boolean;
  sex: Sex;
  saju_year: number;
  elements: Record<Element, number>;
  strength: Strength;
  strength_score: number;
  deuk_ryeong: boolean;
  deuk_ji: boolean;
  yongsin: Element;
  ten_gods: Record<string, number>;
  top_ten_god: string;
  /** 주도 십신이 동률이었는가. 43%가 동률 — 단정해서 쓰지 말 것. */
  top_ten_god_tied: boolean;
  gwan: number;
  jae: number;
  sik: number;
  bi: number;
  inn: number;
  strong_el: Element;
  weak_el: Element;
  /** 최약 오행이 동률이면 전부. 화면에서는 둘 다 말해야 정직하다. */
  weak_els: Element[];
  gap: number;
  flow: Flow;
  flow_el: Element;
  age: number;
  /** 대운 순행 여부. 화면에서 방향을 적을 때 이 값을 쓸 것. */
  forward: boolean;
  daeun: Daeun[];
  daeun_now: number;
  /** 첫 대운에 들어갔는가. false 면 '지금 그 대운' 이라고 말하면 안 된다. */
  daeun_started: boolean;
  daeun_ten_god: string;
  daeun_start: number;
  ilji_chung: boolean;
  ilji_hap: string[];

  /* ── 신살 · 궁위 (docs/14) ── */
  sinsal: SinsalHit[];
  gongmang: string;
  helpers: Helper[];
  ancestor: Ancestor;
  palaces: Palace[];

  correction: Correction;
}

/**
 * 희소도 — 이 배치가 인구에서 몇 명인가.
 *
 * ★ **센 값**입니다. 표는 4만 명을 세어 만듭니다(tools/make_rarity.py).
 *   지어낸 숫자가 아니라 그래서 낼 수 있습니다.
 *
 * ★ 표가 없거나 낡았으면 서버가 아무것도 안 보냅니다(null). 화면은
 *   그 자리를 조용히 접습니다 — 없는 숫자를 지어내지 않습니다.
 */
export interface Rarity {
  words: string;          // "1만 명에 165명"
  band: string;           // 흔함 · 드묾 …
  per10k: number;
  ilju: string | null;    // 일주만 따로
  ilju_gz: string | null; // 庚戌
  ilju_per10k: number | null;
}

export interface ChartResponse {
  chart_id: string;
  features: Features;
  cached: boolean;
  rarity?: Rarity | null;
}

/* ── 훅 ─────────────────────────────────────────────────── */
export interface HookSegment {
  stage: string;              // "0" | "1" | "2" | "2.5" | "3"
  label: string;
  source: string | null;
  /**
   * 근거를 본문 **아래**에 둘 것인가. 0단(찌르기)만 참이다.
   *
   * ★ 0단에 근거가 아예 없었습니다. 손님이 이 집에서 처음 읽는 문장이
   *   하필 근거 없는 문장이라, "근거 대는 집" 이라는 자리가 가장 센
   *   첫 문장에서 사라졌습니다. 그렇다고 근거를 찌르기 **위**에 놓으면
   *   첫 문장이 강의가 됩니다. 그래서 자리만 아래로 옮깁니다.
   */
  source_below: boolean;
  html: string;               // 서버가 렌더한 HTML. 원문은 서버에만 있다.
  question: string;
  yes: string;
  no: string;
  statement_id: string;       // 응답 기록의 단위
}

export interface HookResponse {
  chart_id: string;
  segments: HookSegment[];
  cached: boolean;
}

/* ── 리포트 ─────────────────────────────────────────────── */
export interface ReportCut {
  id: string;
  title: string;
  source: string;
  html: string;
  statement_id: string | null;
}

/**
 * 잠긴 컷은 본문(html)이 오지 않는다. 제목·근거·**첫 줄**만 온다.
 *
 * ★ 전에는 화면이 `가가가가 가가가가가 가가가` 를 그렸습니다.
 *   자리표시 문자열이 그대로 배포된 것입니다. 궁금증은 구체적일 때만
 *   생깁니다 — 무엇을 놓치는지 모르면 아쉽지도 않습니다.
 *   이제 서버가 첫 문장을 **잘라서** 내려보냅니다 (engine/report._teaser).
 */
export interface LockedCut {
  id: string;
  title: string;
  source: string;
  /** 첫 줄. 본문의 40%를 넘지 않는다. 없을 수도 있다. */
  teaser: string | null;
  /** 이 컷의 실제 분량(글자). '컷' 은 손님의 말이 아니다. */
  chars: number;
  need_tier: "one" | "all";
  /**
   * 그 목패의 **이름**. 서버가 실어 보낸다.
   *
   * ★ 화면이 need_tier 를 보고 이름을 제 손으로 지어냈습니다.
   *   `all` 이 "여덟 글자 전부" 에서 "스무 사람 전부" 로 바뀌었는데
   *   페이월만 옛 이름을 불러서, 같은 상품을 두 화면이 다른 이름으로
   *   부르고 있었습니다. 이름도 한 벌입니다 (payments.TIER_NAME).
   */
  need_tier_name: string;
}

export interface LensPublic {
  id: string;
  name: string;
  hanja: string | null;
  group: string | null;
  archetype: string | null;
  /** 무엇을 잘 보는 사람인가 (진열대·릴레이 카드에 붙습니다) */
  specialty?: string | null;
  call: string | null;
  price: number | null;
  released: boolean;
}

export interface ReportResponse {
  report_id: string;
  chart_id: string;
  lens: LensPublic;
  tier: string;
  concern: string;
  cuts: ReportCut[];
  locked: LockedCut[];
  /** 캐릭터의 여는 말·닫는 말. 렌더된 HTML 입니다. */
  opening: string | null;
  closing: string | null;
  /** 이 캐릭터가 더 받아야 하는 추가 입력. 없으면 null.
   *  partner / context / blood / image / cards */
  needs_input: string | null;
  /** 받은 추가 입력이 틀렸을 때 그 사유. 그 컷만 빠지고 리포트는 나옵니다. */
  extra_error: string | null;
  /**
   * 이 자리에서 값을 권해도 되는가.
   *
   * ★ 청동자는 값이 없는 캐릭터이고, 무거운 리포트 뒤에 강제로 붙는
   *   **안전망**입니다 (relay.FALLBACK_LENS). 그런데 그 자리에 잠긴 컷이
   *   여섯 서 있고 「이 자리 하나」 목패는 값이 없어 안 떠서, 살 수 있는
   *   것이 달삯뿐이었습니다. 방금 무거운 것을 읽고 온 사람에게요.
   *   거짓이면 페이월도, 목패로 가는 버튼도 그리지 않습니다.
   */
  sells: boolean;
}

/* ── 릴레이 ─────────────────────────────────────────────── */
/**
 * ★ rule_id · priority · reach · score 는 **내려오지 않습니다.**
 *   근거(reason)는 그 사람의 명식이라 보여야 하지만, 어떤 규칙이 몇 점으로
 *   이겼는지는 우리 분기표입니다. 새면 규칙을 역산할 수 있습니다.
 *   (services/api/engine/relay.py · PUBLIC_FIELDS)
 */
export interface RelayPick {
  lens_id: string;
  name: string;
  price: number | null;
  released: boolean;
  /** 화면에 그대로 그려도 되는 근거 한 줄. 문턱값은 들어 있지 않습니다. */
  reason: string;
  quote: string | null;
}

export interface RelayBreaks {
  per_session_relay: number;
  per_day_purchase: number;
  reunion_cooldown_days: number;
  visit_warn_at: number;
}

export interface RelayResponse {
  recommend: RelayPick[];
  forced: string[];           // 정서 안전망 — 무료 캐릭터 강제
  blocked: boolean;           // 세션 릴레이 상한 도달
  block_reason: string | null;
  breaks: RelayBreaks;
}

/* ── 일진 ───────────────────────────────────────────────── */
export interface DailyResponse {
  date: string;
  gz: string;
  gan: string;
  ji: string;
  element: string;
  relation: string;
  score: number;
  /**
   * 이 점수가 무엇을 센 것인가.
   *
   * ★ 화면이 "적중률이 아니라 배치 점수요" 라고만 적고 있었습니다.
   *   부정만 하고 정의를 안 주면 손님에게 76은 아무 뜻도 없는 수입니다.
   *   여기는 근거 대는 집이니 방어가 아니라 셈법 공개로 처리합니다.
   */
  score_why: { k: string; v: number; t: string }[];
  score_says: string;
  /** 본문. lines 를 이어 붙인 것. */
  text: string;
  /** 본문을 줄 단위로. 관계 × 일간 × 신강약 × 계절 × 용신 을 곱한 결과라
   *  같은 날 다른 사람이 받는 문장이 서로 다릅니다. */
  lines: string[];
  notes: string[];
  source: string;
  statement_id: string;
  free: boolean;
}

/* ── 분석지 ─────────────────────────────────────────────── */
export interface SummarySection {
  id: string;
  title: string;
  source: string;
  html: string;
}

export interface SinsalBrief {
  /** 의인화 그림을 찾는 열쇠 (lib/sinsalFigures.ts) */
  key: string;
  name: string;
  hanja: string;
  kind: "길신" | "살" | "특수";
  at: string[];
}

export interface Summary {
  name: string | null;
  lens: LensPublic;
  concern: string;
  day_gan: string;
  ilgan_name: string;
  element: Element;
  headline: string;
  /** 공유 카드에 박히는 핵심 3줄 */
  three_lines: string[];
  strength: Strength;
  flow: Flow;
  weak_el: Element;
  yongsin: Element;
  pillars: Pillar[];
  hour_known: boolean;
  sections: SummarySection[];
  sinsal: SinsalBrief[];
  /** 숨기면 "맞히는 집" 이 된다. 반드시 함께 보여줄 것. */
  caveats: string[];
}

/* ── 공유받은 것 ────────────────────────────────────────── */
export interface Shared {
  reveal: "full" | "light";
  from_name: string | null;
  name: string | null;
  created_at: string;
  views: number;
  day_gan: string;
  ilgan_name: string;
  element: Element;
  headline: string;
  three_lines: string[];
  strength: Strength;
  flow: Flow;
  weak_el: Element;
  yongsin: Element;
  lens: LensPublic;
  caveats: string[];
  /** reveal="full" 일 때만 온다 */
  pillars?: Pillar[];
  hour_known?: boolean;
  sinsal?: SinsalBrief[];
  sections?: SummarySection[];
}
