import profiles from './character-profiles.json';
type Concern = 'money' | 'work' | 'love' | 'people' | 'dir' | 'health' | 'real_estate';

export const ALL_CONCERNS: readonly Concern[] =
  ['money', 'work', 'love', 'people', 'dir', 'health', 'real_estate'];

/**
 * 손님에게 내놓을 고민 칸 — **전부** 내놓습니다.
 *
 * ★ 캐릭터가 보는 자리로 칸을 걸러 두었습니다 (2026-09-24 에 고침).
 *   그런데 손님은 먼저 **자기 걱정**을 고르고, 그 사주가 다음 사람을
 *   고르는 것이 이 집의 순서입니다. 칸을 미리 지우면 돈이 걱정인 사람은
 *   돈 칸을 못 보고 시작합니다.
 */
export function characterConcerns(_lensId: string): readonly string[] {
  return ALL_CONCERNS;
}

/**
 * 손님이 고른 고민 — **그대로** 돌려줍니다.
 *
 * ★ 여기서 조용히 갈아치우고 있었습니다 (2026-09-24).
 *
 *   `profile.concerns` 에 없는 고민이면 그 캐릭터의 기본 고민으로
 *   바꿔서 저장했습니다. 그것도 **곳간(store)에서** 바꿨으니, 손님이
 *   「돈」 을 누르면 기억에 남는 것은 「사랑」 이었습니다. 서버도 같은
 *   일을 하고 있어서(engine/lens.concern_for) 리포트 본문이 다른 고민
 *   이름을 댔습니다 — 「자네가 물으러 오신 고민은 갈 곳이네」.
 *
 *   캐릭터의 전문은 없애지 않습니다. 안 보는 자리를 물으면 그 사람이
 *   **아니라고 말합니다** (서버의 `topic.LENS_OFF`). 릴레이도 맞는
 *   사람을 앞에 세웁니다.
 *
 *   함수는 남겨 둡니다 — 부르는 자리가 넷이라, 여기 한 곳에서 규칙을
 *   지키는 편이 낫습니다.
 */
export function characterConcern(_lensId: string, concern: Concern): Concern {
  return concern;
}

/** 이 사람이 그 자리를 **제 자리라 하는가**. 화면이 표시에만 씁니다. */
export function characterCovers(lensId: string, concern: Concern): boolean {
  const profile = profiles[lensId as keyof typeof profiles];
  const rows = (profile?.concerns ?? []) as readonly string[];
  return rows.includes(concern);
}
