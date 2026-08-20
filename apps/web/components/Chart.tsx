"use client";

/**
 * 명식 표시 — 기둥 · 오행 막대 · 보정 내역.
 *
 * ★ hour_known=false 면 시주 칸을 **잠금 표시**합니다. 채우지 않습니다.
 *   (CLAUDE.md 절대 규칙 1)
 */
import type { Features } from "@shared/chart";

const EL_WORD: Record<string, string> = {
  목: "나무", 화: "불", 토: "흙", 금: "쇠", 수: "물",
};

export function Pillars({ f }: { f: Features }) {
  const cells = [...f.pillars];
  return (
    <div className="ms">
      {cells.map((p, i) => (
        <div className="pil" key={p.label} style={{ animationDelay: `${i * 0.33}s` }}>
          <div className="lb">{p.label}</div>
          <div className="gz">{p.gan}</div>
          <div className="gz">{p.ji}</div>
        </div>
      ))}
      {!f.hour_known && (
        <div className="pil locked" title="시각을 모르므로 세우지 않았습니다">
          <div className="lb">시주</div>
          <div className="gz">◇</div>
          <div className="gz">◇</div>
        </div>
      )}
    </div>
  );
}

export function ElementBar({ f }: { f: Features }) {
  const entries = Object.entries(f.elements);
  const max = Math.max(...entries.map(([, v]) => v), 1);
  return (
    <div className="elbar">
      {entries.map(([k, v], i) => (
        <div key={k}>
          <i style={{
            ["--h" as string]: `${Math.max(3, (v / max) * 48)}px`,
            animationDelay: `${i * 0.11}s`,
          }} />
          <div className="lb">{k}</div>
          <div className="vv">{v}</div>
        </div>
      ))}
    </div>
  );
}

/** 셈에 쓴 것 — 계산 정밀도가 이 서비스의 자산이므로 사용자에게 보여준다. (docs/05 §10) */
export function CalcPanel({ f }: { f: Features }) {
  const c = f.correction;
  const rows: [string, React.ReactNode][] = [
    ["표준시", c.std_label],
    ["서머타임", c.dst ? <b>적용 · 1시간 되돌림</b> : "해당 없음"],
    ["진태양시", <>{c.city} → <b>{c.lon_min > 0 ? "+" : ""}{c.lon_min}분</b></>],
    ["보정", c.hour_used
      ? <><s>{c.before}</s> → <b>{c.after}</b>{c.day_shift
          ? <b> ({c.day_shift > 0 ? "익" : "전"}일)</b> : null}</>
      : "시각 미상 — 보정 없음"],
    ["절기", `${c.jieqi_name} 절입 ${c.jieqi_at_kst} 기준`],
    ["자시", c.zi_policy],
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
    </div>
  );
}

export function Summary({ f }: { f: Features }) {
  const weakWords = (f.weak_els ?? [f.weak_el]).map((e) => EL_WORD[e] ?? e);
  return (
    <div className="sum">
      <p>
        <b>{f.day_gan}</b> 일간 · <b>{f.strength}</b>({f.strength_score}) ·
        용신 <b>{EL_WORD[f.yongsin] ?? f.yongsin}</b>
      </p>
      <p className="sm">
        가장 강한 것 {EL_WORD[f.strong_el]} {f.elements[f.strong_el as keyof typeof f.elements]} ·
        가장 약한 것 {weakWords.join(" · ")}{" "}
        {f.elements[f.weak_el as keyof typeof f.elements]} · 흐름 {f.flow}
      </p>
      <p className="sm">
        대운 {f.forward ? "순행" : "역행"} · 대운수 {f.daeun[0]?.start_age}
        {f.daeun_started === false && " (아직 들지 않았소)"}
      </p>

      {/*
        동률이면 그 사실을 숨기지 않는다.
        주도 십신은 43%가 동률이다. 단정해서 말하면 그게 거짓말이 된다.
      */}
      {f.top_ten_god_tied && (
        <p className="sm" style={{ color: "var(--gold)" }}>
          ※ 주도 십신 <b>{f.top_ten_god}</b> 은 다른 십신과 개수가 같소.
          월지에 뿌리를 둔 쪽으로 잡았소.
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
