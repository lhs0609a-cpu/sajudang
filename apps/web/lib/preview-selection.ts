import type { LockedCut } from '@shared/chart';

const TOPIC_ENDINGS: Record<string, string[]> = {
  money: ['hold', 'flow', 'bowl', 'gwanjae', 'book'],
  work: ['seat', 'gyeok', 'bone', 'lesson', 'wind'],
  love: ['seat', 'tie', 'thread', 'lack', 'trace', 'spin'],
  people: ['tie', 'beside', 'palace', 'room', 'far'],
  dir: ['road', 'pick', 'next', 'turn', 'gate'],
  health: ['pace', 'fill', 'lean', 'johu', 'seupjo'],
};

/** Select only chapters present in the server's locked list. Do not mutate it. */
export function selectPreviewCuts(cuts: LockedCut[], concern: string): LockedCut[] {
  const available = cuts.filter(c => !!c.teaser);
  const own = available.filter(c => c.id.startsWith('lc_'));
  const endings = TOPIC_ENDINGS[concern] ?? [];
  const rank = (id: string) => {
    const index = endings.findIndex(t => id.endsWith('_' + t));
    return index < 0 ? endings.length : index;
  };
  own.sort((a, b) => rank(a.id) - rank(b.id));
  const pattern = available.find(c => c.id === 'concern_pattern')
    ?? available.find(c => c.id === 'spine_scene');
  const time = available.find(c => c.id === 'concern_turn')
    ?? available.find(c => c.id === 'daeun_map');
  // A specialist's unrelated technical chapter should not lead a money/love question.
  const relevant = own.find(c => rank(c.id) < endings.length);
  const candidates = [relevant ?? pattern ?? own[0], pattern, time, ...own, ...available];
  const unique = new Map<string, LockedCut>();
  for (const cut of candidates) if (cut && !unique.has(cut.id)) unique.set(cut.id, cut);
  return [...unique.values()].slice(0, 3);
}
