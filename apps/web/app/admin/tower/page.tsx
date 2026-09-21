"use client";

/**
 * 관리자 항해 관제탑 — 제품이 **어디까지 준비되었는가** (SHIP OS §17 · §39).
 *
 * ★ 여기서 아무것도 세지 않습니다.
 *
 *   완료율·배선·게이트는 전부 서버의 `shipos` 한 자리가 셉니다
 *   (`GET /v1/admin/tower`). 화면은 **받아 적기만** 합니다.
 *   이 집은 값과 분량을 화면이 제 손으로 적었다가 두 벌이 되어
 *   어긋난 적이 있습니다 — "평생운 18컷" 이라 적어 두고 11컷이
 *   나갔습니다. 완료율은 그 사고가 더 조용히 납니다.
 *
 * ★ 유저 관제탑과 같은 기능 id 를 봅니다. 렌즈만 다릅니다 (§42).
 */

import { Fragment, useCallback, useEffect, useState } from "react";
import Link from "next/link";

const BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";
const KEY = "sd.adminkey";
const TOK = "sd.admintoken";

type Axis =
  | "spec" | "ui_design" | "frontend" | "backend" | "database"
  | "api" | "analytics" | "qa" | "security" | "admin";

const AXES: Axis[] = ["spec", "ui_design", "frontend", "backend", "database",
                      "api", "analytics", "qa", "security", "admin"];
const AXIS_KO: Record<Axis, string> = {
  spec: "정의", ui_design: "설계", frontend: "화면", backend: "서버",
  database: "저장", api: "문", analytics: "계측", qa: "검사",
  security: "보안", admin: "운영",
};

interface Feature {
  id: string; title: string; group: string;
  applicability: "required" | "conditional" | "na";
  reason?: string | null; gap?: string | null; blocker?: string | null;
  declared: string; status: string;
  axes: Record<string, string | null>;
  score: number; missing: string[];
  screens: string[]; apis: string[]; entities: string[];
  events: string[]; qa: string[];
}
interface Stage {
  role: string; stage: string; title: string;
  screens: string[]; features: string[];
  score: number | null; broken: string[];
}
interface Wire { id: string; severity: string; what: string; where: string }
interface Gate { ready: boolean; checks: {name: string; pass: boolean; detail: unknown}[] }
interface Tower {
  product: Record<string, unknown>;
  overall: number; counted: number; na: number;
  tally: Record<string, number>;
  features: Feature[]; stages: Stage[]; wires: Wire[];
  gate: Gate; next: {p: number; why: string; what: string}[];
}

const pct = (n: number) => Math.round(n * 1000) / 10 + "%";

/** 상태 하나를 한 글자로. 색은 CSS 가 답니다. */
function Dot({ v }: { v: string | null }) {
  if (v === null || v === undefined) return <i className="tdot na" title="해당 없음">·</i>;
  const label: Record<string, string> = {
    live: "됨", partial: "절반", spec: "정의만", none: "없음", broken: "끊김",
  };
  return <i className={"tdot " + v} title={label[v] ?? v}>{v === "live" ? "●" : v === "partial" ? "◐" : v === "broken" ? "✕" : "○"}</i>;
}

export default function TowerPage() {
  const [tower, setTower] = useState<Tower | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [open, setOpen] = useState<string | null>(null);
  const [only, setOnly] = useState<"all" | "todo" | "na">("todo");

  const load = useCallback(async () => {
    setBusy(true);
    setErr(null);
    try {
      let key = "", tok = "";
      try {
        key = localStorage.getItem(KEY) ?? "";
        tok = localStorage.getItem(TOK) ?? "";
      } catch { /* 저장소가 막혀 있어도 아래에서 401 로 안내합니다 */ }
      const h: Record<string, string> = {};
      if (key) h["x-funnel-key"] = key;
      if (tok) h["x-admin-token"] = tok;
      const r = await fetch(BASE + "/v1/admin/tower", { headers: h, cache: "no-store" });
      if (r.status === 401 || r.status === 503) {
        setErr("주인 자리에 먼저 들어오시오.");
        return;
      }
      if (!r.ok) throw new Error(String(r.status));
      setTower(await r.json());
    } catch {
      setErr("관제탑을 불러오지 못했소.");
    } finally {
      setBusy(false);
    }
  }, []);

  useEffect(() => { void load(); }, [load]);

  if (err) {
    return (
      <main className="adm">
        <h1>항해 관제탑</h1>
        <p className="admbad">{err}</p>
        <Link className="admlink" href="/admin">주인 자리로</Link>
      </main>
    );
  }
  if (!tower) {
    return (
      <main className="adm">
        <h1>항해 관제탑</h1>
        <p role="status">세는 중이오…</p>
      </main>
    );
  }

  const crit = tower.wires.filter((w) => w.severity === "critical");
  const shown = tower.features.filter((f) =>
    only === "all" ? true
    : only === "na" ? f.applicability === "na"
    : f.applicability !== "na" && f.status !== "live");

  const roles = Array.from(new Set(tower.stages.map((s) => s.role)));

  return (
    <main className="adm tower">
      <div className="admtop">
        <h1>항해 관제탑</h1>
        <div className="admmode">
          <Link className="admlink" href="/admin">현황판으로</Link>
          <button onClick={() => void load()} disabled={busy}>
            {busy ? "세는 중…" : "다시 세기"}
          </button>
        </div>
      </div>

      {/* ── 상단: 한눈에 (§39.2) ───────────────────────── */}
      <section className="tsum">
        <div className="tbig">
          <b>{pct(tower.overall)}</b>
          <span>전체 준비도</span>
        </div>
        <ul className="ttally">
          <li className="live"><b>{tower.tally.live ?? 0}</b><span>됨</span></li>
          <li className="partial"><b>{tower.tally.partial ?? 0}</b><span>절반</span></li>
          <li className="none"><b>{tower.tally.none ?? 0}</b><span>없음</span></li>
          <li className="broken"><b>{tower.tally.broken ?? 0}</b><span>끊김</span></li>
          <li className="na"><b>{tower.na}</b><span>의도적 제외</span></li>
        </ul>
        <div className={"tgate " + (tower.gate.ready ? "ok" : "no")}>
          <b>{tower.gate.ready ? "READY FOR RELEASE" : "NOT READY"}</b>
          <span>{tower.gate.checks.filter((c) => c.pass).length}/{tower.gate.checks.length} 통과</span>
        </div>
      </section>

      {/* ── 다음에 무엇부터 (§40) ──────────────────────── */}
      <section className="tcard">
        <h2>다음에 무엇부터</h2>
        <ol className="tnext">
          {tower.next.map((n, i) => (
            <li key={i}><span className={"tp p" + n.p}>P{n.p}</span> {n.what}<em>{n.why}</em></li>
          ))}
          {!tower.next.length && <li>지금 급한 것은 없소.</li>}
        </ol>
      </section>

      {/* ── 끊긴 배선 (§9) ─────────────────────────────── */}
      <section className="tcard">
        <h2>끊긴 배선 <small>critical {crit.length} · 전체 {tower.wires.length}</small></h2>
        {!tower.wires.length && <p>끊긴 데가 없소.</p>}
        <table className="tw">
          <tbody>
            {tower.wires.map((w, i) => (
              <tr key={i} className={w.severity}>
                <td><code>{w.id}</code></td>
                <td>{w.severity === "critical" ? "막음" : "주의"}</td>
                <td><code>{w.where}</code></td>
                <td>{w.what}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      {/* ── 역할 × 여정 단계 (§17.1) ───────────────────── */}
      <section className="tcard">
        <h2>역할 × 여정 단계</h2>
        {roles.map((role) => (
          <div key={role} className="trole">
            <h3>{role}</h3>
            <div className="tstages">
              {tower.stages.filter((s) => s.role === role).map((s) => (
                <div key={role + s.stage}
                     className={"tstage " + (s.broken.length ? "bad" : "")}>
                  <b>{s.title}</b>
                  <span>{s.score === null ? "—" : pct(s.score)}</span>
                  <small>{s.screens.join(" ")}</small>
                </div>
              ))}
            </div>
          </div>
        ))}
      </section>

      {/* ── 기능 × 구현축 (§17.2) ──────────────────────── */}
      <section className="tcard">
        <h2>
          기능 × 구현축
          <span className="tfilter">
            {(["todo", "all", "na"] as const).map((k) => (
              <button key={k} className={only === k ? "on" : ""} onClick={() => setOnly(k)}>
                {k === "todo" ? "남은 것" : k === "all" ? "전부" : "의도적 제외"}
              </button>
            ))}
          </span>
        </h2>
        <table className="tgrid">
          <thead>
            <tr>
              <th>기능</th>
              {AXES.map((a) => <th key={a} className="ax">{AXIS_KO[a]}</th>)}
              <th>점</th>
            </tr>
          </thead>
          <tbody>
            {shown.map((f) => (
              <Fragment key={f.id}>
                <tr className={"tf " + f.status}
                    onClick={() => setOpen(open === f.id ? null : f.id)}>
                  <td>
                    <b>{f.title}</b>
                    <code>{f.id}</code>
                    {f.applicability === "na" && <em className="tna">의도적 제외</em>}
                    {f.blocker && <em className="tblk">{f.blocker}</em>}
                  </td>
                  {AXES.map((a) => (
                    <td key={a} className="ax"><Dot v={f.axes[a] ?? null} /></td>
                  ))}
                  <td className="tsc">{f.applicability === "na" ? "—" : pct(f.score)}</td>
                </tr>
                {open === f.id && (
                  <tr className="tdet">
                    <td colSpan={AXES.length + 2}>
                      {f.reason && <p><b>까닭</b> {f.reason}</p>}
                      {f.gap && <p><b>빠진 것</b> {f.gap}</p>}
                      {!!f.missing.length && (
                        <p className="bad"><b>코드에 없음</b> {f.missing.join(", ")}</p>
                      )}
                      <dl className="tlinks">
                        {!!f.screens.length && <><dt>화면</dt><dd>{f.screens.join(" ")}</dd></>}
                        {!!f.apis.length && <><dt>문</dt><dd>{f.apis.join(" · ")}</dd></>}
                        {!!f.entities.length && <><dt>표</dt><dd>{f.entities.join(" ")}</dd></>}
                        {!!f.events.length && <><dt>사건</dt><dd>{f.events.join(" ")}</dd></>}
                        {!!f.qa.length && <><dt>검사</dt><dd>{f.qa.join(" ")}</dd></>}
                      </dl>
                    </td>
                  </tr>
                )}
              </Fragment>
            ))}
          </tbody>
        </table>
      </section>

      {/* ── 릴리스 게이트 (§36) ────────────────────────── */}
      <section className="tcard">
        <h2>릴리스 게이트</h2>
        <ul className="tgatelist">
          {tower.gate.checks.map((c) => (
            <li key={c.name} className={c.pass ? "ok" : "no"}>
              <b>{c.pass ? "PASS" : "FAIL"}</b> {c.name}
              {Array.isArray(c.detail) && c.detail.length
                ? <em>{(c.detail as string[]).join(", ")}</em> : null}
            </li>
          ))}
        </ul>
      </section>
    </main>
  );
}
