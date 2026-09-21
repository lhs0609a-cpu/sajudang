"use client";
import type { LockedCut } from '@shared/chart';
import { useSession } from '@/lib/store';
import { CHARACTER_QUESTIONS, CHAPTER_QUESTIONS } from '@/lib/curiosity';
import { readingText } from '@/lib/reading-journey';
import LockedVeil from '@/components/LockedVeil';
import { useState, useId } from 'react';
import { selectPreviewCuts } from '@/lib/preview-selection';

/*
 * 접힌 자리 맛보기.
 *
 * ★ 열일곱이 잠겼는데 **둘만** 보이고 있었습니다 (2026-09-21).
 *
 *   궁금증은 구체적일 때만 섭니다. 무엇을 놓치는지 모르면 아쉽지도
 *   않소. 둘만 보여 주고 나머지 열다섯은 이름조차 안 냈으니, 손님
 *   눈에 접힌 자리는 「두 컷」 이었습니다 — 값을 치를 까닭이 그만큼
 *   작아 보였다는 말이오.
 *
 * ★ 물음표를 달아 둔 자리가 **죽어 있었습니다.**
 *
 *   `QUESTIONS` 에 `daeun_now` 와 `yongsin` 이 적혀 있었는데 둘 다
 *   **무료 컷**입니다. 잠긴 목록에 영영 안 들어오니 이 표는 한 번도
 *   안 쓰였고, 정렬도 늘 제자리였습니다. 실제로 잠기는 컷으로
 *   다시 답니다.
 *
 * ★ 분량은 서버가 셉니다 — 화면이 적지 않습니다 (CLAUDE.md).
 *   수를 대야 손님이 무엇이 걸렸는지 그 자리에서 잽니다.
 */
const QUESTIONS: Record<string, string> = {
  axis: '내가 아는 나와 사주가 읽는 나, 어디서 달라지오?',
  hindsight: '여태 지나온 자리는 어떻게 읽는 자리였소?',
  counter: '이 해석이 틀렸다면 어디서 틀렸겠소?',
  daeun_map: '지금의 흐름은 몇 살을 지나며 달라지오?',
  concern_pattern: '유독 이 고민이 반복되는 이유는 무엇이오?',
  concern_turn: '지금의 고민은 다음 흐름에서 어떻게 달라져 보일까?',
  spine_depth: '남들은 장점이라는데, 나는 왜 그 일로 지치는 것이오?',
  ancestor: '이 성질은 어느 자리에서 왔소?',
  spine_scene: '그 되풀이는 어떤 장면으로 나타나오?',
};

export default function NextReading({ cuts, onOpen, lensId: readingLens }: { cuts: LockedCut[]; onOpen?: () => void; lensId?: string }) {
  const currentLens = useSession(s => s.cur);
  const concern = useSession(s => s.concern);
  const [selected, setSelected] = useState<string | null>(null);
  const panelId = useId();
  const lensId = readingLens ?? currentLens;
  const rows = selectPreviewCuts(cuts, concern);
  const active = rows.find(c => c.id === selected) ?? rows[0];
  const question = (cut: LockedCut) => CHAPTER_QUESTIONS[cut.id.replace(/^lc_/, '')] ?? QUESTIONS[cut.id] ?? cut.title;
  if (!rows.length) return null;
  const rest = cuts.length - rows.length;
  const chars = cuts.reduce((n, c) => n + (c.chars ?? 0), 0);
  return <section className="next-reading" aria-label="이어지는 실제 해석">
    <p className="conversion-kicker">여기서 한 걸음 더</p>
    <h2>{CHARACTER_QUESTIONS[lensId] ?? '왜 같은 자리에서 다시 마음이 걸리는 것이오?'}</h2>
    <p className="conversion-note">지금 가장 마음에 걸리는 질문을 골라보시오. 그대의 실제 풀이에서 첫 대목을 꺼내 두었소.</p>
    <div className="preview-questions" role="group" aria-label="더 알아보고 싶은 질문">
      {rows.map((cut, i) => <button type="button" key={cut.id} aria-pressed={active.id === cut.id} aria-controls={panelId} onClick={() => setSelected(cut.id)}>
        <span aria-hidden="true">{String(i + 1).padStart(2, '0')}</span><span>{question(cut)}</span><span aria-hidden="true">{active.id === cut.id ? '✓' : '+'}</span>
      </button>)}
    </div>
    <article className="preview-focus" id={panelId} aria-live="polite" aria-atomic="true">
      <div>
        <p className="conversion-kicker">그 질문에 이어지는 실제 풀이</p>
        <h3>{question(active)}</h3>
        <p>{readingText(active.teaser ?? '')}</p>
        <LockedVeil />
        {/* ★ 어느 목패부터 열리는지 같이 적습니다. 이름은 서버가
            실어 보낸 것이오 — 화면이 지어내지 않습니다. */}
        <p className="preview-answer">이 대목을 읽은 이유와 자세한 해석은 「{active.title}」에서 이어지오.</p>
        <small>{active.need_tier_name}부터 열림 · {active.chars.toLocaleString()}자</small>
      </div>
    </article>
    <p className="conversion-note">전체 <b>{cuts.length}개 항목 · {chars.toLocaleString()}자</b>{rest > 0 ? ` · 이 밖에 ${rest}개 이야기가 더 이어지오.` : ''}</p>
    {onOpen && <button className="btn" onClick={onOpen}>이 질문의 다음 내용 · 구성과 가격 보기</button>}
  </section>;
}
