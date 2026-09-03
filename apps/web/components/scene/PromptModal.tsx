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
  /* 스무 사람의 초상. tools/char_sheet.py --json 이 넣습니다. */
  chars?: Record<string, PromptEntry>;
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
  kind: "scene" | "figure" | "char";
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
    ? (kind === "scene" ? data.scenes[id]
       : kind === "char" ? (data.chars ?? {})[id]
       : data.figures[id])
    : null;

  /*
   * 계절을 타는 장면(대문)이라도 **만드는 것은 한 장**입니다.
   * 그래서 폴더는 기본 폴더를 알려 줍니다. 계절 폴더는 나중에 계절판을
   * 넣고 싶어졌을 때만 쓰는 자리이고, 넣으면 앱이 그걸 먼저 씁니다.
   * 지금 보고 있는 계절의 그림을 보여 주니 레일에서 계절을 바꿔 가며
   * 마음에 드는 한 장을 고르면 됩니다.
   */
  const seasonal = kind === "scene" && !!e?.seasonal;
  const image = seasonal ? (e?.seasons?.[season] ?? e?.image) : e?.image;
  const dir = kind === "scene" ? `/scene/${id}/`
            : kind === "char" ? `/char/${id}/`
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
              {/*
                ★ 시키는 비율은 `ratio` 가 아니라 `spec[0]` 입니다.

                  `ratio` 는 2026-09-01 부터 **보여 주는 상자**입니다
                  (manifest.SceneSpec.box 주석). 장면 원본은 전부 9:16
                  인데 여기서 상자를 찍는 바람에, 이 창은 hall 을 보면서
                  「16:9」 라고 시키고 있었습니다. 발주서가 틀린 비율을
                  가리키면 그린 사람이 그 비율로 그립니다 — 시트(
                  tools/prompt_sheet.js)는 이미 고쳤는데 창만 남았습니다.
              */}
              <span>{e.spec?.[0] ?? e.ratio}</span>
              <span>{e.duration}</span>
              {e.loop && <span style={{ color: "var(--teal)" }}>seamless loop</span>}
              {e.tint && <span style={{ color: "var(--lav)" }}>무채색 · 앱에서 착색</span>}
              {e.still && <span style={{ color: "var(--rose)" }}>PNG 병행</span>}
            </div>

            <div className="hint" style={{ borderColor: "var(--teal)" }}>
              <b>제작 순서</b><br />
              {kind === "figure" ? (
                <>
                  ① 제미나이로 그림 1장 (3:4 세로)<br />
                  ② <b>{dir}</b> 에 <code>figure.png</code> 로 넣으면 코드
                  수정 없이 교체되오<br />
                  <span style={{ opacity: .7 }}>
                    인물은 움직이지 않소 — 글 옆에 서 있는 초상이라
                    스물여섯이 한꺼번에 움직이면 글을 못 읽소.
                  </span>
                </>
              ) : (
                <>
                  ① 제미나이로 시작 이미지 1장<br />
                  ② 힉스필드 업로드 → 아래 ② 프롬프트 + 프리셋 <b>{e.preset}</b><br />
                  ③ webm(VP9) + mp4(H.264) + poster.jpg<br />
                  ④ <b>{dir}</b> 에 배치하면 코드 수정 없이 교체되오
                </>
              )}
            </div>

            {seasonal && (
              <div className="hint" style={{ borderColor: "var(--teal)" }}>
                <b>한 장이면 되오.</b> 이 그림이 사계절 내내 나옵니다.<br />
                지금 보이는 것은 <b>{SEASON_KO[season] ?? season}</b> 이고,
                레일에서 계절을 바꾸면 다른 꽃으로 갈아 보실 수 있소.
                마음에 드는 걸로 한 장만 뽑으시오.<br />
                <span style={{ opacity: 0.7 }}>
                  나중에 계절마다 다르게 하고 싶어지면
                  <code> /scene/{id}/{"{계절}"}/ </code>
                  에 넣기만 하면 그때부터 그게 우선하오.
                </span>
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
            {/*
              ★ 신살 인물은 **그림 한 장**이면 됩니다 (2026-09-03).

                장면은 배경이라 움직여야 화면이 삽니다. 그런데 신살
                인물은 글 옆에 서 있는 초상이라, 스물여섯 자리에서
                동시에 움직이면 글을 읽을 수가 없습니다. 손님이
                「애니메이션은 필요 없다」 고 못박았습니다.

                프롬프트를 지우지는 않습니다 — 나중에 쓸 수 있게 묶음에
                그대로 두고, **주문서에서만 감춥니다.**
            */}
            {e.motion && kind !== "figure" && (
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
