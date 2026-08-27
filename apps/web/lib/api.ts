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
  }) => post<ReportResponse>("/v1/report", req),

  relay: (req: {
    chart_id: string; session_id: string;
    read?: string[]; skipped?: string[]; last_lens?: string | null;
  }) => post<RelayResponse>("/v1/relay", req),

  /** 실제로 다음 캐릭터로 넘어갈 때. 세션 브레이크 카운터를 올린다. */
  consumeRelay: (sessionId: string) =>
    post<{ used: number; limit: number; blocked: boolean }>(
      `/v1/relay/consume?session_id=${encodeURIComponent(sessionId)}`, {}),

  feedback: (req: {
    statement_id: string; chart_id: string; answer: 0 | 1;
    stage?: string; lens_id?: string | null; concern?: string; axis4?: string | null;
  }) => post<{ ok: boolean; recorded: number }>("/v1/feedback", req),

  /** 공감률. 응답 100건 미만이면 shown=false — 숫자를 지어내지 말 것. */
  agreement: (statementId: string) =>
    call<{ shown: boolean; rate?: number; total?: number; min_responses?: number }>(
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
    post<{
      tiers: {
        id: string; name: string; price: number; per_month: boolean;
        note: string; cuts: number; locked: number; opens: string[];
      }[];
      lens_id: string;
      refund_notice: string;
    }>("/v1/pay/tiers", req),

  payPrepare: (req: {
    session_id: string; chart_id: string; lens_id: string;
    tier: string; concern?: string;
  }) => post<{
    order_id: string; amount: number; tier: string;
    client_key: string | null; enabled: boolean; refund_notice: string;
    purchases_today: number; per_day_limit: number;
  }>("/v1/pay/prepare", req),

  payConfirm: (req: { session_id: string; order_id: string; payment_key: string }) =>
    post<{ ok: boolean; tier: string; unlocked: string[]; seal: string }>(
      "/v1/pay/confirm", req),

  daily: (chartId: string) =>
    call<DailyResponse>(`/v1/daily?chart_id=${encodeURIComponent(chartId)}`),
};

export type { Features };
