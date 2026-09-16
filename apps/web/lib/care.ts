/**
 * 쉬어 가는 자리 — 화면 쪽 표.
 *
 * ★ 표는 **한 벌**입니다 (services/api/engine/care.py).
 *
 *   번호와 문턱을 두 벌 들면 한쪽만 고쳐져 틀린 번호가 나갑니다.
 *   그래서 이 파일은 저쪽을 **베낀 것**이고, `tests/test_safety.py`
 *   가 둘이 같은지 셉니다. 고칠 때는 둘 다 고치시오.
 *
 * ★ 왜 화면에서 세나
 *
 *   신호 넷 가운데 셋(되풀이 · 늦은 때 · 안 맞음)은 **이 기기에만**
 *   있는 값입니다. 서버로 보내면 그건 계측에 준식별자를 싣는 것이오
 *   (CLAUDE.md — 계측에 생년월일·chart_id 싣기 금지). 세는 것은
 *   여기서 하고, 서버는 모릅니다.
 */

/** 도움 받을 곳. 이 집이 상담하지 않소 — 적어 두기만 하오. */
export const CARE_LINES = [
  { name: "자살예방 상담전화", tel: "109", when: "24시간" },
  { name: "정신건강위기 상담전화", tel: "1577-0199", when: "24시간" },
  { name: "청소년 전화", tel: "1388", when: "24시간" },
] as const;

/** 몇이 겹쳐야 여는가. 하나로는 안 엽니다. */
export const OPEN_AT = 2;
/** 하루에 몇 번부터 「되풀이」 로 보는가. */
export const VISITS_AT = 3;
/** 훅 다섯 마디에 「아니오」가 몇이면 안 맞는 것으로 보는가. */
export const MISS_AT = 4;

export type CareSignal = "되풀이" | "안 맞음" | "늦은 때" | "몸";

/**
 * 겹친 신호. **세는 값**만 봅니다 — 지어내지 않습니다.
 *
 * ★ 이건 진단이 아닙니다. 누가 힘든지 우리는 모릅니다. 아는 것은
 *   「이 사람이 오늘 이 집을 오래 붙들고 있다」 뿐이오.
 */
export function careSignals(o: {
  visits?: number;
  hookMisses?: number;
  hour?: number | null;
  concern?: string | null;
  returning?: boolean;
}): CareSignal[] {
  const out: CareSignal[] = [];
  if ((o.visits ?? 0) >= VISITS_AT) out.push("되풀이");
  if ((o.hookMisses ?? 0) >= MISS_AT) out.push("안 맞음");
  if (o.hour != null && o.hour >= 0 && o.hour <= 5 && o.returning) out.push("늦은 때");
  if (o.concern === "health" && o.returning) out.push("몸");
  return out;
}

export function shouldRest(o: Parameters<typeof careSignals>[0]): boolean {
  return careSignals(o).length >= OPEN_AT;
}
