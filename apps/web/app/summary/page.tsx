"use client";

/**
 * @screen c7 c8
 * C · 읽다 — c7 분석지 · c8 공유
 *
 * 다 읽고 나서 한 장으로 받아보는 것. 그리고 그걸 내보내는 자리.
 *
 * ★ 단서(caveats)를 접어두지 않습니다. 숨기면 "맞히는 집" 이 됩니다.
 * ★ 공유 링크에 생년월일시·고을은 담기지 않습니다. 무엇이 담기는지
 *   보내는 사람에게 먼저 보여줍니다.
 */
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Shell from "@/components/Shell";
import Scene from "@/components/scene/Scene";
import { Narration, Say } from "@/components/Narration";
import SinsalFigure from "@/components/scene/SinsalFigure";
import { api, ApiError } from "@/lib/api";
import { useSession } from "@/lib/store";
import { useScreen } from "@/lib/track";
import type { Summary } from "@shared/chart";

const EL_WORD: Record<string, string> = {
  목: "나무", 화: "불", 토: "흙", 금: "쇠", 수: "물",
};

export default function SummaryPage() {
  useScreen("c7");
  const router = useRouter();
  const s = useSession();
  const [sm, setSm] = useState<Summary | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [share, setShare] = useState<{
    path: string; includes: string[]; excludes: string[]; expires_days: number;
  } | null>(null);
  const [busy, setBusy] = useState(false);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    if (!s.chartId) return;
    let alive = true;
    api
      .summary({
        chart_id: s.chartId, concern: s.concern, axis4: s.axis4,
        lens_id: s.cur, name: s.name,
      })
      .then((d) => { if (alive) setSm(d); })
      .catch((e) => {
        if (alive) setErr(e instanceof ApiError ? e.message : "분석지를 펴지 못했소.");
      });
    return () => { alive = false; };
  }, [s.chartId, s.concern, s.axis4, s.cur, s.name]);

  if (!s.chartId) {
    return (
      <Shell title="분석지">
        <Narration lines={["먼저 글자를 세워야 하오."]} />
        <button className="btn mt" onClick={() => router.push("/")}>글자를 세운다</button>
      </Shell>
    );
  }
  if (err) return <Shell title="분석지"><Say who="도령">{err}</Say></Shell>;
  if (!sm) return <Shell title="분석지"><Narration lines={["종이를 편다."]} /></Shell>;

  const shareUrl = share
    ? (typeof window !== "undefined" ? window.location.origin : "") + share.path
    : "";

  return (
    <Shell title="분석지" legal>
      <Scene id="scroll" className="hero" />

      {/* 표지 — 카드로 잘라 나가는 부분 */}
      <div className="card sumhead">
        <p className="sm">성신당 星辰堂</p>
        <p className="gz">{sm.day_gan} · {sm.ilgan_name}</p>
        <p className="hl">{sm.headline}</p>
        <div className="three">
          {sm.three_lines.map((l, i) => (
            <p key={i}><span className="n">{i + 1}</span>{l}</p>
          ))}
        </div>
        <p className="sm">
          {sm.strength} · 흐름 {sm.flow} · 없는 것 {EL_WORD[sm.weak_el]} ·
          필요한 것 {EL_WORD[sm.yongsin]}
        </p>
      </div>

      {/* 본문 */}
      {sm.sections.map((sec) => (
        <div className="blk in" key={sec.id}>
          <div className="lab">{sec.title}</div>
          <span className="src">근거 · {sec.source}</span>
          <div dangerouslySetInnerHTML={{ __html: sec.html }} />
        </div>
      ))}

      {/* 이름 붙은 자리 — 표가 아니라 곁에 선 사람으로 */}
      {sm.sinsal.length > 0 && (
        <div className="blk in">
          <div className="lab">곁에 선 이들</div>
          <p className="sm">
            옛사람들이 이 자리들을 어떤 모습으로 그렸는지 옮긴 것이오.
            무엇이 일어난다는 뜻이 아니오.
          </p>
          {sm.sinsal.map((x) => (
            <SinsalFigure key={x.key + x.at.join()} sinsalKey={x.key} at={x.at} />
          ))}
        </div>
      )}

      {/* ★ 단서 — 접지 않는다 */}
      <div className="caveat">
        <div className="lab">셈에서 흐린 부분</div>
        {sm.caveats.map((c) => <p className="sm" key={c}>· {c}</p>)}
      </div>

      {/* c8 · 공유 */}
      <div className="blk in">
        <div className="lab">내보내기</div>
        {!share ? (
          <>
            <p className="sm">
              링크를 만들면 <b>여덟 글자와 해석</b>이 담기오.
              <b> 생년월일시와 태어난 고을은 담기지 않소.</b>
            </p>
            <button className="btn mt" disabled={busy} onClick={async () => {
              setBusy(true);
              try {
                const r = await api.share({
                  chart_id: s.chartId!, concern: s.concern, axis4: s.axis4,
                  lens_id: s.cur, name: s.name, from_name: s.name,
                  reveal: "full",
                });
                setShare(r);
              } catch (e) {
                setErr(e instanceof ApiError ? e.message : "링크를 만들지 못했소.");
              } finally {
                setBusy(false);
              }
            }}>
              공유 링크 만들기
            </button>
          </>
        ) : (
          <>
            <div className="dz">
              <div className="k">링크</div>
              <p className="mono" style={{ wordBreak: "break-all" }}>{shareUrl}</p>
            </div>
            <button className="btn mt" onClick={() => {
              void navigator.clipboard?.writeText(shareUrl);
              setCopied(true);
            }}>
              {copied ? "베꼈소" : "링크 베끼기"}
            </button>
            <p className="sm mt">담기는 것 · {share.includes.join(" · ")}</p>
            <p className="sm">담기지 않는 것 · {share.excludes.join(" · ")}</p>
            <p className="sm">{share.expires_days}일이 지나면 링크가 스스로 닫히오.</p>
          </>
        )}
      </div>

      <button className="btn gh mt" onClick={() => router.push("/relay")}>
        이어서 다른 사람에게
      </button>
      <button className="btn gh" onClick={() => router.push("/lobby")}>진열대로</button>
    </Shell>
  );
}
