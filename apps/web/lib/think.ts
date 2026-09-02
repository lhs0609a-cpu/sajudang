/**
 * 뜸 한 줄 — 이 컷이 **무엇을 보는 자리인지** 근거 줄에서 뽑는다.
 *
 * ★ 지어내지 않습니다.
 *
 *   근거 줄은 이렇게 생겼습니다:
 *
 *       일지 亥 · 癸일간 — 일지는 나 바로 아래 자리라, 가까운 데서
 *       벌어지는 일을 보오 〔자평 명리 · 십신〕
 *
 *   「—」 앞이 **읽은 것**이고 뒤가 이치입니다. 그 앞머리에서 첫
 *   낱말만 떼어 "일지를 봅니다…" 로 세웁니다. 손님이 그 컷을 읽으면
 *   근거 줄에 같은 말이 그대로 적혀 있습니다 — 대 볼 수 있습니다.
 *
 *   "심도 있게 분석 중" 같은 말은 안 씁니다. 아무것도 안 가리키는
 *   말이고, 이 집은 근거 대는 집입니다.
 */

/** "여덟 글자" 처럼 첫 낱말만 떼면 뜻이 없어지는 것 */
const KEEP2 = new Set(["여덟", "이번", "지금", "다음"]);

const HANGUL_A = 0xac00;
const HANGUL_Z = 0xd7a3;

/** 받침이 있으면 을 · 없으면 를. 한글이 아니면 '을' 로 둡니다. */
function eul(word: string): string {
  const ch = word.charCodeAt(word.length - 1);
  if (ch < HANGUL_A || ch > HANGUL_Z) return "을";
  return (ch - HANGUL_A) % 28 === 0 ? "를" : "을";
}

export function thinkOf(source?: string | null): string | undefined {
  if (!source) return undefined;
  const head = source.split("—")[0].split("〔")[0].trim();
  if (!head) return undefined;

  const first = head.split("·")[0].trim();
  const parts = first.split(/\s+/).filter(Boolean);
  if (parts.length === 0) return undefined;

  let term = parts[0];
  if (KEEP2.has(term) && parts[1]) term = `${parts[0]} ${parts[1]}`;
  // 「신살 6」·「표본 40,000명」처럼 숫자가 붙어 오면 떼어 냅니다.
  term = term.replace(/[0-9,]+.*$/, "").trim();
  if (!term) return undefined;

  return `${term}${eul(term)} 봅니다…`;
}
