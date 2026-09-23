"use client";

import { LENS_BY_ID } from "@/lib/lenses";
import { useSession } from "@/lib/store";
import CharacterSpeech from './CharacterSpeech';

export const ELEMENT_ART: Record<string, string> = { 목: "wood", 화: "fire", 토: "earth", 금: "metal", 수: "water" };
const ELEMENT_NAME: Record<string, string> = { 목: "나무", 화: "불", 토: "흙", 금: "쇠", 수: "물" };
export type ReadingArt = "wood" | "fire" | "earth" | "metal" | "water" | "birth" | "time" | "daily" | "archive" | "action" | "share" | "payment";

export function ArtImage({ art, className = "", eager = false }: { art: ReadingArt; className?: string; eager?: boolean }) {
  return <img className={className} src={`/images/reading/${art}-v1.webp`} alt="" width={480} height={480} loading={eager ? "eager" : "lazy"} decoding="async" />;
}

export function IllustratedNote({ art, title, children }: { art: ReadingArt; title: string; children: React.ReactNode }) {
  return <CharacterSpeech><aside className="illustrated-note"><ArtImage art={art} /><div><strong>{title}</strong><div>{children}</div></div></aside></CharacterSpeech>;
}

type Guide = { art: ReadingArt | "guide" | "people" | "direction"; title: string; text: string };
const SCREEN_GUIDES: Record<string, Guide> = {
  a2: { art: "birth", title: "그대를 부를 이름", text: "별칭은 선택이오. 비워 두어도 사주 계산은 같소." },
  a3: { art: "birth", title: "해 · 달 · 날", text: "양력 생년월일을 적고, 태어난 고을을 골라주시오." },
  a4: { art: "time", title: "태어난 시간은 아는 만큼만", text: "정확한 시각을 알면 적고, 모르면 시간 없이 이어가시오." },
  a4b: { art: "people", title: "스스로 보는 나", text: "아는 성향이 있으면 고르시오. 모르면 그대로 이어가도 되오." },
  a5: { art: "guide", title: "풍운도령과 시작하는 첫 이야기", text: "여섯 그림 중 지금 마음에 걸리는 하나를 골라주시오." },
  a6: { art: "birth", title: "태어난 순간을 네 기둥으로", text: "해 · 달 · 날 · 시각이 명식의 각 자리에 대응하오." },
  a7: { art: "guide", title: "한 마디씩, 경험과 나란히", text: "읽은 해석이 실제 경험과 맞는지 알려주시오." },
  b1: { art: "archive", title: "어떤 이야기를 펼쳐볼까", text: "해석자의 관심 주제와 관점을 살펴보시오." },
  b2: { art: "people", title: "다른 사람, 다른 시선", text: "초상과 고민 주제를 보고, 궁금한 사람을 골라주시오." },
  b3: { art: "people", title: "이 사람의 해석을 만나기 전에", text: "주로 다루는 고민과 읽을 수 있는 범위를 확인하시오." },
  b4: { art: "birth", title: "내 명식 한눈에 보기", text: "먼저 기둥을 보고, 다섯 기운의 분포를 살펴보시오." },
  c1: { art: "archive", title: "이번에 펼칠 이야기", text: "어떤 질문을 다루는지 표지에서 먼저 살펴보시오." },
  c2: { art: "archive", title: "그림 → 핵심 → 근거", text: "각 그림은 읽는 주제를 안내하오. 해석은 경험과 함께 보시오." },
  c3: { art: "direction", title: "시간을 따라 흐름 읽기", text: "나이와 시기를 짚고, 그때의 해석을 함께 보시오." },
  c4: { art: "payment", title: "추가로 열리는 내용", text: "읽을 수 있는 범위와 가격을 보고 결정하시오." },
  c5: { art: "share", title: "나눌 내용부터 확인하시오", text: "공유 카드에 어떤 정보가 담기는지 먼저 살펴보시오." },
  c6: { art: "share", title: "읽고 남은 한마디", text: "도움이 된 점과 맞지 않았던 점을 함께 남겨도 좋소." },
  c7: { art: "archive", title: "해석을 한 장에 모으다", text: "핵심 문장과 근거, 해석의 단서를 함께 챙겨 가시오." },
  c8: { art: "share", title: "공유하기 전 미리보기", text: "담기는 정보와 제외되는 정보를 확인하시오." },
  d0: { art: "action", title: "읽은 이야기에서 작은 행동으로", text: "핵심 해석을 살펴보고, 오늘 해볼 일 하나를 챙기시오." },
  d1: { art: "payment", title: "실제 질문 · 첫 문장 · 가격", text: "결제 후 받는 답을 먼저 읽고 상품을 선택하시오." },
  d1b: { art: "archive", title: "가려진 결론의 첫 문장", text: "원인·갈림길·행동 중 무엇이 열리는지 먼저 보시오." },
  d2: { art: "payment", title: "결제 내역 확인", text: "선택한 상품과 결제 상태를 확인하는 자리요." },
  d3: { art: "archive", title: "열람할 이야기", text: "확인된 이용 범위에서 해석을 펼쳐보시오." },
  f2: { art: "archive", title: "나의 이야기 보관함", text: "읽은 해석과 구매 내역을 다시 찾을 수 있소." },
  g1: { art: "daily", title: "오늘의 한 장", text: "오늘의 해석을 읽고, 일상에 가져갈 작은 행동을 골라보시오." },
  g2: { art: "archive", title: "지나온 이야기 되짚기", text: "남겨 둔 기록을 지금의 경험과 나란히 보시오." },
  g3: { art: "daily", title: "잠시 쉬어 가는 자리", text: "읽은 말은 잠시 내려두고, 오늘의 생활로 돌아가도 좋소." },
  h1: { art: "people", title: "다음 시선을 만나다", text: "다른 해석자가 살펴보는 질문부터 확인하시오." },
  r1: { art: "share", title: "읽고 난 경험을 남기다", text: "실제로 읽으며 느낀 점을 그대의 말로 적어주시오." },
  legal: { art: "payment", title: "이용 전에 확인할 약속", text: "이용 조건 · 개인정보 · 환불 기준을 항목별로 살펴보시오." },
  s1: { art: "share", title: "건네받은 이야기", text: "공유된 명식과 해석을 함께 읽는 자리요." },
  error: { art: "archive", title: "다시 펼쳐보시오", text: "읽던 이야기를 다시 불러올 수 있소." },
  missing: { art: "direction", title: "이야기로 돌아가는 길", text: "대문에서 다시 시작하시오." },
};

export function ScreenReadingGuide({ screen }: { screen?: string }) {
  const guide = screen ? SCREEN_GUIDES[screen] : undefined;
  if (!guide) return null;
  const src = guide.art === "guide" ? "/char/pungun/greet.webp"
    : guide.art === "people" ? "/images/concerns/people-v1.webp"
    : guide.art === "direction" ? "/images/concerns/dir-v1.webp"
    : `/images/reading/${guide.art}-v1.webp`;
  return <aside className={`screen-reading-guide${guide.art === "guide" ? " with-portrait" : ""}`} aria-label="이 화면 읽는 법">
    <img src={src} width={112} height={112} alt="" decoding="async" />
    <CharacterSpeech lensId={guide.art === 'guide' ? 'pungun' : undefined}><div><strong>{guide.title}</strong><p>{guide.text}</p></div></CharacterSpeech>
  </aside>;
}

/** A literal diagram of the inputs, never a fabricated personal chart. */
export function BirthStructure({ hourKnown }: { hourKnown: boolean }) {
  return <figure className="birth-structure">
    <figcaption>입력한 정보가 이렇게 놓이오</figcaption>
    <div>{["해", "달", "날", "시간"].map((label, i) => <div key={label} className={i === 3 && !hourKnown ? "unknown" : ""}>
      <b>{label}</b><span aria-hidden="true">{i === 3 && !hourKnown ? "?" : "□"}<br />{i === 3 && !hourKnown ? "?" : "□"}</span>
      <small>{i === 3 && !hourKnown ? "비워 둠" : "두 글자"}</small>
    </div>)}</div>
    <p>{hourKnown ? "시간까지 알면 네 기둥, 여덟 글자" : "시간을 모르면 세 기둥, 여섯 글자"}로 살펴보오.</p>
  </figure>;
}

export function ElementArtwork({ element }: { element: string }) {
  const id = ELEMENT_ART[element];
  return id ? <ArtImage art={id as ReadingArt} className="element-art" /> : null;
}

export function ElementLegend() {
  return <div className="element-legend" aria-label="오행의 다섯 가지 이름">{Object.keys(ELEMENT_ART).map(el => <div key={el}>
    <ElementArtwork element={el} /><b>{ELEMENT_NAME[el]}</b><small>{el}</small>
  </div>)}</div>;
}

const CUT_ART: Record<string, ReadingArt | "concern" | "people" | "direction"> = {
  chart: "birth", pillars: "birth", spine: "concern", spine_depth: "concern", spine_scene: "concern",
  lack: "earth", balance: "earth", rarity: "birth", why: "concern", solace: "daily", place: "people",
  daeun_now: "direction", daeun_map: "direction", when: "time", yongsin: "wood", need: "wood",
  helper: "people", ancestor: "archive", root: "archive", axis: "people", sequence: "direction",
  concern: "concern", concern_scale: "concern", concern_pattern: "concern", concern_turn: "time", concern_face: "people",
  hindsight: "archive", counter: "direction", hope: "action", week: "action", closing_cut: "share",
};

/** Images identify subject matter; only the server text provides the interpretation. */
export function CutArtwork({ id, title, lensId: readingLens }: { id: string; title: string; lensId?: string }) {
  const concern = useSession(s => s.concern);
  const features = useSession(s => s.features);
  const currentLens = useSession(s => s.cur);
  const lensId = readingLens ?? currentLens;
  if (id === "sinsal") return <h2 className="lab">{title}</h2>; // This section already renders its own figures.
  if (["chart", "pillars", "balance", "lack"].includes(id)) return <><h2 className="lab">{title}</h2><ElementLegend /></>;
  const el = ["yongsin", "need"].includes(id) ? features?.yongsin : null;
  if (["yongsin", "need"].includes(id) && !el) return <><h2 className="lab">{title}</h2><ElementLegend /></>;
  const art = (el && ELEMENT_ART[el]) || CUT_ART[id];
  const portrait = !art;
  const src = portrait ? `/char/${LENS_BY_ID[lensId] ? lensId : "pungun"}/bust.webp`
    : art === "concern" ? `/images/concerns/${concern}-v1.webp`
    : art === "people" ? "/images/concerns/people-v1.webp"
    : art === "direction" ? "/images/concerns/dir-v1.webp"
    : `/images/reading/${art}-v1.webp`;
  return <div className={`cut-art-heading${portrait ? " with-portrait" : ""}`}>
    <img src={src} width={96} height={96} alt="" loading="lazy" decoding="async" />
    <div><small>{portrait ? `${LENS_BY_ID[lensId]?.name ?? "풍운도령"}의 시선` : "이번에 살펴볼 자리"}</small><h2>{title}</h2></div>
  </div>;
}

export function ReadingPath() {
  return <ol className="reading-path" aria-label="읽는 순서">
    {([ ["birth", "근거 보기", "태어난 정보에서 출발"], ["archive", "나와 비교", "해석과 경험을 나란히"], ["action", "하나 실천", "오늘 할 일 챙기기"] ] as const).map(([art, title, text], i) => <li key={art}>
      <ArtImage art={art} /><span>{i + 1}</span><b>{title}</b><small>{text}</small>
    </li>)}
  </ol>;
}
