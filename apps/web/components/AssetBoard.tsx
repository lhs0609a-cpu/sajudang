"use client";

/**
 * 에셋 현황판 — 실물을 보여 주고, 없는 것을 붉게 찍고, 누르면 프롬프트.
 *
 * ★ 왜 이게 필요한가 (2026-09-03)
 *
 *   장면도 캐릭터도 신살 인물도 **파일이 있으면 그걸 쓰고 없으면
 *   자리표시로 버티는** 구조라, 없는 것이 화면에서 티가 안 납니다.
 *   좋은 설계인데 그 대가로 **무엇이 없는지 아무도 모릅니다.**
 *
 *   처음엔 「그림 없음 / 영상 없음」 글자만 찍었습니다. 손님이 말했습니다 —
 *   "각 이미지나 그런거 실황 보여줘야지. 그래야 내가 어떤 이미지가
 *   비어 있구나 확인하고, 클릭하면 명령어 떠서 제미나이랑 힉스필드로
 *   채워 넣지." 글자로는 안 됩니다. **지금 화면에 나가는 그대로**를
 *   여기 늘어놓습니다 — 화면이 쓰는 그 부품(Scene · CharArt ·
 *   SinsalFigure)을 그대로 불러서, 있으면 실물이 뜨고 없으면 자리표시가
 *   뜹니다. 보는 눈과 화면이 쓰는 판단이 언제나 같습니다.
 *
 * ★ 카드 하나가 하는 일 셋
 *     실물        지금 나가는 그림·영상 그대로
 *     없는 것     그림 없음 · 영상 없음 을 붉게
 *     누르면      제작 프롬프트 (제미나이 → 힉스필드 → 폴더)
 *   그리고 **그 장면이 나오는 화면으로 가는 길**을 답니다. 넣고 나서
 *   실제 자리에서 봐야 하기 때문입니다.
 *
 * ★ 신살 인물은 영상을 안 씁니다.
 *   글 옆에 서 있는 초상이라 스물여섯이 한꺼번에 움직이면 글을 못
 *   읽습니다. 그 칸은 「안 씀」 으로 둡니다.
 */
import { useEffect, useState } from "react";
import Link from "next/link";
import PromptModal from "@/components/scene/PromptModal";
import Scene from "@/components/scene/Scene";
import CharArt from "@/components/CharArt";
import SinsalFigure from "@/components/scene/SinsalFigure";
import { SCENES } from "@/components/scene/manifest";
import { LENSES } from "@/lib/lenses";
import { FIGURES } from "@/lib/sinsalFigures";

type Kind = "scene" | "char" | "figure";

/*
 * 장면이 나오는 화면 — 기계로는 못 뽑습니다. 한 장면이 여러 화면에
 * 나오기 때문입니다. tools/prompt_sheet.js 의 차례와 같게 적었습니다.
 * 리포트 안 장면은 명식이 있어야 열리니 진열대로 보냅니다.
 */
const WHERE: Record<string, { at: string; href: string }> = {
  gate:     { at: "a1 골목 — 맨 처음 보는 화면", href: "/" },
  desk:     { at: "a2 이름을 적다", href: "/" },
  ink:      { at: "a3 날·고을", href: "/" },
  room:     { at: "a4 때를 묻다", href: "/" },
  mirror:   { at: "a4b 성향 4글자", href: "/" },
  fork:     { at: "a5 걸리는 것", href: "/" },
  altar:    { at: "a6 글자가 서다", href: "/" },
  facing:   { at: "a7 도령이 말하다", href: "/" },
  hall:     { at: "b2 스무 사람", href: "/lobby?tab=b2" },
  seat:     { at: "b3 그 사람의 자리", href: "/lobby?tab=b3" },
  shelf:    { at: "b1 진열대", href: "/lobby?tab=b1" },
  scroll:   { at: "c1 두루마리 · c7 분석지", href: "/summary" },
  roadmap:  { at: "c2 대운 맵 (리포트)", href: "/lobby" },
  fold:     { at: "c3 접힌 데 (리포트)", href: "/lobby" },
  cardbg:   { at: "c4 패 뒷면 (리포트)", href: "/lobby" },
  wall:     { at: "c5 후기 벽 · m1", href: "/me" },
  oldpaper: { at: "c6 낡은 종이 · p1 값", href: "/pay" },
  coin:     { at: "p2 엽전", href: "/pay" },
  untie:    { at: "p3 매듭을 풀다", href: "/pay" },
  tray:     { at: "p4 소반", href: "/pay" },
  handle:   { at: "r1 손잡이", href: "/relay" },
  banner:   { at: "d1 현수막", href: "/daily" },
  tea:      { at: "d2 차 한 잔", href: "/daily" },
  sealbook: { at: "m2 인장첩", href: "/me" },
};

interface Row {
  kind: Kind;
  id: string;
  name: string;
  /** 그림 파일 후보 — 하나라도 있으면 그림이 있는 것 */
  img: string[];
  /** 영상 파일. 빈 배열이면 「안 씀」 */
  clip: string[];
  at: string;
  href: string;
}

function rows(): Row[] {
  const out: Row[] = [];
  for (const s of SCENES) {
    const w = WHERE[s.id] ?? { at: "", href: "/" };
    out.push({
      kind: "scene", id: s.id, name: s.name,
      img: [`/scene/${s.id}/poster.jpg`],
      clip: [`/scene/${s.id}/clip.webm`],
      at: w.at, href: w.href,
    });
  }
  for (const l of LENSES) {
    out.push({
      kind: "char", id: l.id, name: l.name,
      img: [`/char/${l.id}/bust.png`],
      clip: [`/char/${l.id}/clip.webm`],
      at: "b2 스무 사람 · b3 그 사람", href: "/lobby?tab=b2",
    });
  }
  for (const f of Object.values(FIGURES)) {
    out.push({
      kind: "figure", id: f.key, name: f.title,
      img: [`/sinsal/${f.key}/figure.png`, `/sinsal/${f.key}/poster.jpg`],
      clip: [],
      at: "c7 분석지 · 리포트 신살 컷", href: "/summary",
    });
  }
  return out;
}

/** 있는가, 그리고 **언제 만든 것인가**. 없으면 null. */
async function madeAt(url: string): Promise<number | null> {
  try {
    const r = await fetch(url, { method: "HEAD" });
    if (!r.ok) return null;
    const lm = r.headers.get("last-modified");
    return lm ? Date.parse(lm) : 0;
  } catch {
    return null;
  }
}

const LABEL: Record<Kind, string> = {
  scene: "장면", char: "캐릭터", figure: "신살 인물",
};

const lensOf = (id: string) => LENSES.find((l) => l.id === id);

/** 실물 — 화면이 쓰는 그 부품을 그대로 부릅니다. */
function Art({ r }: { r: Row }) {
  if (r.kind === "scene") return <Scene id={r.id} />;
  if (r.kind === "char") {
    const l = lensOf(r.id);
    return l ? <CharArt lens={l} size="card" /> : null;
  }
  return <SinsalFigure sinsalKey={r.id} size={120} />;
}

export default function AssetBoard() {
  const all = rows();
  const [have, setHave] = useState<Record<string, [boolean, boolean]>>({});
  /*
   * ★ 그림이 있어도 **낡았을 수 있습니다** (2026-09-03).
   *
   *   초상 프롬프트를 정면으로 고쳤는데, 이미 뽑아 둔 도령 그림은
   *   비스듬한 채였습니다. 판은 「그림 있음」 이라 초록불을 켰고,
   *   그래서 다 된 줄 알았습니다. 파일이 프롬프트보다 오래면 그렇게
   *   말해야 합니다 — 판이 거짓말을 하면 안 봅니다.
   */
  const [revised, setRevised] = useState<Record<string, number>>({});
  const [stale, setStale] = useState<Record<string, boolean>>({});
  /*
   * ★ 영상도 낡습니다 (2026-09-04).
   *
   *   초상을 정면으로 바꾸고 나니 그림은 새로 뽑는데 **영상은 그대로**
   *   비스듬한 채였습니다. 대사 옆 작은 얼굴은 그림(bust.png)을 쓰지만,
   *   첫 대면·진열대·릴레이의 **큰 초상은 영상을 씁니다**(CharArt).
   *   그림만 갈아 끼우면 큰 얼굴만 계속 옆을 봅니다.
   */
  const [staleClip, setStaleClip] = useState<Record<string, boolean>>({});
  const [busy, setBusy] = useState(true);
  const [open, setOpen] = useState<{ kind: Kind; id: string } | null>(null);
  const [onlyMissing, setOnlyMissing] = useState(false);

  /* 프롬프트를 언제 고쳤는가 — 묶음이 자리마다 적어 둡니다. */
  useEffect(() => {
    let alive = true;
    fetch("/asset-prompts.json")
      .then((r) => r.json())
      .then((d) => {
        if (!alive) return;
        const at: Record<string, number> = {};
        for (const grp of ["scenes", "chars", "figures"] as const) {
          for (const [k, v] of Object.entries(d[grp] ?? {})) {
            const rev = (v as { revised?: string }).revised;
            if (rev) at[k] = Date.parse(rev);
          }
        }
        setRevised(at);
      })
      .catch(() => {});
    return () => { alive = false; };
  }, []);

  useEffect(() => {
    let alive = true;
    (async () => {
      const got: Record<string, [boolean, boolean]> = {};
      const old: Record<string, boolean> = {};
      const oldClip: Record<string, boolean> = {};
      for (const r of all) {
        const times = await Promise.all(r.img.map(madeAt));
        const made = times.filter((t): t is number => t !== null);
        const img = made.length > 0;
        const clipAt = r.clip.length
          ? (await Promise.all(r.clip.map(madeAt)))
              .filter((t): t is number => t !== null)
          : [];
        const clip = r.clip.length ? clipAt.length > 0 : true;
        got[r.kind + ":" + r.id] = [img, clip];
        // 프롬프트를 고친 날보다 오래면 낡은 것입니다 — 그림도 영상도.
        const rev = revised[r.id];
        if (rev) {
          if (img && made.every((t) => t > 0 && t < rev)) old[r.id] = true;
          if (clipAt.length && clipAt.every((t) => t > 0 && t < rev)) {
            oldClip[r.id] = true;
          }
        }
        if (!alive) return;
        setHave({ ...got });
        setStale({ ...old });
        setStaleClip({ ...oldClip });
      }
      if (alive) setBusy(false);
    })();
    return () => { alive = false; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [revised]);

  const kinds: Kind[] = ["scene", "char", "figure"];
  const tally = (k: Kind, which: 0 | 1) => {
    const rs = all.filter((r) => r.kind === k);
    const done = rs.filter((r) => have[k + ":" + r.id]?.[which]).length;
    return `${done}/${rs.length}`;
  };
  const missing = (r: Row) => {
    const st = have[r.kind + ":" + r.id];
    // 낡은 것도 채워야 할 자리입니다 — 「없는 것만」 에 같이 걸립니다.
    return !st || !st[0] || !st[1] || !!stale[r.id] || !!staleClip[r.id];
  };

  return (
    <section className="assetboard">
      <h2>에셋 — 지금 나가는 그대로</h2>
      <p className="sm">
        파일이 있으면 화면이 자동으로 그걸 쓰오. 없으면 자리표시가 나가오.
        여기 보이는 것이 손님이 보는 것과 같소.
        {busy && " 세는 중이오…"}
      </p>

      <div className="abtot">
        {kinds.map((k) => (
          <div key={k} className="abcard">
            <b>{LABEL[k]}</b>
            <span>그림 {tally(k, 0)}</span>
            <span>
              {k === "figure" ? "영상 안 씀" : `영상 ${tally(k, 1)}`}
            </span>
          </div>
        ))}
        <label className="abonly">
          <input type="checkbox" checked={onlyMissing}
                 onChange={(e) => setOnlyMissing(e.target.checked)} />
          없는 것만
        </label>
      </div>

      {kinds.map((k) => {
        const list = all.filter((r) => r.kind === k)
                        .filter((r) => !onlyMissing || missing(r));
        if (!list.length) return null;
        return (
          <div key={k}>
            <div className="lab2">{LABEL[k]}</div>
            <div className={"abgrid " + k}>
              {list.map((r) => {
                const st = have[k + ":" + r.id];
                const img = st?.[0];
                const clip = st?.[1];
                return (
                  <div key={r.id} className={"abtile" + (missing(r) ? " lack" : "")}>
                    {/*
                      ★ 실물을 누르면 **이 판의 프롬프트 창**이 뜹니다.
                        부품마다 제 창을 여는 손잡이가 있는데(관리자 모드),
                        둘 다 열리면 창이 두 겹이라 여기서 붙잡습니다.
                    */}
                    <div className="abart"
                         role="button" tabIndex={0}
                         title="눌러서 제작 프롬프트 보기"
                         onClickCapture={(ev) => {
                           ev.stopPropagation();
                           setOpen({ kind: r.kind, id: r.id });
                         }}
                         onKeyDown={(ev) => {
                           if (ev.key === "Enter" || ev.key === " ") {
                             ev.preventDefault();
                             setOpen({ kind: r.kind, id: r.id });
                           }
                         }}>
                      <Art r={r} />
                    </div>
                    <div className="abmeta">
                      <div className="abhead">
                        <b>{r.name}</b>
                        <span className="abid">{r.id}</span>
                      </div>
                      <div className="abdots">
                        <span className={"abdot"
                                         + (stale[r.id] ? " old"
                                            : img ? " on" : "")}>
                          {stale[r.id] ? "프롬프트 바뀜"
                           : img ? "그림" : "그림 없음"}
                        </span>
                        <span className={"abdot" + (r.clip.length === 0
                                                    ? " na"
                                                    : staleClip[r.id] ? " old"
                                                    : clip ? " on" : "")}>
                          {r.clip.length === 0
                            ? "영상 안 씀"
                            : staleClip[r.id] ? "영상 낡음"
                            : clip ? "영상" : "영상 없음"}
                        </span>
                      </div>
                      <div className="abwhere">
                        <Link href={r.href}>{r.at || "화면으로"} →</Link>
                      </div>
                      <button className="abbtn"
                              onClick={() => setOpen({ kind: r.kind, id: r.id })}>
                        프롬프트
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        );
      })}

      {open && (
        <PromptModal kind={open.kind} id={open.id}
                     onClose={() => setOpen(null)} />
      )}
    </section>
  );
}
