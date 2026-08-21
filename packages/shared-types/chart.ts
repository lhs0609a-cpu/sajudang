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
  correction: Correction;
}

export interface ChartResponse {
  chart_id: string;
  features: Features;
  cached: boolean;
}

/* ── 훅 ─────────────────────────────────────────────────── */
export interface HookSegment {
  stage: string;              // "0" | "1" | "2" | "2.5" | "3"
  label: string;
  source: string | null;
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

/** 잠긴 컷은 본문(html)이 오지 않는다. 제목과 근거만 온다. */
export interface LockedCut {
  id: string;
  title: string;
  source: string;
  need_tier: "one" | "all";
}

export interface LensPublic {
  id: string;
  name: string;
  hanja: string | null;
  group: string | null;
  archetype: string | null;
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
}

/* ── 릴레이 ─────────────────────────────────────────────── */
export interface RelayPick {
  rule_id: string;
  lens_id: string;
  name: string;
  priority: number;
  price: number | null;
  released: boolean;
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
  text: string;
  notes: string[];
  source: string;
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
