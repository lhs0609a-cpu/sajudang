/*
 * 조사 — 받침을 보고 고른다.
 *
 * ★ 손님이 짚은 것 (2026-09-07)
 *
 *     「풍운도령가 종이를 덮었다.」
 *
 *   「령」에 받침이 있으니 「풍운도령**이**」라야 합니다. 화면이
 *   `${lens.name}가` 라고 손으로 박아 두어, 스무 사람 중 받침 없는
 *   이름(몽화·화경·연담·훈장…)만 맞고 나머지는 전부 틀렸습니다.
 *
 * ★ 서버에는 있었고 화면에는 없었습니다
 *
 *   `bank.josa` · `lens_cuts._fmt` · `topic._fmt` 가 서버에서는
 *   받침을 봅니다. 화면에는 그 자리가 없어서 같은 집에 두 규칙이
 *   돌고 있었습니다. `tools/josa_audit.py` 가 이제 셉니다.
 */

/** 마지막 한글 글자에 받침이 있는가. 한글이 없으면 null. */
export function batchim(word: string): boolean | null {
  for (let i = word.length - 1; i >= 0; i -= 1) {
    const c = word.charCodeAt(i);
    if (c >= 0xac00 && c <= 0xd7a3) return (c - 0xac00) % 28 !== 0;
    // 한자·숫자·라틴은 소리를 모르니 건너뜁니다 — 지어내지 않습니다.
  }
  return null;
}

/**
 * `josa("풍운도령", "이", "가")` → `"풍운도령이"`
 *
 * 받침을 못 읽으면 **받침 없는 쪽**으로 둡니다. 한자 뒤 조사는
 * 읽는 소리를 알아야 해서 여기서 정하지 않습니다 (서버 `josa_hanja`).
 */
export function josa(word: string, withBatchim: string, without: string): string {
  const b = batchim(word);
  return word + (b ? withBatchim : without);
}

/** 자주 쓰는 짝 — 손으로 「이/가」를 적지 마시오. */
export const iga = (w: string) => josa(w, "이", "가");
export const eunneun = (w: string) => josa(w, "은", "는");
export const eulreul = (w: string) => josa(w, "을", "를");
export const gwawa = (w: string) => josa(w, "과", "와");
export const euro = (w: string) => josa(w, "으로", "로");
/** 서술격 — 「…이오 / …요」 */
export const io = (w: string) => josa(w, "이오", "요");
