"use client";

/**
 * 캐릭터 초상 — 스무 사람의 얼굴.
 *
 * ★ 여기가 통째로 없었습니다.
 *   `docs/10_에셋제작_발주서.md` §7 은 `/char/{id}/bust.png` 768×1024 를
 *   요구하고 제작 순서(§6)까지 정해 놓았는데, **그걸 그리는 코드가
 *   하나도 없었습니다.** `LensInfo` 에는 색(color)만 있고 그림을 가리키는
 *   필드가 없었습니다. 스무 장을 만들어도 갈 데가 없는 상태였습니다.
 *   (tools/asset_audit.py 가 잡았습니다)
 *
 * ★ 장면(Scene)과 같은 규칙입니다.
 *   파일이 있으면 그걸 쓰고, 없으면 자리표시로 버팁니다. 코드를 안 고치고
 *   `/public/char/{id}/` 에 넣기만 하면 그때부터 그게 나옵니다.
 *
 *     public/char/{id}/bust.webp    768×1024 투명 · 눈높이 y=380
 *     public/char/{id}/clip.webm    움직이는 초상 (선택)
 *     public/char/{id}/poster.jpg   clip 의 첫 프레임
 *
 * ★ 자리표시는 얼굴을 흉내내지 않습니다.
 *   반쯤 그린 얼굴은 없는 것보다 나쁩니다. 그 사람의 색과 한자 한 글자로
 *   자리만 잡습니다 — 에셋이 오면 그대로 갈아 끼웁니다.
 */
import { useEffect, useRef, useState } from "react";
import type { LensInfo } from "@/lib/lenses";
import { useSession } from "@/lib/store";
import PromptModal from "@/components/scene/PromptModal";

type Size = "chip" | "talk" | "card" | "full";

/*
 * ★ 표정.
 *
 *   얼굴 한 장으로 다 하면 **짚는 순간과 누그러뜨리는 순간이 같은
 *   얼굴**이 됩니다. 훅 0단은 아픈 데를 찌르는 자리이고, 만류 문구는
 *   그만 보라고 달래는 자리인데, 같은 표정이면 둘 다 힘을 잃습니다.
 *
 *   문장 뱅크를 세어 보고 셋으로 정했습니다 —
 *     짚는 말 26 · 누그러뜨리는 말 19 · 아니라고 하는 말 7
 *   「아니라고 하는 말」은 짚는 얼굴에 접습니다. 일곱 마디를 위해
 *   스무 명분을 더 그리는 것은 값이 안 맞습니다.
 *
 *   파일이 없으면 기본 얼굴로 내려옵니다 — 장면과 같은 규칙입니다.
 */
export type Mood = "base" | "cut" | "soft";

/*
 * ★ 초상은 **웹피**로 옵니다 (2026-09-04).
 *
 *   PNG 로는 768×1024 한 장이 800KB 였습니다. 스무 명이면 16MB 이고,
 *   첫 장은 손님이 도령의 첫 마디를 읽기도 전에 받습니다. 팔레트로
 *   줄이는 길은 재 보고 접었습니다 — 볼의 홍조가 사라지고 이마에 띠가
 *   생깁니다. 꼴을 바꾸니 80~110KB 로 갑니다 (tools/place_char).
 *
 *   ★ PNG 로 물러섭니다. 옛 그림이 그대로 살고, 새로 넣는 것만
 *     가벼워집니다.
 */
const FILE: Record<Mood, string[]> = {
  base: ["bust.webp", "bust.png"],
  cut: ["bust_cut.webp", "bust_cut.png"],     // 짚는 얼굴 — 훅 찌르기
  soft: ["bust_soft.webp", "bust_soft.png"],  // 누그러뜨리는 얼굴 — 만류·마무리
};

const BOX: Record<Size, { w: number; h: number }> = {
  chip: { w: 48, h: 64 },     // 진열대 목록
  /*
   * 대사 옆. 얼굴이 글을 이기면 안 되고, 안 보이면 놓은 뜻이 없습니다.
   * 한 줄 높이(약 3.5줄)에 맞춥니다.
   */
  talk: { w: 66, h: 88 },
  card: { w: 132, h: 176 },   // 릴레이 카드 · 인장첩
  full: { w: 288, h: 384 },   // 그 사람의 자리 (b3)
};

/** 파일이 있는지 본다. 없으면 자리표시로 간다 — Scene 과 같은 방식. */
function useBust(id: string, mood: Mood) {
  const [src, setSrc] = useState<string | null | undefined>(undefined);
  useEffect(() => {
    let alive = true;
    const ok = (u: string) =>
      fetch(u, { method: "HEAD" }).then((r) => r.ok).catch(() => false);
    const first = async (names: string[]) => {
      for (const n of names) {
        const u = `/char/${id}/${n}`;
        if (await ok(u)) return u;
      }
      return null;
    };

    (async () => {
      // 그 표정이 있으면 그걸, 없으면 기본 얼굴로 내려옵니다.
      if (mood !== "base") {
        const want = await first(FILE[mood]);
        if (want) {
          if (alive) setSrc(want);
          return;
        }
      }
      const base = await first(FILE.base);
      if (alive) setSrc(base);
    })();
    return () => { alive = false; };
  }, [id, mood]);
  return src;
}

/*
 * 움직이는 초상이 있는가.
 *
 * ★ 진열대 조각(48×64)에서는 안 씁니다. 스무 명이 한 화면에 늘어서는
 *   자리라 영상 스무 벌을 한꺼번에 받아 옵니다.
 *
 * ★ 대사 옆(talk)에서는 **안 씁니다** (2026-09-04).
 *
 *   9-03 에 「이제 얼굴로 잘라 쓰니 눈과 입이 보인다」고 켰습니다. 보이는
 *   것은 맞지만, 켜 놓으니 **대사 옆 얼굴이 정면이 아니게** 됐습니다 —
 *   영상은 옆을 보는 초상에서 뽑은 것이고, 정면 초상을 새로 넣어도
 *   영상이 그 위를 덮습니다. 초상만 갈아 끼우고는 화면이 안 바뀌는
 *   자리가 여기였습니다 (같은 지적이 네 번 왔습니다).
 *
 *   대사 옆은 **말하는 사람의 눈을 마주 보는 자리**입니다. 움직임보다
 *   정면이 먼저라, 여기서는 멈춘 정면 초상만 씁니다. 큰 초상(full·card)
 *   은 그대로 영상을 쓰되, 그 영상도 정면으로 다시 뽑아야 합니다.
 *
 * ★ 기본 얼굴일 때만 씁니다. 표정이 따로 있는 자리는 그 표정이 뜻이라,
 *   움직이는 기본 얼굴로 덮으면 뜻이 사라집니다.
 */
function useClip(id: string, on: boolean) {
  const [ok, setOk] = useState(false);
  useEffect(() => {
    if (!on) return;
    let alive = true;
    fetch(`/char/${id}/clip.webm`, { method: "HEAD" })
      .then((r) => { if (alive) setOk(r.ok); })
      .catch(() => {});
    return () => { alive = false; };
  }, [id, on]);
  return ok;
}


/*
 * 첫 인사 — **소리까지 있는** 한 번짜리 초상.
 *
 * ★ 왜 clip 과 따로 두나 (2026-09-04)
 *
 *   `clip.webm` 은 배경처럼 도는 초상입니다 — 소리 없이, 끝없이.
 *   첫 인사는 그 반대입니다. 도령이 고개를 들고 한 번 인사하고
 *   멈춥니다. 되풀이되면 인사가 아니라 태엽입니다.
 *
 *   그래서 파일도 따로 둡니다. 없으면 clip 으로, clip 도 없으면
 *   멈춘 초상으로 물러섭니다 — 장면과 같은 규칙입니다.
 *
 *     public/char/{id}/greet.webm   VP9 + Opus
 *     public/char/{id}/greet.mp4    H.264 + AAC (사파리)
 *     public/char/{id}/greet.jpg    첫 프레임
 */
function useGreet(id: string, on: boolean) {
  const [ok, setOk] = useState(false);
  useEffect(() => {
    if (!on) { setOk(false); return; }
    let alive = true;
    fetch(`/char/${id}/greet.webm`, { method: "HEAD" })
      .then((r) => { if (alive) setOk(r.ok); })
      .catch(() => {});
    return () => { alive = false; };
  }, [id, on]);
  return ok;
}


export default function CharArt({
  lens, size = "card", className, mood = "base", greet = false,
  soundOn = true, onSoundBlocked,
}: {
  lens: LensInfo;
  size?: Size;
  className?: string;
  /** 어떤 얼굴인가. 없으면 기본 얼굴로 내려옵니다. */
  mood?: Mood;
  /**
   * 처음 만나는 자리인가. 참이면 **소리까지 있는 인사**를 한 번 틉니다.
   * 파일이 없으면 도는 초상으로, 그것도 없으면 멈춘 그림으로 갑니다.
   */
  greet?: boolean;
  /**
   * 소리를 낼 것인가.
   *
   * ★ 스위치를 여기 두지 않는 까닭 — `.charart` 도 `.meetart` 도
   *   네 변을 **마스크로 녹입니다**. 초상이 네모로 잘려 보이면
   *   스티커가 되기 때문입니다. 그런데 마스크는 그 안의 것을 다
   *   녹여서, 귀퉁이에 단추를 얹으면 단추도 같이 사라집니다.
   *   그래서 스위치는 마스크 **밖**(Meet)에 두고 여기는 상태만
   *   받습니다.
   */
  soundOn?: boolean;
  /** 브라우저가 소리를 막았을 때. 화면이 켜는 자리를 내라는 뜻입니다. */
  onSoundBlocked?: () => void;
}) {
  const bust = useBust(lens.id, mood);
  const wantGreet = greet && mood === "base";
  const hello = useGreet(lens.id, wantGreet);
  const wantClip = !hello && size !== "chip" && size !== "talk" && mood === "base";
  const clip = useClip(lens.id, wantClip && !!bust);

  /* 동작 줄이기를 켠 사람에게는 멈춘 그림으로 냅니다 */
  const [still, setStill] = useState(false);
  useEffect(() => {
    setStill(window.matchMedia("(prefers-reduced-motion: reduce)").matches);
  }, []);
  const { w, h } = BOX[size];
  const dim = !lens.released;

  /*
   * ★ 관리자는 눌러서 제작 프롬프트를 봅니다.
   *
   *   장면은 눌러서 볼 수 있는데 **캐릭터는 못 봤습니다.** 그림을
   *   맡기려면 그 사람 앞에서 바로 프롬프트가 나와야지, 도구를 따로
   *   돌려 찾아야 하면 안 찾습니다.
   *
   *   손님에게는 아무 일도 안 일어납니다 — 누를 수 있다는 표도 안 냅니다.
   */
  const admin = useSession((st) => st.admin);
  const [open, setOpen] = useState(false);

  /*
   * ★ 소리는 **손님이 문을 열어 줘야** 납니다.
   *
   *   브라우저는 손님이 아직 아무것도 안 누른 문서에서 소리 나는
   *   자동 재생을 막습니다. 대문에서 버튼을 누르고 들어온 사람은
   *   그 누름이 문서에 남아 있어 그냥 납니다. 그런데 이 화면을
   *   직접 열거나 새로 고친 사람에게는 안 납니다.
   *
   *   막히면 **조용히 물러섭니다** — 소리를 끄고 그림만 틉니다.
   *   그리고 켜는 자리를 냅니다. 손님이 안 부른 소리를 억지로
   *   밀어 넣지 않고, 못 듣고 지나치게 두지도 않습니다.
   */
  const vref = useRef<HTMLVideoElement | null>(null);
  useEffect(() => {
    const v = vref.current;
    if (!v || !hello || still) return;
    if (!soundOn) { v.muted = true; v.play().catch(() => {}); return; }
    v.muted = false;
    // 켤 때는 처음부터 — 인사를 반쯤 듣게 두지 않습니다.
    v.currentTime = 0;
    v.play().catch(() => {
      // 브라우저가 막았소. 조용히 물러서고, 켜는 자리를 내라고 이릅니다.
      v.muted = true;
      v.play().catch(() => {});
      onSoundBlocked?.();
    });
    // onSoundBlocked 는 화면이 매번 새로 만드는 함수라 여기 넣지 않습니다 —
    // 넣으면 그릴 때마다 인사가 처음으로 되감깁니다.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [hello, still, soundOn]);

  return (
    <div
      className={`charart ${size} ${dim ? "off" : ""} ${className ?? ""}`}
      style={{ width: w, height: h, ["--cc" as string]: lens.color }}
      role={admin ? "button" : undefined}
      tabIndex={admin ? 0 : undefined}
      title={admin ? `${lens.name} — 눌러서 제작 프롬프트 보기` : undefined}
      onClick={admin ? (ev) => { ev.stopPropagation(); setOpen(true); } : undefined}
      onKeyDown={admin ? (ev) => {
        if (ev.key === "Enter" || ev.key === " ") {
          ev.preventDefault(); ev.stopPropagation(); setOpen(true);
        }
      } : undefined}
    >
      {admin && <span className="slot">프롬프트</span>}
      {open && (
        <PromptModal kind="char" id={lens.id} onClose={() => setOpen(false)} />
      )}
      {/*
        ★ 첫 인사는 **한 번만** 돕니다 (loop 없음). 되풀이되면 인사가
          아니라 태엽입니다. 끝나면 마지막 프레임에 멈춰 섭니다.
      */}
      {hello && !still ? (
        <video ref={vref} width={w} height={h}
               poster={`/char/${lens.id}/greet.jpg`}
               autoPlay playsInline preload="auto" aria-label={lens.name}>
          <source src={`/char/${lens.id}/greet.webm`} type="video/webm" />
          {/* 사파리 몫 — VP9 를 못 읽습니다 */}
          <source src={`/char/${lens.id}/greet.mp4`} type="video/mp4" />
        </video>
      ) : clip && !still ? (
        <video width={w} height={h} poster={bust ?? undefined}
               autoPlay muted playsInline loop aria-label={lens.name}>
          <source src={`/char/${lens.id}/clip.webm`} type="video/webm" />
          {/* mp4 는 투명이 없어 바탕색이 구워져 있습니다 */}
          <source src={`/char/${lens.id}/clip.mp4`} type="video/mp4" />
        </video>
      ) : bust ? (
        // eslint-disable-next-line @next/next/no-img-element
        <img src={bust} alt={lens.name} width={w} height={h} loading="lazy" />
      ) : (
        /* 자리표시 — 얼굴을 흉내내지 않습니다. 색과 한자 한 글자. */
        <span className="ph" aria-label={lens.name}>
          <i>{lens.hanja?.[0] ?? lens.name[0]}</i>
        </span>
      )}
    </div>
  );
}
