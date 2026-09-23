"use client";
import { useRef } from 'react';
import { useAmbience } from '@/lib/ambience';
import type { Concern } from '@/lib/store';

export const ENTRY_QUESTIONS: Record<Concern, { question: string; promise: string; next: string }> = {
  money: { question: '버는 만큼, 내 돈도 남고 있소?', promise: '돈을 버는 방식과 지키는 습관을 함께 보오.', next: '내 돈이 모이는 방식까지 읽기' },
  work: { question: '잘해내고 있는데, 왜 버겁기만 할까.', promise: '일을 잘하는 힘과 나를 지치게 하는 책임을 보오.', next: '나에게 맞는 일의 방식 읽기' },
  love: { question: '사랑 앞에서, 나는 왜 이럴까.', promise: '마음을 주는 방식과 편안해지는 관계를 보오.', next: '내 사랑의 반복과 이유 읽기' },
  people: { question: '좋은 사람으로 지내는 게 지치오?', promise: '가까워지는 방식과 지켜야 할 경계를 보오.', next: '내 관계의 거리와 기준 읽기' },
  dir: { question: '다른 길을 골랐다면, 달랐을까.', promise: '선택할 때 지키고 싶은 기준부터 찾아보오.', next: '나에게 맞는 선택의 기준 읽기' },
  health: { question: '쉬는 날에도, 마음은 일하고 있소?', promise: '쉼을 깨우는 책임과 오늘 멈춰도 되는 기준을 가르오.', next: '내 쉼을 막는 원인 판정받기' },
  real_estate: { question: '집을 고르는 마음과 감당할 비용이 같은 방향이오?', promise: '매수·매도·이사에서 목적, 총비용, 나올 조건을 나누어 보오.', next: '내 부동산 판단의 기준 읽기' },
};

export default function EntryArt({ scene, caption, priority = false }: {
  scene: 'threshold' | 'desk' | 'night' | 'reading'; caption?: string; priority?: boolean;
}) {
  const artRef = useRef<HTMLElement>(null);
  useAmbience(scene === 'threshold' ? 'outside' : scene === 'reading' ? 'hall' : 'study', artRef);
  return <figure ref={artRef} className={`entry-art entry-art-${scene}`}>
    <img src={`/images/entry-v2/${scene}.webp`} alt="" width={1200} height={scene === 'threshold' ? 1800 : 800}
      loading={priority ? 'eager' : 'lazy'} fetchPriority={priority ? 'high' : 'auto'} decoding="async" />
    {caption && <figcaption>{caption}</figcaption>}
  </figure>;
}
