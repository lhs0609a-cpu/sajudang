"use client";

/**
 * 명식 표시 — 기둥 · 오행 막대 · 보정 내역.
 *
 * ★ hour_known=false 면 시주 칸을 **잠금 표시**합니다. 채우지 않습니다.
 *   (CLAUDE.md 절대 규칙 1)
 */
import { useEffect, useState } from "react";
import type { Features } from "@shared/chart";

const EL_WORD: Record<string, string> = {
  목: "나무", 화: "불", 토: "흙", 금: "쇠", 수: "물",
};

/*
 * ★ 화면이 손님이 모르는 말로만 되어 있었습니다.
 *
 *   "여덟 글자가 섰다 · 년주 월주 일주 시주 · 庚 일간 · 신강(26) ·
 *    용신 불 · 흐름 식상 · 주도 십신 상관 · 대운 순행 대운수 4"
 *
 *   이 집은 "근거 대는 집" 인데, 근거를 **모르는 말로** 대면 그건 근거가
 *   아니라 주문입니다. 처음 온 사람이 하나도 못 알아봅니다.
 *
 * ★ 용어를 지우지 않습니다. 옆에 뜻을 답니다.
 *   명리 용어는 이 집의 근거이자 신뢰의 재료입니다. 없애면 여느
 *   점집과 같아집니다. 대신 **모르는 말이 나올 때마다 그 자리에서**
 *   풀어 줍니다.
 */
const WHAT: Record<string, string> = {
  년주: "태어난 해",
  월주: "태어난 달",
  일주: "태어난 날 — 여기가 나 자신이오",
  시주: "태어난 시각",
};

/** 십신 열 — 여덟 글자 사이의 관계에 붙인 이름 */
const TEN_GOD: Record<string, string> = {
  비견: "나와 같은 힘 — 고집·자립",
  겁재: "나와 겨루는 힘 — 경쟁·나눔",
  식신: "밖으로 내놓는 힘 — 표현·먹는 복",
  상관: "밖으로 내지르는 힘 — 재주·거침",
  편재: "굴리는 재물 — 벌이·씀씀이",
  정재: "쌓는 재물 — 성실·저축",
  편관: "나를 누르는 힘 — 압박·책임",
  정관: "나를 잡아 주는 힘 — 규율·자리",
  편인: "받아들이는 힘 — 직관·비주류 공부",
  정인: "기대는 힘 — 배움·보살핌",
};

const STRENGTH: Record<string, string> = {
  신강: "기운이 넉넉한 쪽",
  중화: "한쪽으로 크게 안 기운 쪽",
  신약: "기운이 모자란 쪽",
};

export function Pillars({ f }: { f: Features }) {
  /*
   * ★ .pil 은 opacity:0 · rotateY(90deg) 로 시작합니다.
   *   .flip 을 붙여야 보입니다. 참조 구현체는 JS 로 붙였는데
   *   그걸 옮기지 않아 **기둥이 아예 안 보이던** 버그가 있었습니다.
   *   기둥 뒤집기는 로딩이 아니라 결과 발표 연출입니다. (docs/08 §7)
   */
  const [flip, setFlip] = useState(false);
  useEffect(() => {
    const t = setTimeout(() => setFlip(true), 40);
    return () => clearTimeout(t);
  }, []);

  const cells = [...f.pillars];
  return (
    <div className="ms">
      {cells.map((p, i) => (
        <div className={"pil" + (flip ? " flip" : "")} key={p.label}
             style={{ animationDelay: `${i * 0.33}s` }}>
          <div className="p">{p.label}</div>
          <div className="g">{p.gan}</div>
          <div className="j">{p.ji}</div>
          {/* 이 기둥이 무엇을 보는 자리인지. 없으면 한자 넉 줄일 뿐입니다. */}
          <div className="what">{WHAT[p.label] ?? ""}</div>
        </div>
      ))}
      {!f.hour_known && (
        <div className={"pil lk" + (flip ? " flip" : "")}
             style={{ animationDelay: `${cells.length * 0.33}s` }}
             title="시각을 모르므로 세우지 않았습니다">
          <div className="p">시주</div>
          <div className="g">◇</div>
          <div className="j">◇</div>
          <div className="what">때를 모르셔서 안 세웠소</div>
        </div>
      )}
    </div>
  );
}

export function ElementBar({ f }: { f: Features }) {
  const entries = Object.entries(f.elements);
  const max = Math.max(...entries.map(([, v]) => v), 1);
  return (
    <>
      {/* ★ 목·화·토·금·수 다섯 글자와 숫자만 있었습니다. 손님은
          이게 무엇을 센 것인지 모릅니다. */}
      <p className="barhead">
        <b>다섯 기운(오행)</b> — 여덟 글자를 나무·불·흙·쇠·물로 나눠 센 것이오.
        많다고 좋고 적다고 나쁜 게 아니라, <b>치우친 자리</b>를 봅니다.
      </p>
    <div className="elbar">
      {entries.map(([k, v], i) => (
        <div key={k}>
          {/* 막대 자리를 고정 높이로 잡아야 라벨이 한 줄로 선다.
              안 잡으면 막대 길이만큼 라벨이 위아래로 흩어지고
              아래 글씨를 덮는다. */}
          <span className="bar">
            <i style={{
              ["--h" as string]: `${Math.max(3, (v / max) * 48)}px`,
              animationDelay: `${i * 0.11}s`,
            }} />
          </span>
          <div className="lb">{k}</div>
          <div className="ko">{EL_WORD[k] ?? ""}</div>
          <div className="vv">{v}</div>
        </div>
      ))}
    </div>
    </>
  );
}

/** 셈에 쓴 것 — 계산 정밀도가 이 서비스의 자산이므로 사용자에게 보여준다. (docs/05 §10) */
/*
 * 지장간 — 지지 속에 숨은 천간.
 *
 * ★ 서버(engine/constants.py HIDDEN)와 **같은 표**입니다. 두 곳이
 *   다르면 화면과 셈이 다른 말을 하게 됩니다. 검사가 지킵니다.
 *
 * ★ 이걸 보여 주는 까닭 — 손님이 「나무가 0개인데 왜 0.3이냐」 고
 *   묻습니다. 답이 여기 있습니다: 亥 안에 甲이 들어 있습니다.
 *   말로만 하면 안 믿고, 표로 보여 주면 셀 수 있습니다.
 */
const HIDDEN: Record<string, string[]> = {
  子: ["癸"], 丑: ["己", "癸", "辛"], 寅: ["甲", "丙", "戊"], 卯: ["乙"],
  辰: ["戊", "乙", "癸"], 巳: ["丙", "庚", "戊"], 午: ["丁", "己"],
  未: ["己", "丁", "乙"], 申: ["庚", "壬", "戊"], 酉: ["辛"],
  戌: ["戊", "辛", "丁"], 亥: ["壬", "甲"],
};

/**
 * 만세력처럼 보는 표.
 *
 * ★ 왜 이걸 따로 두나
 *
 *   손님은 쓰던 만세력 앱과 대 봅니다. 우리 화면이 다른 모양이면
 *   **한 줄씩 눈으로 옮겨** 가며 견줘야 합니다. 그러다 지칩니다.
 *
 *   만세력이 늘 그리는 모양 그대로 둡니다 — 오른쪽부터 시·일·월·년,
 *   위가 천간 아래가 지지, 그 아래 지장간. 그러면 나란히 놓고
 *   **눈으로 바로** 견줄 수 있습니다.
 *
 * ★ 순서가 거꾸로인 까닭
 *
 *   만세력은 오른쪽에서 왼쪽으로 읽습니다(시 · 일 · 월 · 년). 우리
 *   화면은 왼쪽부터 년주였습니다. 익숙한 순서를 바꾸면 그것만으로
 *   「다른 값」처럼 보입니다.
 */
export function ManseTable({ f }: { f: Features }) {
  const cols = [...f.pillars].reverse();      // 시 · 일 · 월 · 년
  const plain = countPlain(f.pillars);
  const day = f.pillars.find((p) => p.label === "일주");

  return (
    <div className="manse">
      <div className="t">
        <span>■ 만세력처럼 보기</span>
        <span className="dim">오른쪽부터 시 · 일 · 월 · 년</span>
      </div>

      <table className="mt">
        <tbody>
          <tr className="lab">
            {cols.map((p) => <td key={p.label}>{p.label}</td>)}
          </tr>
          <tr className="gan">
            {cols.map((p) => (
              <td key={p.label} className={`el-${EL_GAN[p.gan] ?? ""}`}>
                <b>{p.gan}</b>
                <i>{EL_KO[EL_GAN[p.gan]] ?? ""}</i>
                {p.gan === day?.gan && p.label === "일주" && (
                  <em>나</em>
                )}
              </td>
            ))}
          </tr>
          <tr className="ji">
            {cols.map((p) => (
              <td key={p.label} className={`el-${EL_JI[p.ji] ?? ""}`}>
                <b>{p.ji}</b>
                <i>{EL_KO[EL_JI[p.ji]] ?? ""}</i>
              </td>
            ))}
          </tr>
          <tr className="hid">
            {cols.map((p) => (
              <td key={p.label}>
                {(HIDDEN[p.ji] ?? []).map((g) => (
                  <span key={g} className={`el-${EL_GAN[g] ?? ""}`}>{g}</span>
                ))}
              </td>
            ))}
          </tr>
        </tbody>
      </table>
      <p className="sm dim">
        아랫줄은 <b>지장간</b> — 지지 속에 숨은 천간이오. 글자로는 안
        보이지만 셈에는 듭니다. 나무가 없는데 0.3 이 나오는 까닭이
        여기 있소.
      </p>

      <div className="mcount">
        {(["수", "금", "토", "화", "목"] as const).map((k) => (
          <div key={k} className={`el-${k}`}>
            <b>{EL_KO[k]}</b>
            <span>{plain[k] ?? 0}개</span>
          </div>
        ))}
      </div>
      <p className="sm dim">
        여덟 글자만 세면 이렇소. 지장간까지 넣어 무게를 매긴 값은 위의
        막대에 있소.
      </p>
    </div>
  );
}


export function CalcPanel({ f }: { f: Features }) {
  const c = f.correction;
  const rows: [string, React.ReactNode][] = [
    ["표준시", <>{c.std_label} <i className="gl">(그 시절 우리나라가 쓰던 시계 기준)</i></>],
    ["서머타임", c.dst ? <b>적용 · 1시간 되돌림</b> : "해당 없음"],
    ["진태양시", <>{c.city} → <b>{c.lon_min > 0 ? "+" : ""}{c.lon_min}분</b> <i className="gl">(해가 남중하는 때로 고친 시각)</i></>],
    ["보정", c.hour_used
      ? <><s>{c.before}</s> → <b>{c.after}</b>{c.day_shift
          ? <b> ({c.day_shift > 0 ? "익" : "전"}일)</b> : null}</>
      : "시각 미상 — 보정 없음"],
    ["절기", <>{c.jieqi_name} 절입 {c.jieqi_at_kst} 기준 <em className="fork">집마다 다름</em>
      <i className="gl">(계절이 바뀌는 마디 스물넷 · 넘어가는 시각까지 셉니다)</i></>],
    ["자시", <>{c.zi_policy} <em className="fork">집마다 다름</em>
      <i className="gl">(밤 11시부터 다음 날로 보는가)</i></>],
    ["시주", c.hour_used
      ? <b>산출됨</b>
      : <b style={{ color: "var(--gold)" }}>제외 — 세 기둥으로 계산</b>],
  ];
  return (
    <div className="calc">
      <div className="t">
        <span>■ 셈에 쓴 것</span>
        <span style={{ color: "var(--paper3)" }}>검증 가능</span>
      </div>
      {rows.map(([k, v]) => (
        <div className="r" key={k}>
          <span className="k">{k}</span><span className="v">{v}</span>
        </div>
      ))}
      {c.boundary_note && (
        <p className="sm" style={{ color: "var(--gold)", marginTop: 8 }}>
          {c.boundary_note}
        </p>
      )}

      {/*
        ★ 집마다 다른 자리를 **누구에게나** 밝힙니다.

          전에는 실제로 갈리는 사람에게만 말했습니다. 그런데 손님은
          자기가 안 걸리는 줄도 모르고 다른 만세력과 대 봅니다.
          「어디가 다를 수 있는지」 를 먼저 알면, 같게 나왔을 때도
          그게 우연이 아니라는 걸 압니다.

          그리고 안 걸리는 사람에게는 **안 걸린다고** 말해 줍니다 —
          그게 이 화면에서 가장 안심되는 한 줄입니다.
      */}
      <p className="sm dim" style={{ marginTop: 9 }}>
        위 둘(<b>절기 기준</b> · <b>자시</b>)은 집마다 다르게 정하오.
        이 집은 <b>진태양시로 고친 시각</b>과 견주고, 밤 11시는
        <b> 다음 날</b>로 보오. 다르게 정한 집도 정식이오 —
        틀린 게 아니라 <b>고른 것이 다른</b> 것이오.
        {" "}
        {c.boundary_note
          ? <b style={{ color: "var(--gold)" }}>그대는 그 자리에 걸리오.</b>
          : <b>그대는 그 자리에 안 걸리니, 어느 집에서 보아도 같소.</b>}
      </p>
    </div>
  );
}

/* 글자 그대로 세기 — 손님이 직접 셀 수 있는 수라야 합니다.
   서버의 상수와 같은 표입니다 (engine/constants.py). */
const EL_GAN: Record<string, string> = {
  甲: "목", 乙: "목", 丙: "화", 丁: "화", 戊: "토",
  己: "토", 庚: "금", 辛: "금", 壬: "수", 癸: "수",
};
const EL_JI: Record<string, string> = {
  子: "수", 丑: "토", 寅: "목", 卯: "목", 辰: "토", 巳: "화",
  午: "화", 未: "토", 申: "금", 酉: "금", 戌: "토", 亥: "수",
};
const EL_KO: Record<string, string> = {
  목: "나무", 화: "불", 토: "흙", 금: "쇠", 수: "물",
};

function countPlain(pillars: { gan: string; ji: string }[]) {
  const n: Record<string, number> = { 목: 0, 화: 0, 토: 0, 금: 0, 수: 0 };
  for (const p of pillars) {
    if (EL_GAN[p.gan]) n[EL_GAN[p.gan]] += 1;
    if (EL_JI[p.ji]) n[EL_JI[p.ji]] += 1;
  }
  return n;
}

/** 「물 4 · 금 2 · 흙 1 · 불 1 · 나무 없음」 */
function elWords(n: Record<string, number>, dec = false) {
  return Object.entries(n)
    .sort((a, b) => b[1] - a[1])
    .map(([k, v]) => `${EL_KO[k] ?? k} ${v === 0 ? "없음"
      : dec ? v.toFixed(1).replace(/\.0$/, "") : v}`)
    .join(" · ");
}

export function Summary({ f }: { f: Features }) {
  const weakWords = (f.weak_els ?? [f.weak_el]).map((e) => EL_WORD[e] ?? e);
  const strong = EL_WORD[f.strong_el] ?? f.strong_el;
  const yong = EL_WORD[f.yongsin] ?? f.yongsin;
  const turn = f.daeun[0]?.start_age;

  const plain = countPlain(f.pillars);
  const plainWords = elWords(plain);
  const weightWords = elWords(f.elements as unknown as Record<string, number>, true);

  return (
    <div className="sum">
      {/*
        ★ 여기가 "庚 일간 · 신강(26) · 용신 불" 한 줄이었습니다.
          손님은 넷 다 모릅니다. 한 줄씩 갈라 뜻을 답니다.

        ★ 그리고 **(26) 은 내부 점수**였습니다. 신강약을 재는 우리 쪽
          척도인데 그게 화면에 그대로 나가고 있었습니다. 근거는 보이되
          규칙은 감춥니다 (CLAUDE.md) — 뺐습니다.
      */}
      <div className="term">
        <span className="k">{f.day_gan} 일간</span>
        <span className="v">여덟 글자 중 <b>나 자신</b>을 나타내는 글자요.
          태어난 날의 윗 글자를 봅니다.</span>
      </div>

      <div className="term">
        <span className="k">{f.strength}</span>
        <span className="v">{STRENGTH[f.strength] ?? ""} —
          내 편을 드는 기운과 나를 누르는 기운을 견줘 봅니다.</span>
      </div>

      <div className="term">
        <span className="k">용신 {yong}</span>
        <span className="v"><b>모자란 것을 채워 줄 기운</b>이오.
          이걸 어디서 얻을지가 이 집이 보는 자리요.</span>
      </div>

      {/*
        ★ 여기서 신뢰가 깨지고 있었습니다.

          「가장 많은 건 물 4, 가장 적은 건 나무 0.3」 이라고 냈습니다.
          그런데 손님은 여덟 글자를 **직접 셉니다.** 세어 보면 나무는
          0개인데 화면은 0.3 이라 하고, 금은 2개인데 2.3 이라 합니다.
          그러면 「이거 진짜 사주 맞나」 가 됩니다.

          0.3 은 지지 속에 숨은 글자(지장간)까지 넣어 **무게를 매긴**
          값입니다. 명리에서 쓰는 정식 셈이지만, **그 말을 안 하면
          그냥 틀린 수**입니다.

          그래서 순서를 뒤집습니다 —
            1. 손님이 직접 셀 수 있는 수를 먼저 냅니다 (여덟 글자)
            2. 숨은 글자까지 넣은 수를 그 다음에, 까닭과 함께
      */}
      <div className="term">
        <span className="k">기운 세기</span>
        <span className="v">
          <b>여덟 글자로 세면</b> {plainWords}.
          <br />
          <span className="dim">
            지지(아랫글자) 속에 <b>숨은 글자</b>가 더 있소. 그것까지 넣어
            무게를 매기면 {weightWords}. 그래서 글자로는 없는 기운이
            0.3 처럼 나오오 — 戌 안에 辛이 든 것 같은 자리요.
          </span>
        </span>
      </div>

      <div className="term">
        <span className="k">주도 {f.top_ten_god}</span>
        <span className="v">
          {TEN_GOD[f.top_ten_god] ?? ""} — 여덟 글자 사이의 관계에 붙인
          이름 열 가지 중 그대에게 가장 많은 것이오.
        </span>
      </div>

      <div className="term">
        <span className="k">대운 {turn}살부터</span>
        <span className="v">
          십 년마다 <b>읽는 자리가 바뀌는</b> 것을 대운이라 하오.
          그대는 {turn}살에 첫 칸이 들고,
          {f.forward ? " 앞으로 나아가며" : " 거꾸로 거슬러"} 도오.
          {f.daeun_started === false && " 아직 그 나이가 안 됐소."}
        </span>
      </div>

      {/*
        동률이면 그 사실을 숨기지 않는다.
        주도 십신은 43%가 동률이다. 단정해서 말하면 그게 거짓말이 된다.
      */}
      {f.top_ten_god_tied && (
        <p className="sm note">
          ※ 주도로 잡은 <b>{f.top_ten_god}</b> 은 다른 것과 개수가 같소.
          태어난 달에 뿌리를 둔 쪽으로 골랐소 — 갈릴 수 있는 자리라 적어 두오.
        </p>
      )}
      {(f.weak_els?.length ?? 1) > 1 && (
        <p className="sm" style={{ color: "var(--gold)" }}>
          ※ {weakWords.join(" 과 ")} 이 똑같이 바닥이오. 둘 다 없는 자리요.
        </p>
      )}
    </div>
  );
}
