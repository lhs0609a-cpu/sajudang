"use client";

/**
 * /admin — 주인 화면.
 *
 * ★ 왜 주소를 갈랐나
 *
 *   전에는 손님 화면 주소 뒤에 `?admin=1` 만 붙이면 레일이 열렸습니다.
 *   그건 잠금이 아니라 **가림**입니다 — 아무나 붙일 수 있고, 실수로
 *   그 주소를 공유하면 그대로 열립니다.
 *
 *   이제 주인 화면은 `/admin` 한 자리입니다. 매출·이탈은 영업 정보라
 *   퍼널과 **같은 열쇠**(FUNNEL_KEY) 뒤에 둡니다. 열쇠는 이 기기에만
 *   남고 서버로는 머리표로만 갑니다.
 *
 * ★ 손님 화면은 깨끗합니다
 *
 *   유저 모드로 넘기면 레일이 사라지고 손님이 보는 그대로가 됩니다.
 *   되돌아오는 길은 이 화면 주소를 아는 사람에게만 있습니다.
 */
import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { SCREEN_GROUPS, useSession } from "@/lib/store";

const BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";
const KEY = "sd.adminkey";

type Overview = {
  at: string;
  sales: {
    orders_all: number; paid: number; paid_today: number; refunded: number;
    revenue: number; revenue_today: number; close_rate: number | null;
    by_tier: Record<string, number>; by_lens: Record<string, number>;
  };
  live: { sessions_seen: number; active_15m: number };
  funnel: {
    sessions?: number;
    steps?: { screen: string; label: string; sessions: number;
              from_prev: number | null; from_top: number | null;
              lost: number | null }[];
    hook?: { stage: string; shown: number; answered: number;
             yes_rate: number | null }[];
  };
  house: Record<string, unknown>;
};

/*
 * 연출 점수 — 화면마다 「다음 화가 보고 싶어지는가」.
 *
 * ★ 서버가 **실제로 나가는 글을 그 자리에서 재서** 냅니다.
 *   지어낸 숫자가 아니라, 문장을 고치면 바로 움직이는 값입니다.
 *   (engine/dramaturgy.py · engine/screenscan.py)
 */
type ScreenScore = {
  id: string; title: string; kind: string; chars: number;
  pull: number; bite: number; depth: number; plain: number; total: number;
  actout: string[]; missing: string[];
};
type Drama = {
  at: string;
  summary: {
    screens: number; pull: number; bite: number; depth: number;
    plain: number; total: number;
    weakest: { id: string; title: string; total: number }[];
  };
  screens: ScreenScore[];
};

const won = (n: number) => n.toLocaleString("ko-KR") + "원";

export default function AdminPage() {
  const router = useRouter();
  const s = useSession();
  const [key, setKey] = useState("");
  const [typed, setTyped] = useState("");
  const [data, setData] = useState<Overview | null>(null);
  const [drama, setDrama] = useState<Drama | null>(null);
  const [openRow, setOpenRow] = useState<string | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    try { setKey(localStorage.getItem(KEY) ?? ""); } catch { /* 막힌 브라우저 */ }
  }, []);

  const load = useCallback(async (k: string) => {
    if (!k) return;
    setBusy(true);
    setErr(null);
    try {
      const r = await fetch(BASE + "/v1/admin/overview",
                            { headers: { "x-funnel-key": k } });
      if (r.status === 401) throw new Error("열쇠가 맞지 않습니다.");
      if (r.status === 503) throw new Error("서버에 FUNNEL_KEY 가 없습니다.");
      if (!r.ok) throw new Error("가져오지 못했습니다 (" + r.status + ")");
      setData(await r.json());
      /*
       * ★ 연출 점수는 **매출과 함께** 받아 옵니다.
       *
       *   손님이 "항상 연동해서 점수 보여줘" 라 했습니다. 따로 누르게
       *   해 두면 안 누르고, 안 누르면 없는 것과 같습니다.
       *   실패해도 매출 화면은 안 막습니다 — 점수는 곁다리입니다.
       */
      try {
        const d = await fetch(BASE + "/v1/admin/screens",
                              { headers: { "x-funnel-key": k } });
        setDrama(d.ok ? await d.json() : null);
      } catch {
        setDrama(null);
      }
    } catch (e) {
      setErr(e instanceof Error ? e.message : "가져오지 못했습니다.");
      setData(null);
    } finally {
      setBusy(false);
    }
  }, []);

  useEffect(() => { void load(key); }, [key, load]);

  /* ── 열쇠를 받기 전 ─────────────────────────────────── */
  if (!key || (err && !data)) {
    return (
      <main className="adm">
        <h1>성신당 · 주인 자리</h1>
        <p className="sm">
          매출과 이탈은 영업 정보라 열쇠를 겁니다. 열쇠는 이 기기에만
          남습니다.
        </p>
        {err && <p className="admerr">{err}</p>}
        <input className="fld" type="password" placeholder="FUNNEL_KEY"
               value={typed} onChange={(e) => setTyped(e.target.value)}
               onKeyDown={(e) => {
                 if (e.key === "Enter") {
                   try { localStorage.setItem(KEY, typed); } catch { /* */ }
                   setKey(typed);
                 }
               }} />
        <button className="btn mt" onClick={() => {
          try { localStorage.setItem(KEY, typed); } catch { /* */ }
          setKey(typed);
        }}>
          연다
        </button>
        <Link className="admlink" href="/">손님 화면으로</Link>
      </main>
    );
  }

  const flat = SCREEN_GROUPS.flatMap((g) => g.items);
  const sales = data?.sales;
  const steps = data?.funnel?.steps ?? [];
  const worst = steps.length
    ? steps.reduce((a, b) =>
        ((b.lost ?? 0) > (a.lost ?? 0) ? b : a))
    : null;

  return (
    <main className="adm">
      <div className="admtop">
        <h1>성신당 · 주인 자리</h1>
        <div className="admmode">
          <span className="on">관리자</span>
          {/*
            ★ 유저 모드 — 레일을 끄고 손님이 보는 그대로 넘어갑니다.
              돌아오는 길은 이 주소(/admin)를 아는 사람에게만 있습니다.
          */}
          <button onClick={() => {
            s.set({ admin: false });
            router.push("/");
          }}>
            유저 모드로
          </button>
        </div>
      </div>

      <p className="sm">
        {busy ? "세는 중이오…" : data ? `기준 ${data.at}` : ""}
        {" · "}
        <button className="lnk" onClick={() => void load(key)}>다시 세기</button>
        {" · "}
        <button className="lnk" onClick={() => {
          try { localStorage.removeItem(KEY); } catch { /* */ }
          setKey("");
        }}>열쇠 지우기</button>
      </p>

      {/* ── 돈 ───────────────────────────────────────── */}
      <section>
        <h2>돈</h2>
        <div className="kpi">
          <div><b>{sales ? won(sales.revenue) : "—"}</b><span>총 매출</span></div>
          <div><b>{sales ? won(sales.revenue_today) : "—"}</b><span>오늘</span></div>
          <div><b>{sales?.paid ?? "—"}</b><span>치른 건</span></div>
          <div><b>{sales?.paid_today ?? "—"}</b><span>오늘 치른 건</span></div>
          <div><b>{sales?.close_rate == null ? "—" : sales.close_rate + "%"}</b>
               <span>주문 → 결제</span></div>
          <div><b>{sales?.refunded ?? "—"}</b><span>환불</span></div>
        </div>
        {sales && Object.keys(sales.by_tier).length > 0 && (
          <table className="admt">
            <tbody>
              {Object.entries(sales.by_tier).map(([k, v]) => (
                <tr key={k}><td>{k}</td><td className="n">{v}건</td></tr>
              ))}
            </tbody>
          </table>
        )}
        {sales && sales.paid === 0 && (
          <p className="sm">
            아직 치른 건이 없소. 실거래를 한 번도 안 돌려 봤다면
            4,900원짜리로 한 번 해 보시오 — 결제 · 리포트 · 환불까지.
          </p>
        )}
      </section>

      {/* ── 사람 ─────────────────────────────────────── */}
      <section>
        <h2>사람</h2>
        <div className="kpi">
          <div><b>{data?.live.active_15m ?? "—"}</b><span>지금 도는 사람</span></div>
          <div><b>{data?.funnel?.sessions ?? "—"}</b><span>들어온 사람</span></div>
        </div>
      </section>

      {/* ── 연출 점수 ────────────────────────────────── */}
      <section>
        <h2>다음 화가 보고 싶어지는가</h2>
        {!drama ? (
          <p className="sm">점수를 못 가져왔소.</p>
        ) : (
          <>
            <div className="kpi">
              <div><b>{drama.summary.pull}</b><span>당김</span></div>
              <div><b>{drama.summary.bite}</b><span>팩폭</span></div>
              <div><b>{drama.summary.depth}</b><span>충실</span></div>
              <div><b>{drama.summary.plain}</b><span>쉬움</span></div>
              <div><b>{drama.summary.total}</b><span>합 (화면 {drama.summary.screens})</span></div>
            </div>
            {drama.summary.pull < 60 && (
              <p className="admbad">
                <b>당김이 {drama.summary.pull}점.</b> 미드는 막마다 끊습니다 —
                밝힘 · 뒤집기 · 딜레마 · 끊긴 동작 · 남긴 물음 중 하나로.
                끝이 그냥 끝나는 화면은 다음으로 안 데려갑니다.
              </p>
            )}
            {/*
              ★ 표는 **낮은 것부터**. 좋은 것부터 보여 주면 고칠 자리가
                아래로 밀려 안 봅니다.
            */}
            <table className="admt drama">
              <thead>
                <tr>
                  <th>화면</th><th className="n">당김</th><th className="n">팩폭</th>
                  <th className="n">충실</th><th className="n">쉬움</th>
                  <th className="n">합</th><th>액트아웃</th>
                </tr>
              </thead>
              <tbody>
                {[...drama.screens].sort((a, b) => a.total - b.total).map((r) => (
                  <tr key={r.id}
                      className={"clk " + (r.total < 50 ? "bad"
                                 : r.total < 65 ? "mid" : "good")}
                      onClick={() => setOpenRow(openRow === r.id ? null : r.id)}>
                    <td>
                      <b>{r.id}</b> {r.title}
                      {openRow === r.id && r.missing.length > 0 && (
                        <ul className="lack">
                          {r.missing.map((m, i) => <li key={i}>{m}</li>)}
                        </ul>
                      )}
                      {openRow === r.id && r.missing.length === 0 && (
                        <p className="sm">모자란 데가 없소.</p>
                      )}
                    </td>
                    <td className="n">{r.pull}</td>
                    <td className="n">{r.bite}</td>
                    <td className="n">{r.depth}</td>
                    <td className="n">{r.plain}</td>
                    <td className="n"><b>{r.total}</b></td>
                    <td className="sm">{r.actout.join(" · ") || "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            <p className="sm">
              줄을 누르면 <b>무엇이 모자란지</b> 나오오.
              점수는 지어낸 값이 아니라 <b>지금 나가는 글</b>을 그 자리에서
              잰 것이오 — 문장을 고치면 바로 움직이오.
            </p>
          </>
        )}
      </section>

      {/* ── 어디서 나가는가 ──────────────────────────── */}
      <section>
        <h2>어디서 나가는가</h2>
        {steps.length === 0 ? (
          <p className="sm">
            아직 쌓인 게 없소. 계측은 `/v1/events` 로 들어옵니다.
          </p>
        ) : (
          <>
            {worst && (worst.lost ?? 0) > 0 && (
              <p className="admbad">
                가장 크게 잃는 자리 — <b>{worst.label}</b> 에서 {worst.lost}명
              </p>
            )}
            <table className="admt">
              <tbody>
                {steps.map((st) => (
                  <tr key={st.screen}
                      className={worst && st.screen === worst.screen ? "bad" : ""}>
                    <td>{st.screen}</td>
                    <td>{st.label}</td>
                    <td className="n">{st.sessions}</td>
                    <td className="n">
                      {st.from_prev == null ? "—" : st.from_prev + "%"}
                    </td>
                    <td className="n">{st.lost ? "−" + st.lost : ""}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </>
        )}
      </section>

      {/* ── 훅 ───────────────────────────────────────── */}
      {data?.funnel?.hook && data.funnel.hook.length > 0 && (
        <section>
          <h2>훅 — 초반이 어디서 끊기는가</h2>
          <table className="admt">
            <tbody>
              {data.funnel.hook.map((h) => (
                <tr key={h.stage}>
                  <td>{h.stage}단</td>
                  <td className="n">{h.shown}</td>
                  <td className="n">{h.answered}</td>
                  <td className="n">
                    {h.yes_rate == null ? "—" : h.yes_rate + "%"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <p className="sm">보인 수 · 답한 수 · 그렇소 비율</p>
        </section>
      )}

      {/* ── 화면 훑기 ────────────────────────────────── */}
      <section>
        <h2>화면 훑기 · {flat.length}개</h2>
        <p className="sm">
          누르면 그 화면으로 갑니다. 화면 안에서는 상단 레일의
          <b> ← 이전 / 다음 → </b>으로 순서대로 넘길 수 있소.
        </p>
        {SCREEN_GROUPS.map((g) => (
          <div key={g.group} className="admgrp">
            <div className="admgh">{g.group} · {g.label}</div>
            <div className="admscr">
              {g.items.map((it) => (
                <Link key={it.id} href={it.href}
                      onClick={() => s.set({ admin: true })}>
                  <b>{it.id}</b> {it.name}
                </Link>
              ))}
            </div>
          </div>
        ))}
      </section>

      {/* ── 집 ───────────────────────────────────────── */}
      <section>
        <h2>집</h2>
        <table className="admt">
          <tbody>
            {Object.entries(data?.house ?? {}).map(([k, v]) => (
              <tr key={k}>
                <td>{k}</td>
                <td className="n">
                  {typeof v === "object" && v !== null
                    ? Object.entries(v as Record<string, unknown>)
                        .map(([a, b]) => `${a}=${b}`).join(" · ")
                    : String(v)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </main>
  );
}
