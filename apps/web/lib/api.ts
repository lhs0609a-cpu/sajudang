/**
 * API 클라이언트.
 *
 * ★ 계산과 문장은 전부 서버에 있습니다. 여기서 사주를 계산하거나
 *   문장을 만들지 마세요. (docs/02 §7 · CLAUDE.md 절대 규칙 5)
 */
import type {
  ChartRequest, ChartResponse, DailyResponse, Features,
  HookResponse, RelayResponse, ReportResponse, Shared, Summary,
} from "@shared/chart";

const BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";

export const API_BASE = BASE;

/**
 * 배포된 사이트인데 API 주소가 localhost 로 남아 있으면 아무것도 못 합니다.
 * 조용히 실패하지 말고 그 사실을 화면에 알립니다.
 */
export function apiMisconfigured(): boolean {
  if (typeof window === "undefined") return false;
  const localApi = /^https?:\/\/(localhost|127\.0\.0\.1)/.test(BASE);
  const localSite = /^(localhost|127\.0\.0\.1)$/.test(window.location.hostname);
  return localApi && !localSite;
}

/**
 * 목패 한 장. ★ 값도 분량도 **서버가 세어서** 줍니다.
 *
 * 화면이 제 손으로 적으면 엔진이 달라져도 그 줄은 안 바뀌어 다시
 * 어긋납니다 — "평생운 18컷 · 25페이지" 라 적혀 있었고 실제로는
 * 11컷이었습니다.
 */
export interface TierCard {
  id: string;
  name: string;
  price: number;
  /**
   * 달마다 자동으로 빠져나가는가.
   *
   * ★ 지금은 **항상 거짓**입니다. 빌링키도 자동결제도 없습니다.
   *   「한 달 듣기」는 한 번 치르고 `days` 일입니다 — 저절로 다시
   *   빠져나가지 않습니다. 자동결제를 붙이는 날 이 자리를 다시 보세요.
   */
  per_month: boolean;
  /** 며칠짜리인가. 영구면 null. */
  days: number | null;
  /** 한 번 치르면 계속인가. all·one 이 참입니다. */
  forever: boolean;
  note: string;
  /** 이 명식으로 실제 열리는 자리 수. one 은 한 사람, all·sub 은 스무 사람 합계. */
  cuts: number;
  /** 그 분량이 몇 글자인가. '컷' 은 손님의 말이 아닙니다. */
  chars: number;
  /** 읽는 데 걸리는 어림 시간(분). 서버가 글자 수로 셉니다. */
  minutes: number;
  /** 몇 사람이 열리는가. one 은 1, all·sub 은 스무 사람. */
  lenses: number;
  locked: number;
  opens: string[];
}

/** 값을 치른 직후 **실제로** 열린 것. 명식 캐시가 없으면 counted=false. */
export interface Granted {
  counted: boolean;
  cuts?: number;
  chars?: number;
  minutes?: number;
  lenses?: number;
  tier_name?: string;
}

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
  }
}

async function call<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(BASE + path, {
    ...init,
    headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
  });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail);
    } catch {
      /* 본문이 JSON 이 아니면 statusText 로 둔다 */
    }
    throw new ApiError(res.status, detail);
  }
  return res.json() as Promise<T>;
}

const post = <T>(path: string, body: unknown) =>
  call<T>(path, { method: "POST", body: JSON.stringify(body) });

export const api = {
  chart: (req: ChartRequest) => post<ChartResponse>("/v1/chart", req),

  /** 새로고침 뒤 chart_id 만 남았을 때 명식을 되찾는다. */
  getChart: (chartId: string) =>
    call<ChartResponse>(`/v1/chart/${encodeURIComponent(chartId)}`),

  hook: (req: {
    chart_id: string; concern: string; axis4?: string | null;
    name?: string; lens_id?: string | null;
    /** 「아니오」가 몇 번 나왔는가. 둘이면 도령이 짚는 자리를 바꿉니다. */
    misses?: number;
  }) => post<HookResponse>("/v1/hook", req),

  /**
   * ★ session_id 를 반드시 실어 보냅니다.
   *   tier 는 "보고 싶다" 는 말일 뿐이고, 실제로 열리는 것은 서버가
   *   치른 주문을 보고 정합니다. 안 보내면 무료 구간만 옵니다.
   *   응답의 tier 가 **실제로 내려온 티어**이니 그걸 믿으세요.
   */
  report: (req: {
    chart_id: string; lens_id: string; tier: string;
    session_id: string; concern: string; axis4?: string | null;
    /**
     * 손님이 적은 이름.
     *
     * ★ 셈에는 안 씁니다 — **부르는 데만** 씁니다. 어떤 캐릭터는
     *   이름으로 부릅니다(월하선녀·시계장이·패선생·약초의원).
     *   안 적었으면 그 캐릭터의 대신 부르는 말로 물러섭니다.
     */
    name?: string;
    /**
     * 이 캐릭터가 따로 받는 것. **저장되지 않습니다** —
     * 특히 상대 사주는 제3자의 생년월일이라 본인 동의가 없습니다.
     * 서버가 계산하고 버립니다. (engine/extras.py · docs/11)
     */
    extras?: Record<string, unknown> | null;
  }) => post<ReportResponse>("/v1/report", req),

  /**
   * 추가 입력에서 고를 수 있는 것들.
   *
   * ★ 이 엔드포인트가 있는데 화면이 안 쓰고 있었습니다. 그래서
   *   캐릭터가 입력을 요구하는 51.3%에게 그 컷이 조용히 사라졌습니다.
   */
  reportChoices: () => call<Record<string, unknown>>("/v1/report/choices"),

  relay: (req: {
    chart_id: string; session_id: string;
    read?: string[]; skipped?: string[]; last_lens?: string | null;
  }) => post<RelayResponse>("/v1/relay", req),

  /** 실제로 다음 캐릭터로 넘어갈 때. 세션 브레이크 카운터를 올린다. */
  consumeRelay: (sessionId: string) =>
    post<{ used: number; limit: number; blocked: boolean }>(
      `/v1/relay/consume?session_id=${encodeURIComponent(sessionId)}`, {}),

  feedback: (req: {
    statement_id: string; chart_id: string;
    /** 1 그렇소 · 0 아니오 · **null 글쎄올시다**(노출로만 셉니다) */
    answer?: 0 | 1 | null;
    stage?: string; lens_id?: string | null; concern?: string; axis4?: string | null;
  }) => post<{ ok: boolean; recorded: number }>("/v1/feedback", req),

  /**
   * 공감률. 응답 100건 미만이면 shown=false — 숫자를 지어내지 말 것.
   *
   * ★ 그때도 `seen`(이 문장이 몇 번 나갔는가)은 옵니다. 공감률이 비어
   *   있는 동안 그 자리를 비워 두면 사회적 증거가 0인 채로 결제
   *   갈림길까지 갑니다. 노출 수는 정확도 주장이 아니라 사실입니다.
   */
  agreement: (statementId: string) =>
    call<{ shown: boolean; rate?: number; total?: number; seen?: number;
           min_responses?: number }>(
      `/v1/agreement?statement_id=${encodeURIComponent(statementId)}`),

  /* ── 분석지 · 공유 ── */
  summary: (req: {
    chart_id: string; concern: string; axis4?: string | null;
    lens_id?: string; name?: string;
  }) => post<Summary>("/v1/summary", req),

  /** 공유 링크 발급. 생년월일시는 담기지 않는다. */
  share: (req: {
    chart_id: string; concern: string; axis4?: string | null;
    lens_id?: string; name?: string; from_name?: string;
    reveal?: "full" | "light";
  }) => post<{
    token: string; path: string; expires_days: number;
    includes: string[]; excludes: string[];
  }>("/v1/share", req),

  openShare: (token: string) =>
    call<Shared>(`/v1/share/${encodeURIComponent(token)}`),

  countShareOpen: (token: string) =>
    post<{ views: number }>(`/v1/share/${encodeURIComponent(token)}/open`, {}),

  /* ── 결제 ── */
  payConfig: () =>
    call<{ enabled: boolean; client_key: string | null; refund_notice: string }>(
      "/v1/pay/config"),

  /** 금액은 서버가 정합니다. 여기서 금액을 보내지 마세요. */
  /**
   * 목패 셋. ★ 값과 분량을 **서버가 세어서** 줍니다.
   *   화면이 제 손으로 적으면 엔진이 달라져도 그 줄은 안 바뀌어
   *   다시 어긋납니다. (전에 "18컷 · 25페이지" 라 적혀 있었고
   *   실제로는 11~12컷 · 6탭이었습니다)
   */
  payTiers: (req: {
    chart_id: string; lens_id: string;
    concern?: string; axis4?: string | null;
  }) =>
    post<{ tiers: TierCard[]; lens_id: string;
            refund_notice: string; refund_say: string }>("/v1/pay/tiers", req),

  payPrepare: (req: {
    session_id: string; chart_id: string; lens_id: string;
    tier: string; concern?: string;
  }) => post<{
    order_id: string; amount: number; tier: string;
    client_key: string | null; enabled: boolean; refund_notice: string;
    /** 같은 약속을 이 집의 말로. 결제 버튼 **바로 위**에 놓습니다. */
    refund_say: string;
    purchases_today: number; per_day_limit: number;
  }>("/v1/pay/prepare", req),

  payConfirm: (req: { session_id: string; order_id: string; payment_key: string }) =>
    post<{
      ok: boolean; tier: string; unlocked: string[]; seal: string;
      refund_notice: string;
      /** 방금 무엇을 얻었는가. ★ 서버가 셉니다 — 화면이 적지 않습니다. */
      granted: Granted;
    }>("/v1/pay/confirm", req),

  /**
   * 별점·후기.
   *
   * ★ '결제 확인됨' 을 여기서 주장하지 마세요. 그건 **치른 주문**이
   *   정합니다 (서버가 session_id 로 봅니다). 화면이 paid 를 실어
   *   보내면 그건 광고 문구를 손님이 스스로 다는 것과 같습니다.
   */
  review: (req: {
    lens_id: string; rating?: number | null; body?: string;
    session_id?: string; chart_id?: string;
  }) => post<{ ok: boolean; verified: boolean; visible: boolean; say: string }>(
    "/v1/review", req),

  /**
   * 주문번호로 치른 것을 되찾습니다.
   *
   * ★ 로그인이 없습니다. 자격이 localStorage 난수(session_id)에 매여
   *   있어서, 브라우저를 지우거나 기기를 바꾸면 치른 값을 통째로
   *   잃었습니다. 서버가 토스에 되물어 실제로 치러진 주문인지 봅니다.
   */
  payRestore: (req: { session_id: string; order_id: string }) =>
    post<{ ok: boolean; tier: string; lens_id: string | null;
           expires_at: string | null; say: string }>("/v1/pay/restore", req),

  daily: (chartId: string) =>
    call<DailyResponse>(`/v1/daily?chart_id=${encodeURIComponent(chartId)}`),
};

export type { Features };
