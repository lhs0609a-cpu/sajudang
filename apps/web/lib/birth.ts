/**
 * 생년월일 검증 — 틀린 자리에서 바로 말해 준다.
 *
 * ★ 왜 화면에서도 막는가
 *   예전에는 a3 을 그냥 통과시키고 a6 에서 서버가 거절했습니다. 오타 하나
 *   낸 사람이 a4·a4b·a5 를 다 지나서야 오류를 보고, 되돌아갈 버튼도
 *   없었습니다. 세 화면을 헛걸음한 뒤에 막다른 길이었습니다.
 *
 * ★ 서버 검증을 없애는 게 아닙니다
 *   화면은 사람에게 빨리 알려주는 쪽이고, 진짜 방어선은 서버입니다.
 *   여기 규칙이 서버(schemas/api.py · engine/calendar.py)와 같아야
 *   "화면은 통과했는데 서버가 거절" 하는 자리가 안 생깁니다.
 *
 * ★ 말투
 *   이 집의 말로 적습니다. 영어 원문이 뜨면 그 순간 몰입이 깨집니다.
 */

/** 엔진이 다루는 범위. services/api/engine/solar_terms.py 와 같아야 합니다. */
export const YEAR_MIN = 1900;
export const YEAR_MAX = 2100;

const DAYS = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];

function leap(y: number): boolean {
  return (y % 4 === 0 && y % 100 !== 0) || y % 400 === 0;
}

export function daysInMonth(y: number, m: number): number {
  if (m < 1 || m > 12) return 31;
  return m === 2 && leap(y) ? 29 : DAYS[m - 1];
}

/**
 * 문제가 있으면 그 문장을, 없으면 null.
 * 아직 덜 적은 칸은 조용히 넘어갑니다 — 적는 도중에 빨간 글씨가 뜨면
 * 쫓기는 기분이 듭니다.
 */
export function birthProblem(
  year: number | null, month: number | null, day: number | null,
): string | null {
  if (year === null || month === null || day === null) {
    return "아직 다 적지 않았소.";
  }
  if (year < YEAR_MIN || year > YEAR_MAX) {
    return `${YEAR_MIN}년부터 ${YEAR_MAX}년까지만 보오. 절기를 셀 수 있는 데까지요.`;
  }
  if (month < 1 || month > 12) {
    return "달은 1에서 12 사이요.";
  }
  const last = daysInMonth(year, month);
  if (day < 1 || day > last) {
    return `${year}년 ${month}월은 ${last}일까지요.`;
  }

  // 아직 오지 않은 날. 서버는 받지만 사람에게는 물어보는 게 맞습니다.
  const now = new Date();
  const born = new Date(year, month - 1, day);
  if (born.getTime() > now.getTime()) {
    return "아직 오지 않은 날이오. 다시 보시오.";
  }
  return null;
}

/** 서버가 거절한 것을 이 집의 말로 옮긴다. */
export function birthMessageFrom(detail: unknown): string | null {
  const text = typeof detail === "string" ? detail : JSON.stringify(detail ?? "");
  if (/year/.test(text) && /greater|less/.test(text)) {
    return `${YEAR_MIN}년부터 ${YEAR_MAX}년까지만 보오.`;
  }
  if (/month/.test(text)) return "달은 1에서 12 사이요.";
  if (/day is out of range|day/.test(text)) return "그 달에 없는 날이오.";
  if (/hour/.test(text)) return "때가 잘못 적혔소.";
  return null;
}
