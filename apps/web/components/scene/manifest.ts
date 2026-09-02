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

/**
 * 일간 색을 입히는 방식. (docs/10 §4)
 *
 *   recolor  무채색으로 발주한 클립. 흑백으로 깔고 --c 를 통째로 덧칠한다.
 *            색이 전부 앱에서 나오므로 발주가 안 된 장면의 기본값이다.
 *   grade    **컬러로 온 클립.** 원래 색을 그대로 두고 --c 를 옅게만 얹는다.
 *
 * ★ 컬러 에셋에 recolor 를 걸면 안 됩니다. grayscale(1) 이 원본 색을
 *   통째로 버립니다. 대문이 실제로 이 사고를 냈습니다 — 능소화 분홍,
 *   등불 주황, 반딧불이 전부 사라지고 보라 단색으로 나왔습니다.
 *   에셋이 들어오면 그 클립이 무채색인지 보고 이 값을 정하세요.
 */
export type TintMode = "recolor" | "grade";

export interface SceneSpec {
  id: string;
  name: string;
  preset: Preset;
  ratio: Ratio;
  seconds: number;
  loop: boolean;
  /** 일간 색을 입히는 장면. 방식은 TintMode 주석 참고. (docs/10 §4) */
  tint?: TintMode;
  /** 계절에 따라 하늘·꽃이 바뀌는 장면 */
  seasonal?: boolean;
  /**
   * ★ 어디를 보여 줄 것인가 (CSS object-position).
   *
   *   들어오는 영상은 **전부 9:16 세로**입니다(2026-09-01 부터). 그런데
   *   글 위에 얹는 장면은 16:9 띠로 보여 줍니다 — 세로를 그대로 흘리면
   *   폭의 178% 높이가 되어 아래 버튼이 화면 밖으로 밀립니다. a5 의
   *   고민 여섯 칸이 그렇게 묻혔습니다.
   *
   *   그래서 `ratio` 는 **보여 주는 상자**이고, 남는 데는 잘립니다.
   *   가운데가 답이 아닌 장면만 여기에 적습니다.
   */
  focus?: string;
  /**
   * ★ 보여 주는 상자 (ratio 와 다른 뜻).
   *
   *   `ratio` 는 **그림을 어떤 비율로 그리는가**(발주서 §3)이고,
   *   `box` 는 **화면에서 어느 비율로 보여 주는가**입니다. 원본이 전부
   *   9:16 이 되면서 둘이 갈렸습니다.
   *
   *   글 위에 얹는 장면의 기본은 4:3 입니다. 왜 4:3 인가 —
   *
   *     9:16 그대로   폭의 178% 높이. 440px 화면에서 782px.
   *                   a5 의 고민 여섯 칸이 통째로 화면 밖으로 밀립니다.
   *     16:9 띠       248px. 안전하지만 세로의 32%만 보입니다.
   *     4:3           330px. 세로의 42%가 보이고 버튼이 아직 위에 옵니다.
   *
   *   더 키우려면 여기서 올립니다. 올릴 때는 그 화면의 버튼이 첫 화면에
   *   남는지 눈으로 보세요 — 묻히면 값을 잃습니다.
   */
  box?: Ratio;
}

export const SCENES: SceneSpec[] = [
  { id: "gate", name: "대문 · 사계", preset: "Dolly In", ratio: "9:16", seconds: 5, loop: false, tint: "grade", seasonal: true },
  // ★ 아무 화면도 이걸 안 부릅니다 (tools/asset_audit.py).
  //   만들어도 안 나옵니다. 대문(gate)이 이미 "열려 있는 문" 을
  //   보여주고, 문고리(handle)가 릴레이에서 그 몫을 합니다.
  //   발주 목록에서 뺍니다 — 안 쓸 것을 만들지 않습니다.
  //   쓸 자리가 생기면 이 줄을 되살리고 화면에 <Scene id="door"/> 를 넣으세요.
  // { id: "door", name: "열리는 문", preset: "Static", ratio: "9:16", seconds: 2, loop: false },
  { id: "desk", name: "붓·벼루·빈 종이", preset: "Static", ratio: "16:9", seconds: 3, loop: true },
  { id: "ink", name: "먹이 번지는 종이", preset: "Static", ratio: "9:16", seconds: 5, loop: false },
  { id: "room", name: "실내·병풍·주렴", preset: "Static", ratio: "9:16", seconds: 5, loop: true },
  /*
   * ★ a4b 「성향 4글자」 몫. 이 화면은 발주서(docs/10)가 쓰인 뒤에
   *   붙어서 제 장면이 없었고, a3 의 「먹이 번지는 종이」를 그대로
   *   갖다 쓰고 있었습니다. 두 화면이 잇달아 나오는데 그림이 같으면
   *   손님은 화면이 안 넘어간 줄 압니다.
   *
   *   이 화면이 하는 일은 **넉 자와 여덟 글자를 맞대 보는 것**입니다.
   *   (셈에는 안 들어가고 어긋난 자리를 찾는 데만 씁니다)
   */
  { id: "mirror", name: "맞대어 보는 자리", preset: "Static", ratio: "9:16", seconds: 5, loop: true },
  { id: "fork", name: "갈림길", preset: "Static", ratio: "16:9", seconds: 3, loop: true, focus: "50% 55%" },
  { id: "altar", name: "명식 받침", preset: "Static", ratio: "9:16", seconds: 5, loop: false, tint: "recolor" },
  { id: "facing", name: "마주앉은 자리", preset: "Static", ratio: "9:16", seconds: 5, loop: true },
  { id: "shelf", name: "진열대", preset: "Static", ratio: "16:9", seconds: 3, loop: true },
  { id: "hall", name: "스무 자리", preset: "Dolly In", ratio: "16:9", seconds: 4, loop: false },
  { id: "seat", name: "그 사람의 자리", preset: "Static", ratio: "3:4", seconds: 3, loop: true, tint: "recolor" },
  // ★ 16:9 였습니다. 그런데 쓰는 자리 둘(리포트 표지 c1 · 분석지)이
  //   `.sceneart.hero` — aspect-ratio 9/16 + object-fit:cover 라
  //   **가로의 약 68%가 잘려 나갑니다.** 두루마리는 세로로 펼쳐지는
  //   물건이니 9:16 이 맞습니다. 아직 안 만든 에셋이라 지금이 고칠 때입니다.
  { id: "scroll", name: "펼쳐지는 두루마리", preset: "Static", ratio: "9:16", seconds: 3, loop: false },
  { id: "fold", name: "반쯤 접힌 두루마리", preset: "Static", ratio: "16:9", seconds: 2, loop: false },
  { id: "untie", name: "붉은 끈·개봉", preset: "Static", ratio: "1:1", seconds: 2, loop: false },
  { id: "handle", name: "문고리·그림자", preset: "Dolly In", ratio: "9:16", seconds: 3, loop: false },
  { id: "roadmap", name: "대운 길", preset: "Dolly Right", ratio: "16:9", seconds: 4, loop: false, tint: "recolor" },
  { id: "cardbg", name: "공유 카드 문양", preset: "Static", ratio: "1:1", seconds: 3, loop: true, tint: "recolor" },
  { id: "tray", name: "목패 늘어놓은 상", preset: "Static", ratio: "16:9", seconds: 2, loop: true },
  { id: "coin", name: "엽전", preset: "Static", ratio: "1:1", seconds: 2, loop: false },
  { id: "tea", name: "다과상", preset: "Static", ratio: "16:9", seconds: 3, loop: true },
  { id: "sealbook", name: "인장첩", preset: "Static", ratio: "3:4", seconds: 2, loop: false },
  // ★ 16:9 로 적혀 있었지만 실제로 들어온 그림은 9:16 입니다
  //   (2026-09-01 부터 원본이 전부 세로). 적힌 값을 그림에 맞춥니다.
  //
  //   focus 를 아래로 내린 이유 — 4:3 상자는 세로의 42%만 보입니다.
  //   가운데로 두면 **인장과 눌린 꽃이 둘 다 잘려 나가고** 줄만 그은
  //   빈 종이가 남습니다. 70% 로 내리면 인장·꽃·종이 아래 끝이 다
  //   들어옵니다. 인장은 이 집의 표라 잘리면 안 됩니다.
  { id: "oldpaper", name: "오래된 종이", preset: "Static", ratio: "9:16", seconds: 3, loop: true, focus: "50% 70%" },
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
