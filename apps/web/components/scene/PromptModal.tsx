"use client";

/**
 * 에셋 프롬프트 모달 — 장면·신살 인물을 클릭하면 뜬다.
 *
 * 참조 구현체의 showScn() 을 옮긴 것입니다. 프롬프트 원문은
 * reference/sajudang.html 에서 그대로 뽑아 public/asset-prompts.json 에
 * 넣었습니다. 손으로 옮기면 어긋나므로 추출해서 씁니다.
 *
 * 제작 순서 (docs/10 §1)
 *   ① 제미나이로 시작 이미지 1장
 *   ② 힉스필드 업로드 → 모션 프롬프트 + 프리셋
 *   ③ webm(VP9) + mp4(H.264) + poster.jpg
 *   ④ /scene/{id}/ 또는 /sinsal/{key}/ 에 배치
 *
 * ★ 영상 앵커(ANIMBASE)가 빠지면 3초 안에 얼굴이 사진처럼 변합니다.
 *   모션 프롬프트에 이미 붙어 있으니 통째로 복사하세요.
 */
import { useEffect, useState } from "react";
import { seasonOf, useSession } from "@/lib/store";

const SEASON_KO: Record<string, string> = {
  spring: "봄 · 벚꽃", summer: "여름 · 능소화",
  autumn: "가을 · 국화", winter: "겨울 · 매화",
};

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
}

interface Bundle {
  ANIMBASE: string;
  TINT: string;
  PIPE: string;
  scenes: Record<string, PromptEntry>;
  figures: Record<string, PromptEntry>;
}

let cache: Bundle | null = null;

async function load(): Promise<Bundle> {
  if (cache) return cache;
  const res = await fetch("/asset-prompts.json");
  cache = (await res.json()) as Bundle;
  return cache;
}

const PRESET_COLOR: Record<string, string> = {
  "Dolly In": "var(--gold)",
  "Dolly Right": "var(--gold)",
  Static: "var(--teal)",
};

function Block({ n, label, text, dir }: {
  n: string; label: string; text: string; dir?: string;
}) {
  const [copied, setCopied] = useState(false);
  return (
    <>
      <div className="pl">
        <span>{n} {label}</span>
        <button onClick={() => {
          void navigator.clipboard?.writeText(text);
          setCopied(true);
          setTimeout(() => setCopied(false), 1600);
        }}>
          {copied ? "베꼈소" : "복사"}
        </button>
      </div>
      {dir && <div className="pdir">{dir}</div>}
      <pre>{text}</pre>
    </>
  );
}

export default function PromptModal({
  kind, id, onClose,
}: {
  kind: "scene" | "figure";
  id: string;
  onClose: () => void;
}) {
  const [data, setData] = useState<Bundle | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const override = useSession((st) => st.seasonOverride);
  const season = override ?? seasonOf();

  useEffect(() => {
    let alive = true;
    load()
      .then((d) => { if (alive) setData(d); })
      .catch(() => { if (alive) setErr("프롬프트를 불러오지 못했소."); });
    return () => { alive = false; };
  }, []);

  useEffect(() => {
    const esc = (e: KeyboardEvent) => { if (e.key === "Escape") onClose(); };
    window.addEventListener("keydown", esc);
    document.body.style.overflow = "hidden";
    return () => {
      window.removeEventListener("keydown", esc);
      document.body.style.overflow = "";
    };
  }, [onClose]);

  const e = data
    ? (kind === "scene" ? data.scenes[id] : data.figures[id])
    : null;

  /*
   * 계절을 타는 장면은 지금 보고 있는 계절의 프롬프트와 폴더를 보여 줍니다.
   * 한 벌만 보여 주면 넉 장을 만들어야 하는 줄 모르고 한 장만 만들게 됩니다.
   */
  const seasonal = kind === "scene" && !!e?.seasonal;
  const image = seasonal ? (e?.seasons?.[season] ?? e?.image) : e?.image;
  const dir = kind === "scene"
    ? (seasonal ? `/scene/${id}/${season}/` : `/scene/${id}/`)
    : `/sinsal/${id}/`;

  return (
    <div className="pmod on" onClick={onClose}>
      <div className="pmodin" onClick={(ev) => ev.stopPropagation()}>
        <button className="x" onClick={onClose}>닫기 ✕</button>

        {err && <p className="sm">{err}</p>}
        {!data && !err && <p className="sm">프롬프트를 펴는 중이오…</p>}

        {e && (
          <>
            <h3>{e.title}</h3>
            <div className="m1">
              {dir} · 힉스필드 단일 파이프라인
              {e.who ? " · " + e.who : ""}
            </div>

            <div className="sp">
              <span style={{ color: PRESET_COLOR[e.preset] ?? "var(--teal)",
                             borderColor: "currentColor" }}>
                {e.preset}
              </span>
              <span>{e.ratio}</span>
              <span>{e.duration}</span>
              {e.loop && <span style={{ color: "var(--teal)" }}>seamless loop</span>}
              {e.tint && <span style={{ color: "var(--lav)" }}>무채색 · 앱에서 착색</span>}
              {e.still && <span style={{ color: "var(--rose)" }}>PNG 병행</span>}
            </div>

            <div className="hint" style={{ borderColor: "var(--teal)" }}>
              <b>제작 순서</b><br />
              ① 제미나이로 시작 이미지 1장<br />
              ② 힉스필드 업로드 → 아래 ② 프롬프트 + 프리셋 <b>{e.preset}</b><br />
              ③ webm(VP9) + mp4(H.264) + poster.jpg<br />
              ④ <b>{dir}</b> 에 배치하면 코드 수정 없이 교체되오
            </div>

            {seasonal && (
              <div className="hint" style={{ borderColor: "var(--rose)" }}>
                <b>계절 넉 장이 필요하오.</b><br />
                꽃이 계절마다 다릅니다 — 벚꽃 · 능소화 · 국화 · 매화.
                착색으로는 꽃 모양을 못 바꾸니 그림 자체가 넉 장이어야 합니다.<br />
                지금 보이는 것은 <b>{SEASON_KO[season] ?? season}</b> 것이오.
                레일에서 계절을 바꾸면 나머지가 나옵니다.
              </div>
            )}
            {image && (
              <Block
                n="①"
                label={seasonal
                  ? `시작 이미지 · 제미나이 · ${SEASON_KO[season] ?? season}`
                  : "시작 이미지 · 제미나이"}
                text={image} />
            )}
            {e.motion && (
              <Block n="②" label="모션 · 힉스필드" text={e.motion}
                     dir="영상 앵커가 붙어 있소. 통째로 복사하시오 — 빼면 3초 안에 얼굴이 사진처럼 변하오." />
            )}
            {e.tint && data && (
              <Block n="③" label="착색 · CSS" text={data.TINT} />
            )}

            {e.note && (
              <div className="hint"
                   dangerouslySetInnerHTML={{ __html: e.note }} />
            )}
            {e.hint && (
              <div className="hint" style={{ borderColor: "var(--gold)" }}
                   dangerouslySetInnerHTML={{ __html: e.hint }} />
            )}
          </>
        )}
      </div>
    </div>
  );
}
