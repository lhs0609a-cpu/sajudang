"use client";

/**
 * @screen s1 s2
 * S · 건너오다 — s1 받은 분석지 · s2 의심 풀기
 *
 * 링크를 받고 처음 들어온 사람이 보는 화면.
 * 이 사람은 우리를 모르고, 사주를 안 믿을 수도 있습니다.
 *
 * 순서를 지킵니다.
 *   ① 누가 보냈는지 먼저 밝힌다 (광고가 아니라 친구가 보낸 것)
 *   ② 친구의 것을 보여준다 (자랑이 아니라 근거가 붙은 글)
 *   ③ **의심을 먼저 꺼낸다** — 우리가 먼저 말한다
 *   ④ 그제야 권한다. 값은 묻지 않는다.
 *
 * ★ 이 화면에서 적중률·통계·과학 같은 말을 쓰지 않습니다.
 *   의심을 이기려고 거짓을 보태면 그 자리에서 끝납니다.
 */
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Shell from "@/components/Shell";
import { useScreen } from "@/lib/track";
import Scene from "@/components/scene/Scene";
import { Narration, Say } from "@/components/Narration";
import SinsalFigure from "@/components/scene/SinsalFigure";
import Doubts from "@/components/Doubts";
import { api, ApiError } from "@/lib/api";
import type { Shared } from "@shared/chart";

const EL_WORD: Record<string, string> = {
  목: "나무", 화: "불", 토: "흙", 금: "쇠", 수: "물",
};

export default function SharedView({ token }: { token: string }) {
  useScreen("s1");
  const router = useRouter();

  const [d, setD] = useState<Shared | null>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    let alive = true;
    api
      .openShare(token)
      .then((r) => {
        if (!alive) return;
        setD(r);
        void api.countShareOpen(token).catch(() => {});
      })
      .catch((e) => {
        if (alive) setErr(e instanceof ApiError ? e.message : "링크를 열지 못했소.");
      });
    return () => { alive = false; };
  }, [token]);

  if (err) {
    return (
      <Shell title="건너오다" legal>
        <Scene id="gate" className="hero" />
        <Say who="도령">{err}</Say>
        <button className="btn mt" onClick={() => router.push("/")}>
          나도 내 운명을 확인해 본다
        </button>
      </Shell>
    );
  }
  if (!d) {
    return <Shell title="건너오다"><Narration lines={["대문을 여는 중이오."]} /></Shell>;
  }

  const who = d.from_name || d.name;

  return (
    <Shell title="건너오다" legal>
      <Scene id="gate" className="hero" />

      {/* ① 누가 보냈는가 */}
      <Narration
        lines={
          who
            ? [`${who}님이 이 종이를 보내셨소.`, "광고가 아니라, 아는 사람이 건넨 것이오."]
            : ["누가 보냈는지는 적히지 않았소.", "받으신 종이만 여기 있소."]
        }
      />

      {/* ② 친구의 것 */}
      <div className="card sumhead">
        <p className="sm">{who ? `${who}님의 여덟 글자` : "받으신 여덟 글자"}</p>
        <p className="gz">{d.day_gan} · {d.ilgan_name}</p>
        <p className="hl">{d.headline}</p>
        <div className="three">
          {d.three_lines.map((l, i) => (
            <p key={i}><span className="n">{i + 1}</span>{l}</p>
          ))}
        </div>
        {d.pillars && (
          <div className="pillars sm">
            {d.pillars.map((p) => (
              <div className="p" key={p.label}>
                <span className="lb">{p.label}</span><b>{p.gz}</b>
              </div>
            ))}
            {d.hour_known === false && (
              <div className="p locked"><span className="lb">시주</span><b>◇◇</b></div>
            )}
          </div>
        )}
        <p className="sm">
          {d.strength} · 흐름 {d.flow} · 없는 것 {EL_WORD[d.weak_el]}
        </p>
      </div>

      {/* 친구 곁에 선 이들 — 길신부터 보여준다 */}
      {d.sinsal && d.sinsal.length > 0 && (
        <div className="blk in">
          <div className="lab">{who ? who + "님 곁에 선 이들" : "곁에 선 이들"}</div>
          {[...d.sinsal]
            .sort((a, b) => (a.kind === "길신" ? -1 : 1) - (b.kind === "길신" ? -1 : 1))
            .map((x) => (
              <SinsalFigure key={x.key + x.at.join()} sinsalKey={x.key}
                            at={x.at} size={120} />
            ))}
        </div>
      )}

      <p className="sm">
        생년월일과 태어난 고을은 이 링크에 담기지 않았소.
        {who ? ` ${who}님이 무엇이 담기는지 보고 보내신 것이오.` : ""}
      </p>

      {/* ③ ★ 의심 풀기 — 우리가 먼저 꺼낸다.
          문장은 components/Doubts.tsx 에 한 벌만 둡니다. 전에는 이 화면
          안에 갇혀 있어서, 직접 들어온 사람은 한 번도 못 봤습니다. */}
      <Doubts first={0} />

      {/* 친구가 받은 단서까지 같이 보여준다 */}
      {d.caveats?.length > 0 && (
        <div className="caveat">
          <div className="lab">이 글이 스스로 밝힌 흐린 부분</div>
          {d.caveats.map((c) => <p className="sm" key={c}>· {c}</p>)}
          <p className="sm" style={{ color: "var(--paper3)" }}>
            잘 맞는 부분만 골라 보여드리지 않소. 흐린 데는 흐리다고 적소.
          </p>
        </div>
      )}

      {/* ④ 그제야 권한다 */}
      <div className="blk in">
        <Say who="도령">
          {who ? `${who}님 것은 여기까지요.` : "받으신 것은 여기까지요."}
          <br />그대 여덟 글자도 세워보시겠소? 값은 아직 묻지 않소.
        </Say>
        <button className="btn mt" onClick={() => router.push("/")}>
          내 여덟 글자를 세운다
        </button>
        <button className="btn gh" onClick={() => router.push("/lobby")}>
          어떤 사람들이 있는지부터 본다
        </button>
        <p className="sm mt" style={{ textAlign: "center", color: "var(--paper3)" }}>
          이 종이는 {d.views}번 열렸소
        </p>
      </div>
    </Shell>
  );
}
