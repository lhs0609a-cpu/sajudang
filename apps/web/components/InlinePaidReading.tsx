"use client";

import type { LockedCut } from '@shared/chart';
import { useEffect, useRef } from 'react';
import { track } from '@/lib/track';
import { saveReadingIntent } from '@/lib/reading-intent';
import { useSession } from '@/lib/store';
import { LENS_BY_ID } from '@/lib/lenses';
import { CHARACTER_QUESTIONS, CHAPTER_QUESTIONS } from '@/lib/curiosity';
import { readingText, READING_QUESTIONS } from '@/lib/reading-journey';
import { selectPreviewCuts } from '@/lib/preview-selection';
import { ReadingSpeaker } from './ReadingVoice';
import CharacterSpeech from './CharacterSpeech';
import { characterConcern } from '@/lib/character-topic';
import { useRouter } from 'next/navigation';

/**
 * 무료 구간에서 **잠긴 풀이를 맛보이는 자리.**
 *
 * ★ 한 자리뿐입니다 (2026-09-25).
 *
 *   손님이 무료 구간 전문을 붙여 놓고 말했습니다 — 「왜 전체가 풀이가
 *   어렵고 와닿지가 않지? 전체 다 그래.」 세어 보니 한 장에 페이월로
 *   부르는 말이 **25.6번**이었습니다. 이 상자가 두 번(`spine_depth` ·
 *   `lens_bridge`), 끝의 페이월이 한 번, 그 셋이 각각 같은 물음을 다시
 *   내서 「버틸 힘은 있는데…」 한 줄이 한 장에 네 번 섰습니다.
 *
 *   읽다가 광고판에 자꾸 부딪히면 손님은 글을 못 믿습니다. 값이 오가는
 *   자리는 하나로 족합니다 — **뒤쪽 한 곳**에 둡니다. 앞에 두면 그 사람을
 *   들어 보기 전에 값을 먼저 말하는 셈이고, 무료 구간이 그 사람을 들려
 *   주려고 있는 자리이기 때문입니다.
 *
 *   ★ 어느 자리가 가장 잘 서는지는 **계측이 답할 일**입니다
 *     (`inline_offer_view` · `inline_offer_click` 이 이미 찍습니다).
 *     감으로 늘리지 마시오 — 늘리면 또 25번이 됩니다.
 */
export const INLINE_READING_SLOTS = ['lens_bridge'];

// Editorial questions, not popularity claims or promised personal outcomes.
const PAIN_POINTS: Record<string, [string, string, string]> = {
  money: ['벌 때는 분명 애썼는데, 왜 내 몫은 남지 않을까?', '돈이 새는 이유가 소비 습관일까, 사람과의 약속일까?', '같은 방식으로 더 벌면 풀릴까, 남기는 기준부터 바꿔야 할까?'],
  work: ['잘한다는 말을 들을수록, 왜 내 일만 늘어날까?', '지금 버거운 건 일이 안 맞아서일까, 맡은 범위가 흐려져서일까?', '계속할 일과 방식을 바꿀 일, 무엇으로 나눌까?'],
  love: ['마음을 줄수록 왜 나만 더 애쓰는 기분이 들까?', '말하지 않아 몰랐던 걸까, 말했는데도 달라지지 않은 걸까?', '가까워져도 편안한 관계와 계속 증명해야 하는 관계는 어디서 갈릴까?'],
  people: ['좋은 사람으로 남으려다 내 시간까지 내주고 있지는 않을까?', '도와준 뒤 남는 서운함은 어느 약속에서 시작됐을까?', '관계를 아끼면서도 내 몫을 지킬 선은 어디일까?'],
  dir: ['확신이 부족한 걸까, 하나를 고르면 잃을 것이 아까운 걸까?', '남에게 설명하기 좋은 선택과 내가 살고 싶은 하루는 같을까?', '지금 지킬 기준과 바꿔도 되는 기준은 무엇일까?'],
  health: ['쉬고 있는데도 마음이 계속 일하는 까닭은 무엇일까?', '하루가 버거운 건 할 일이 많아서일까, 끝내는 기준이 없어서일까?', '무엇을 더 챙기기보다, 어떤 부담부터 덜어볼까?'],
};

export default function InlinePaidReading({after, cuts, lensId, onOpen}: {after: string; cuts: LockedCut[]; lensId: string; onOpen: () => void}) {
  const router = useRouter();
  const concern = characterConcern(lensId, useSession(s => s.concern));
  const chartId = useSession(s => s.chartId);
  const review = useSession(s => s.hookReview);
  const index = INLINE_READING_SLOTS.indexOf(after);
  const lens = LENS_BY_ID[lensId];
  const rejected = review?.chartId === chartId && review.concern === concern && review.lensId === lensId
    && Object.values(review.answers).some(answer => answer === false);
  const cut = selectPreviewCuts(cuts, concern)[index];
  const enabled = index >= 0 && !!lens?.price && !rejected && !!cut?.teaser;
  const node = useRef<HTMLElement | null>(null);
  useEffect(() => {
    if (!enabled || !node.current) return;
    let timer: ReturnType<typeof setTimeout> | undefined;
    const observer = new IntersectionObserver(([entry]) => {
      clearTimeout(timer);
      if (entry.isIntersecting && entry.intersectionRatio >= .5) timer = setTimeout(() => {
        track('inline_offer_view', location.pathname === '/pay' ? 'd0' : 'c2', {stage:index+1});
        observer.disconnect();
      }, 1000);
    }, {threshold: .5});
    observer.observe(node.current);
    return () => {clearTimeout(timer);observer.disconnect();};
  }, [enabled, index, cut?.id, lensId, chartId, concern]);
  if (!enabled) return null;
  const chapterQuestion = CHAPTER_QUESTIONS[cut.id.replace(/^lc_/, '')]
    ?? (cut.id === 'concern_pattern' ? READING_QUESTIONS[concern]
      : ['concern_turn', 'daeun_map'].includes(cut.id) ? '지금과 다음 흐름을 나란히 읽으면 무엇이 달라질까?' : cut.title);
  return <CharacterSpeech lensId={lensId}><aside ref={node} className="inline-paid-reading" data-lens={lensId} data-chapter={cut.id} aria-label={`${lens.name}의 결제 후 공개되는 판정`}>
    {/* ★ 물음은 **하나**입니다 (2026-09-25).
     *
     *   여기 물음이 셋 연달아 섰습니다 — 고민 물음(PAIN_POINTS) · 그 컷이
     *   답하는 물음(chapterQuestion) · 캐릭터 물음(CHARACTER_QUESTIONS).
     *   셋이 다 물음표로 끝나니 손님은 무엇에 답을 받는지 모릅니다.
     *
     *   남기는 것은 **그 컷이 답하는 물음**입니다 — 값을 치르면 열리는 것이
     *   그것이기 때문입니다. 고민 물음은 맥락 한 줄로 남기고, 캐릭터 물음은
     *   뺍니다(무료 끝의 페이월이 이미 냅니다 — 한 장에 네 번 서던 줄이오). */}
    <ReadingSpeaker lensId={lensId} label={['강점이 짐으로 바뀐 정확한 조건', '반복된 장면에서 놓친 결정적 차이', '계속할 것과 멈출 것을 가르는 기준'][index]} />
    <p className="inline-paid-context">{PAIN_POINTS[concern]?.[index] ?? CHARACTER_QUESTIONS[lensId]}</p>
    <h3>{chapterQuestion}</h3>
    <p className="inline-paid-perspective">{lens.name}의 판정 기준</p>
    <blockquote><span>결제 후 열리는 본문의 실제 첫 문장</span><p>{readingText(cut.teaser ?? '')}</p></blockquote>
    <div className="inline-paid-mask" aria-label="결론이 갈리는 다음 해석은 결제 후 공개됩니다">
      <p><strong>여기서 결론이 갈립니다.</strong> 지금 보이는 말 뒤에는 ‘왜 반복되는지’, ‘어느 선택을 멈출지’, ‘언제 다시 확인할지’가 이어집니다.</p>
      <span aria-hidden="true"><i/><i/><i/></span>
    </div>
    <p className="inline-paid-scope">「{cut.title}」의 원인·분기·행동 판정 · 약 {cut.chars.toLocaleString()}자 · {cut.need_tier_name}부터 열립니다.</p>
    <button className="btn" onClick={() => {
      if (chartId) saveReadingIntent({chartId,lensId,concern,question:chapterQuestion,title:cut.title,tier:cut.need_tier_name,tierId:cut.need_tier,chapterId:cut.id});
      track('inline_offer_click', location.pathname === '/pay' ? 'd0' : 'c2', {stage:index+1});
      useSession.getState().set({cur:lensId});
      track('price_view','d1');
      router.push(`/pay?step=d1&direct=1&tier=${encodeURIComponent(cut.need_tier)}`);
    }}>이 풀이 열기 · 결제하기</button>
    <p className="inline-paid-continue">무료 이야기는 아래에서 계속 읽을 수 있소 ↓</p>
  </aside></CharacterSpeech>;
}
