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

export const INLINE_READING_SLOTS = ['spine_depth', 'spine_scene', 'lens_bridge'];

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
    <ReadingSpeaker lensId={lensId} label={['강점이 짐으로 바뀐 정확한 조건', '반복된 장면에서 놓친 결정적 차이', '계속할 것과 멈출 것을 가르는 기준'][index]} />
    <p className="inline-paid-context">{PAIN_POINTS[concern]?.[index] ?? CHARACTER_QUESTIONS[lensId]}</p>
    <h3>{chapterQuestion}</h3>
    <p className="inline-paid-perspective">{lens.name}의 판정 기준 · {CHARACTER_QUESTIONS[lensId]}</p>
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
