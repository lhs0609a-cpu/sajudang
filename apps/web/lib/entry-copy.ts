import type { Concern } from "./store";

// Navigation promises only. Personal interpretations are rendered by the API.
export const ENTRY_CONCERNS: Record<Concern, { question: string; detail: string; next: string }> = {
  money: { question: "버는데, 왜 남는 돈은 없을까?", detail: "수입보다 먼저 살펴볼 소비와 책임의 경계", next: "돈을 벌고 쓰는 방식 더 살펴보기" },
  work: { question: "계속 버틸까, 다른 일을 찾을까?", detail: "잘하는 일과 나를 지치게 하는 일 구분하기", next: "일에서 힘을 쓰는 방식 더 살펴보기" },
  love: { question: "왜 좋아할수록 마음이 어려울까?", detail: "다가가는 방식과 서운함이 쌓이는 순간", next: "관계에서 반복하는 선택 더 살펴보기" },
  people: { question: "왜 나만 관계에 애쓰는 것 같을까?", detail: "배려하다 내 몫까지 잃는 순간 돌아보기", next: "사람 사이에서 지킬 경계 더 살펴보기" },
  dir: { question: "이대로 가도 괜찮을까?", detail: "남의 기대와 내가 원하는 선택 구분하기", next: "선택 앞에서 망설이는 이유 더 살펴보기" },
  health: { question: "쉬어도 왜 쉰 것 같지 않을까?", detail: "생활 속 책임과 휴식을 끊는 습관 살펴보기", next: "생활과 휴식의 균형 더 살펴보기" },
};
