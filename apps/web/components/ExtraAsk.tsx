"use client";

/**
 * 이 캐릭터가 따로 받는 것 — 추가 입력.
 *
 * ★ 여기가 통째로 없었습니다.
 *   서버는 `needs_input` 으로 무엇이 필요한지 말하고 `/v1/report/choices`
 *   로 고를 것까지 내려보내는데, **화면이 그 둘을 하나도 안 썼습니다.**
 *   그래서 그 컷이 조용히 사라졌습니다 — 재보니 **51.3%** 입니다.
 *   값을 치른 사람도 잃습니다. 무엇을 잃는지도 모른 채로.
 *
 * ★ 저장하지 않습니다.
 *   여기서 받은 것은 리포트 요청에 실어 보내고 그걸로 끝입니다.
 *   특히 상대 사주는 **제3자의 생년월일**이라 본인 동의가 없습니다.
 *   계산하고 버립니다. (engine/extras.py · docs/11)
 *
 * ★ 얼굴 사진은 여기 없습니다. 생체인식정보라 받지 않습니다.
 */
import { useEffect, useState } from "react";
import { api } from "@/lib/api";

type Choice = { id: string; label: string };
type Choices = {
  situation: Choice[];
  stance: Choice[];
  blood: string[];
  image: Choice[];
  card: Choice[];
};

const TITLE: Record<string, string> = {
  blood: "피를 물으오",
  image: "눈에 걸리는 그림 하나",
  cards: "패 셋을 고르시오",
  context: "지금 어떤 자리에 계시오?",
  partner: "상대의 날을 아시오?",
};

const WHY: Record<string, string> = {
  blood: "피는 셈에 안 들어가오. 이 사람이 그걸로 한 겹 더 볼 뿐이오.",
  image: "고른 그림이 여덟 글자와 어긋나는 데를 봅니다.",
  cards: "셋을 뽑은 순서까지 봅니다.",
  context: "지금 자리를 알아야 같은 글자도 다르게 읽히오.",
  partner: "상대의 여덟 글자와 맞대 봅니다. 적으신 것은 남기지 않소.",
};

export default function ExtraAsk({
  need, onSubmit, busy,
}: {
  need: string;
  onSubmit: (extras: Record<string, unknown>) => void;
  busy?: boolean;
}) {
  const [ch, setCh] = useState<Choices | null>(null);
  const [pick, setPick] = useState<string | null>(null);
  const [picks, setPicks] = useState<string[]>([]);
  const [stance, setStance] = useState<string | null>(null);
  const [months, setMonths] = useState("");
  const [p, setP] = useState({ year: "", month: "", day: "", sex: "F" });

  const [chErr, setChErr] = useState(false);
  const [tryAt, setTryAt] = useState(0);

  useEffect(() => {
    let alive = true;
    setChErr(false);
    api.reportChoices()
      .then((c) => alive && setCh(c as Choices))
      /*
       * ★ 여기서 실패를 통째로 삼키고 있었습니다 — `.catch(() => {})`.
       *   고를 것을 못 받으면 `ch` 가 영영 null 이라 손님은
       *   「고를 것을 펴는 중이오…」 를 **끝없이** 봅니다. 오류도
       *   없고 다시 할 길도 없습니다. 값을 치른 사람일 수 있습니다.
       */
      .catch(() => alive && setChErr(true));
    return () => { alive = false; };
  }, [tryAt]);

  if (chErr && !ch) {
    return (
      <div className="ask blk">
        <p className="sm">고를 것을 못 펴겠소. 이 자리 하나만 접히오.</p>
        <button className="btn gh mt" onClick={() => setTryAt((n) => n + 1)}>
          다시 펴 보겠습니다
        </button>
      </div>
    );
  }
  if (!ch) return <p className="sm">고를 것을 펴는 중이오…</p>;

  const togglePick = (id: string) =>
    setPicks((v) => v.includes(id) ? v.filter((x) => x !== id)
                                   : v.length >= 3 ? v : [...v, id]);

  let body: React.ReactNode = null;
  let ready = false;
  let build: () => Record<string, unknown> = () => ({});

  if (need === "blood") {
    ready = !!pick;
    build = () => ({ blood: { type: pick } });
    body = (
      <div className="og" style={{ gridTemplateColumns: "repeat(4,1fr)" }}>
        {ch.blood.map((b) => (
          <button key={b} className={`op ${pick === b ? "on" : ""}`}
                  style={{ textAlign: "center" }} onClick={() => setPick(b)}>
            {b}
          </button>
        ))}
      </div>
    );
  } else if (need === "image") {
    ready = !!pick;
    build = () => ({ image: { pick } });
    body = (
      <div className="og c2">
        {ch.image.map((x) => (
          <button key={x.id} className={`op ${pick === x.id ? "on" : ""}`}
                  onClick={() => setPick(x.id)}>{x.label}</button>
        ))}
      </div>
    );
  } else if (need === "cards") {
    ready = picks.length === 3;
    build = () => ({ cards: { picks } });
    body = (
      <>
        <div className="og c2">
          {ch.card.map((x) => (
            <button key={x.id} className={`op ${picks.includes(x.id) ? "on" : ""}`}
                    onClick={() => togglePick(x.id)}>{x.label}</button>
          ))}
        </div>
        <p className="sm">{picks.length} / 3</p>
      </>
    );
  } else if (need === "context") {
    ready = !!pick && !!stance;
    build = () => ({
      context: { situation: pick, stance,
                 months: months === "" ? 0 : Number(months) },
    });
    body = (
      <>
        <div className="og c2">
          {ch.situation.map((x) => (
            <button key={x.id} className={`op ${pick === x.id ? "on" : ""}`}
                    onClick={() => setPick(x.id)}>{x.label}</button>
          ))}
        </div>
        <p className="sm mt">그 자리에서 지금 어찌하고 계시오?</p>
        <div className="og" style={{ gridTemplateColumns: "repeat(3,1fr)" }}>
          {ch.stance.map((x) => (
            <button key={x.id} className={`op ${stance === x.id ? "on" : ""}`}
                    style={{ textAlign: "center" }}
                    onClick={() => setStance(x.id)}>{x.label}</button>
          ))}
        </div>
        <p className="sm mt">그리 된 지 몇 달이오? (모르면 비워 두시오)</p>
        <input className="fld" inputMode="numeric" maxLength={3} placeholder="0"
               value={months}
               onChange={(e) => setMonths(e.target.value.replace(/[^0-9]/g, ""))} />
      </>
    );
  } else if (need === "partner") {
    const n = (v: string) => v.replace(/[^0-9]/g, "");
    ready = p.year.length === 4 && !!p.month && !!p.day;
    build = () => ({
      partner: {
        year: Number(p.year), month: Number(p.month), day: Number(p.day),
        sex: p.sex, hour_known: false,
      },
    });
    body = (
      <>
        <div className="f3">
          <div><label>년</label>
            <input className="fld" inputMode="numeric" maxLength={4} placeholder="1993"
                   value={p.year} onChange={(e) => setP({ ...p, year: n(e.target.value) })} /></div>
          <div><label>월</label>
            <input className="fld" inputMode="numeric" maxLength={2} placeholder="5"
                   value={p.month} onChange={(e) => setP({ ...p, month: n(e.target.value) })} /></div>
          <div><label>일</label>
            <input className="fld" inputMode="numeric" maxLength={2} placeholder="15"
                   value={p.day} onChange={(e) => setP({ ...p, day: n(e.target.value) })} /></div>
        </div>
        <div className="og c2 mt">
          {([["F", "여인"], ["M", "사내"]] as const).map(([v, l]) => (
            <button key={v} className={`op ${p.sex === v ? "on" : ""}`}
                    style={{ textAlign: "center" }}
                    onClick={() => setP({ ...p, sex: v })}>{l}</button>
          ))}
        </div>
        <p className="sm mt">
          때는 안 묻소 — 모르는 걸 채우지 않소. 적으신 것은 <b>남기지 않습니다.</b>
        </p>
      </>
    );
  } else {
    return null;
  }

  return (
    <div className="ask blk in">
      <div className="lab">{TITLE[need] ?? "한 가지를 더 묻소"}</div>
      <p className="sm">{WHY[need] ?? ""}</p>
      {body}
      <button className="btn mt" disabled={!ready || busy}
              onClick={() => onSubmit(build())}>
        {busy ? "다시 펴는 중입니다" : "이걸로 봐 주십시오"}
      </button>
      <p className="sm">
        안 적으셔도 되오.
        그 자리 하나만 접히고 나머지는 그대로 있소.
      </p>
    </div>
  );
}
