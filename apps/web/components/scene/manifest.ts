/**
 * 장면 에셋 24종 — docs/10_에셋제작_발주서.md §3
 *
 * 현재 0/24. 에셋이 들어오면 /public/scene/{id}/ 에 넣으면
 * Scene 컴포넌트가 자동으로 그걸 씁니다. 코드 수정 불필요.
 *
 *   public/scene/{id}/clip.webm   VP9
 *   public/scene/{id}/clip.mp4    H.264
 *   public/scene/{id}/poster.jpg  정지컷 (reduced-motion 대체본)
 */
export type Preset = "Static" | "Dolly In" | "Dolly Right";
export type Ratio = "9:16" | "16:9" | "3:4" | "1:1";

export interface SceneSpec {
  id: string;
  name: string;
  preset: Preset;
  ratio: Ratio;
  seconds: number;
  loop: boolean;
  /** 무채색으로 뽑고 앱에서 색을 입히는 장면. (docs/10 §4) */
  tint?: boolean;
  /** 계절에 따라 하늘·꽃이 바뀌는 장면 */
  seasonal?: boolean;
}

export const SCENES: SceneSpec[] = [
  { id: "gate", name: "대문 · 사계", preset: "Dolly In", ratio: "9:16", seconds: 5, loop: false, tint: true, seasonal: true },
  { id: "door", name: "열리는 문", preset: "Static", ratio: "9:16", seconds: 2, loop: false },
  { id: "desk", name: "붓·벼루·빈 종이", preset: "Static", ratio: "16:9", seconds: 3, loop: true },
  { id: "ink", name: "먹이 번지는 종이", preset: "Static", ratio: "16:9", seconds: 2, loop: false },
  { id: "room", name: "실내·병풍·주렴", preset: "Static", ratio: "16:9", seconds: 4, loop: true },
  { id: "fork", name: "갈림길", preset: "Static", ratio: "16:9", seconds: 3, loop: true },
  { id: "altar", name: "명식 받침", preset: "Static", ratio: "16:9", seconds: 4, loop: false, tint: true },
  { id: "facing", name: "마주앉은 자리", preset: "Static", ratio: "16:9", seconds: 3, loop: true },
  { id: "shelf", name: "진열대", preset: "Static", ratio: "16:9", seconds: 3, loop: true },
  { id: "hall", name: "스무 자리", preset: "Dolly In", ratio: "16:9", seconds: 4, loop: false },
  { id: "seat", name: "그 사람의 자리", preset: "Static", ratio: "3:4", seconds: 3, loop: true, tint: true },
  { id: "scroll", name: "펼쳐지는 두루마리", preset: "Static", ratio: "16:9", seconds: 3, loop: false },
  { id: "fold", name: "반쯤 접힌 두루마리", preset: "Static", ratio: "16:9", seconds: 2, loop: false },
  { id: "untie", name: "붉은 끈·개봉", preset: "Static", ratio: "1:1", seconds: 2, loop: false },
  { id: "handle", name: "문고리·그림자", preset: "Dolly In", ratio: "9:16", seconds: 3, loop: false },
  { id: "roadmap", name: "대운 길", preset: "Dolly Right", ratio: "16:9", seconds: 4, loop: false, tint: true },
  { id: "cardbg", name: "공유 카드 문양", preset: "Static", ratio: "1:1", seconds: 3, loop: true, tint: true },
  { id: "tray", name: "목패 늘어놓은 상", preset: "Static", ratio: "16:9", seconds: 2, loop: true },
  { id: "coin", name: "엽전", preset: "Static", ratio: "1:1", seconds: 2, loop: false },
  { id: "tea", name: "다과상", preset: "Static", ratio: "16:9", seconds: 3, loop: true },
  { id: "sealbook", name: "인장첩", preset: "Static", ratio: "3:4", seconds: 2, loop: false },
  { id: "oldpaper", name: "오래된 종이", preset: "Static", ratio: "16:9", seconds: 3, loop: true },
  { id: "wall", name: "후기 벽", preset: "Static", ratio: "16:9", seconds: 3, loop: true },
  { id: "banner", name: "등불 배너", preset: "Static", ratio: "16:9", seconds: 3, loop: true },
];

export const SCENE_BY_ID: Record<string, SceneSpec> =
  Object.fromEntries(SCENES.map((s) => [s.id, s]));

export const RATIO_BOX: Record<Ratio, [number, number]> = {
  "9:16": [280, 498],
  "16:9": [400, 225],
  "3:4": [300, 400],
  "1:1": [320, 320],
};

/** 계절 팔레트 — docs/09 §5 */
export const SEASON_PALETTE = {
  spring: { ko: "봄 · 벚꽃", sky: "#221A3A", flower: "#F2B8CC", air: "나비" },
  summer: { ko: "여름 · 능소화", sky: "#1A1230", flower: "#E58BA5", air: "반딧불" },
  autumn: { ko: "가을 · 국화", sky: "#241A28", flower: "#E5C87A", air: "낙엽" },
  winter: { ko: "겨울 · 매화", sky: "#161632", flower: "#F2ECE4", air: "눈" },
} as const;
