/**
 * 제작 프롬프트 한 벌 — 창과 현황판이 **같은 글**을 냅니다.
 *
 * ★ 왜 밖으로 뺐나 (2026-09-04)
 *
 *   프롬프트를 만드는 자리가 `PromptModal` 안에만 있었습니다. 그런데
 *   에셋 현황판이 **없는 자리에 프롬프트를 바로 펴** 보여야 해서
 *   같은 글이 두 군데서 필요해졌습니다. 붙이는 규칙(워터마크 금지·
 *   가장자리 비우기·초상 크롭)을 두 벌로 두면 한쪽만 고쳐집니다 —
 *   이 집은 이름도 규칙도 한 벌로 둡니다.
 */
export type PromptKind = "scene" | "char" | "figure";

export interface PromptEntry {
  title: string;
  who?: string | null;
  /* 대문처럼 계절을 타는 장면 — 꽃이 계절마다 달라 그림이 넉 장 필요합니다 */
  seasonal?: boolean;
  seasons?: Record<string, string> | null;
  spec?: string[] | null;
  hint?: string | null;
  image: string | null;
  motion: string | null;
  preset: string;
  ratio: string;
  duration: string;
  loop: boolean;
  tint: boolean;
  still: boolean;
  note?: string | null;
  revised?: string | null;
  /*
   * ★ 이 그림이 **그 화면에서 어떻게 걸리는가** (2026-09-04).
   *
   *   원본은 전부 9:16 세로인데 인라인 장면은 4:3 상자로 잘라 씁니다 —
   *   세로의 42%만 보입니다. 그걸 모르고 그리면 주제가 잘려 나갑니다.
   *   손으로 안 적습니다: `tools/prompt_use.py` 가 코드에서 읽어
   *   박습니다. 화면을 옮기면 다시 돌리면 됩니다.
   */
  use?: string | null;
}

export interface Bundle {
  ANIMBASE: string;
  TINT: string;
  PIPE: string;
  /*
   * ★ 공통 촬영 규칙 — 명령어마다 손으로 적지 않습니다.
   *
   *   9:16 원본 · 글자와 워터마크 금지 · 세로 가운데 42% 안에 주제 ·
   *   가장자리 6% 비우기 · 폰에서 396px 로 읽히는 덩어리.
   *   쉰여덟 장에 손으로 적으면 한 장은 빠집니다. 한 자리에 두고
   *   **복사되는 글에 붙여서** 냅니다.
   */
  SHOT: string;
  SHOT_TINT: string;
  SHOT_LOOP: string;
  SHOT_FILL: string;
  /* 초상은 **얼굴로 잘라** 씁니다 — 눈높이 37% 를 붙잡고 2.6배.
     그 말이 없으면 턱이나 이마에 크롭이 떨어집니다. */
  SHOT_CHAR: string;
  SHOT_FIGURE: string;
  scenes: Record<string, PromptEntry>;
  figures: Record<string, PromptEntry>;
  /* 스무 사람의 초상. tools/char_sheet.py --json 이 넣습니다. */
  chars?: Record<string, PromptEntry>;
}

let cache: Bundle | null = null;

/** 묶음 한 벌. 두 번째부터는 받아 둔 것을 줍니다. */
export async function loadPrompts(): Promise<Bundle> {
  if (cache) return cache;
  const res = await fetch("/asset-prompts.json");
  cache = (await res.json()) as Bundle;
  return cache;
}

export function entryOf(
  data: Bundle | null, kind: PromptKind, id: string,
): PromptEntry | undefined {
  if (!data) return undefined;
  const grp = kind === "scene" ? data.scenes
            : kind === "char" ? (data.chars ?? {})
            : data.figures;
  return grp?.[id];
}

/**
 * 그림 명령어 — **공통 규칙을 붙여서** 냅니다.
 *
 * ★ 전에는 규칙이 어디에도 없었습니다 — 쉰여덟 장 중 워터마크를
 *   막는 줄이 **하나도** 없었고, 가장자리를 비우라는 줄은 여섯
 *   장에만 있었습니다. 그림을 맡기는 사람은 카드 하나를 복사해
 *   붙일 뿐이니, 규칙은 그 복사되는 글 안에 있어야 합니다.
 *
 *   장면마다 다른 몫(무채색·루프 이음새·글 얹히는 자리)은 그
 *   장면일 때만 붙습니다.
 */
export function imagePrompt(
  data: Bundle | null, kind: PromptKind, id: string, season?: string,
): string | null {
  const e = entryOf(data, kind, id);
  if (!e) return null;
  const seasonal = kind === "scene" && !!e.seasonal;
  const image = seasonal && season
    ? (e.seasons?.[season] ?? e.image) : e.image;
  if (!image || !data) return image ?? null;
  const add = [kind === "char" ? data.SHOT_CHAR
             : kind === "figure" ? data.SHOT_FIGURE
             : data.SHOT];
  if (kind === "scene") {
    if (e.tint) add.push(data.SHOT_TINT);
    if (e.loop) add.push(data.SHOT_LOOP);
    if ((e.use ?? "").includes("통째로 덮고")) add.push(data.SHOT_FILL);
  }
  return [image, ...add].join("\n\n");
}

/** 파일을 어디에 두는가. */
export function dirOf(kind: PromptKind, id: string): string {
  return kind === "scene" ? `/scene/${id}/`
       : kind === "char" ? `/char/${id}/`
       : `/sinsal/${id}/`;
}
