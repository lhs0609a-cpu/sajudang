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
import ActOut from "@/components/ActOut";
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
        <Say who="도령" lens="pungun">{err}</Say>
        <button className="btn mt" onClick={() => router.push("/")}>
          나도 내 운명을 확인해 보겠습니다
        </button>
      </Shell>
    );
  }
  if (!d) {
    return <Shell title="건너오다"><Narration lines={["대문을 여는 중이오."]} /></Shell>;
  }

  const who = d.from_name || d.name;

  return (
    /*
     * ★ 이 화면은 **한 번도 점수를 안 받고 있었습니다.**
     *
     *   `@screen s1 s2` 라 적혀 있어 화면 지도(screen_graph)는 32개를
     *   다 세는데, 연출 자(screenscan)는 `<Shell screen="…">` 선언을
     *   보고 잘라 냅니다. 여기에 그 선언이 없었고, 이 파일이 스캔
     *   목록(PAGES)에도 없었습니다. 그래서 스물일곱만 재고 있었습니다.
     *
     *   하필 여기는 **남이 보낸 링크로 처음 들어오는 자리**입니다
     *   (docs/15). 이 집을 처음 보는 사람이 가장 많이 서는 화면이
     *   점수 밖에 있었습니다.
     */
    <Shell screen="s1" title="건너오다" legal>
      <Scene id="gate" className="hero" />

      {/* ① 누가 보냈는가 */}
      {/*
        ★ 여기가 스물여덟 중 **꼴찌(45)** 였습니다. 그리고 하필
          이 집을 **처음 보는 사람**이 서는 자리입니다.

          여는 줄이 「보내셨소」로 시작해 콜드 오픈이 아니었고,
          받은 사람 얘기가 한 줄도 없었습니다. 남의 사주를 대신
          읽어 주는 화면이라 더 그랬습니다 — 이 종이의 주인은
          여기 없고, 보는 사람은 구경꾼이 됩니다.

          ★ 파는 말은 안 얹습니다. 유입 화면입니다 (docs/15) —
            적중률·과학·통계 같은 말은 이 집이 금지한 것입니다.
            적는 건 **이 화면이 이미 아는 것**뿐입니다.
      */}
      <Narration
        lines={
          who
            ? [`${who}님이 이 종이를 보내 왔다.`,
               "광고가 아니라, 아는 사람이 건넨 것이다."]
            : ["누가 보냈는지는 적혀 있지 않다.",
               "받은 종이만 여기 있다."]
        }
      />
      <Say who="도령" lens="pungun">
        여기 적힌 8글자는 그대 것이 아니오. 기둥 4자리를 옮긴
        남의 글자요.
        <br />
        그런데도 끝까지 내려 보게 되오. <b>남의 것을 보면서 제
        것을 견주기 때문</b>이오. 여기까지 오는 동안 벌써 한 번은
        「나는 어떤가」 하셨소.
          <br /> 그러고도 묻기는 미뤄 두셨을 것이오 —
        이런 걸 믿느냐 소리를 들을까 참은 적이 있어서요.
        <br />
        이 집은 맞힌다고 하지 않소. <b>무엇을 보고 한 말인지</b>를
        칸마다 적어 둘 뿐이오. 흐린 데는 흐리다고 아래에 적어
        두었으니, 대 보고 아니다 싶으면 닫으시오.
          <br /> 남이 건넨
        종이는 대문 앞에 놓인 편지처럼, 뜯어 보고 그냥 두고 가도
        되오. 여태 그런 편지를 몇 번 받아 보셨을 것이오.
      </Say>
      <span className="src">
        근거 · 기둥 4자리에서 옮긴 8글자로 셈한 것이오 ·
        생년월일시와 태어난 고을은 이 고리에 안 담기오 ·
        고리는 90일이 지나면 스스로 닫히오
      </span>

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
        생년월일과 태어난 고을은 이 링크에 담기지 않았소.
        {who ? ` ${who}님이 무엇이 담기는지 보고 보내신 것이오.` : ""}
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
            잘 맞는 부분만 골라 보여드리지 않소.
            흐린 데는 흐리다고 적소.
          </p>
        </div>
      )}

      {/* ④ 그제야 권한다 */}
      <div className="blk in">
        <Say who="도령" lens="pungun">
          {who ? `${who}님 것은 여기까지요.` : "받으신 것은 여기까지요."}
          <br />그대 여덟 글자도 세워보시겠소? 값은 아직 묻지 않소.
        </Say>
        {/*
          ★ 막이 그냥 끝나고 있었습니다. 남의 종이를 다 보고 나서
            버튼 둘이 나올 뿐이라, 「나도 해볼까」가 손님 머릿속에서
            혼자 서야 했습니다. 재촉이 아니라 **무엇이 다른지**를
            한 줄로 말합니다 — 여기 있는 건 남의 글자입니다.
        */}
        <ActOut kind="남긴 물음" next="골목">
          여기 있는 8글자는 끝까지 남의 것이오. 남의 옷을 걸쳐 본
          것처럼, 품이 맞는지는 알아도 제 치수는 모르오.
          <br />
          <b>그대 것은 아직 한 글자도 안 섰소.</b>
        </ActOut>
        {/*
          ★ 열린 횟수가 **버튼 아래**에 있었습니다. 그건 고를 때
            보라고 있는 수인데, 다 고르고 난 자리에 놓여 있었습니다.
            누르기 전에 보이게 위로 올립니다.
        */}
        <p className="sm" style={{ textAlign: "center", color: "var(--paper3)" }}>
          이 종이는 {d.views}번 열렸소.
        </p>
        <button className="btn mt" onClick={() => router.push("/")}>
          내 여덟 글자를 세우겠습니다
        </button>
        <button className="btn gh" onClick={() => router.push("/lobby")}>
          어떤 사람들이 있는지부터 보겠습니다
        </button>
      </div>
    </Shell>
  );
}
