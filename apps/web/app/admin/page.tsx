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
import AssetBoard from "@/components/AssetBoard";

const BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";
const KEY = "sd.adminkey";
const TOK = "sd.admintoken";

type Overview = {
  at: string;
  sales: {
    orders_all: number; paid: number; paid_today: number; refunded: number;
    refunded_amount: number; pending: number; pending_amount: number;
    avg_order: number | null;
    revenue: number; revenue_today: number; close_rate: number | null;
    by_tier: Record<string, number>; by_lens: Record<string, number>;
  };
  /*
   * 지금 막힌 자리. 주인이 가장 먼저 묻는 것은 「뭐 터진 거 없소?」 입니다.
   * (services/api/routers/admin._trouble)
   */
  trouble?: {
    gate: string; enabled: boolean; live: boolean;
    pay_start: number | null; pay_fail: number | null;
    fail_rate: number | null;
    stale_pending: { order_id: string; amount: number; tier: string | null;
                     lens_id: string | null; age_min: number | null }[];
    stale_pending_all: number;
    canceled: { order_id: string; amount: number; tier: string | null;
                pg_status: string | null }[];
    canceled_all: number;
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
  /* 여섯 축 — 손님이 이름 붙인 그대로입니다.
     당김 다음 화가 보고 싶은가 · 팩폭 틀릴 수 있는 말인가 ·
     울림 눈물이 핑 도는가 · 명확 무엇을 보고 한 말인지 ·
     쉬움 어려운 말을 푸는가 · 비유 그림이 그려지는가 */
  pull: number; bite: number; heart: number;
  clear: number; plain: number; figure: number;
  /* 글이 **앉은 모양** — 앞의 여섯 축은 무슨 말을 했는지를 보고,
     이 둘은 그 말이 화면 폭에 어떻게 앉는지를 봅니다.
     줄길이   한 줄이 열넉~서른넉 자에 드는가 · 벽처럼 선 문단이 없는가
     읽기속도 이 종류의 화면치고 오래 잡지 않는가 · 숨 쉴 자리가 있는가
     (engine/typo.py — tools/widow.py 와 같은 자) */
  measure: number; pace: number; secs: number;
  total: number;
  actout: string[]; missing: string[];
};
type Drama = {
  at: string;
  summary: {
    screens: number;
    /*
     * ★ 화면 소스를 읽을 수 있었는가.
     *
     *   연출 점수는 화면 글이 코드에 박혀 있어서 `apps/web/**\/page.tsx`
     *   를 **소스째 읽어서** 셉니다. 그런데 배포 이미지(Dockerfile)에는
     *   `seed/` 와 `services/api/` 만 들어갑니다 — `apps/web` 이 없습니다.
     *
     *   그러면 27화면이 6화면으로 줄고 **숫자는 그럴듯하게 나옵니다.**
     *   그게 제일 나쁩니다. 서버는 이 깃발로 그 사실을 말하고 있었는데
     *   화면이 한 번도 안 읽었습니다 — 배포본 관리자 화면에 63점이
     *   아무 표시 없이 떠 있었습니다.
     *
     *   틀린 숫자를 내느니 **못 잰다고 말합니다.**
     *   (services/api/engine/screenscan.has_source)
     */
    has_source: boolean;
    /** source 소스째 · snapshot 찍어 둔 글(배포본) · none 못 잼 */
    source?: "source" | "snapshot" | "none";
    snapshot_at?: string | null;
    pull?: number; bite?: number; heart?: number;
    clear?: number; plain?: number; figure?: number;
    measure?: number; pace?: number; secs?: number;
    total?: number;
    weakest?: { id: string; title: string; total: number }[];
  };
  screens: ScreenScore[];
};

const won = (n: number) => n.toLocaleString("ko-KR") + "원";

/**
 * 문지기에게 내미는 것 — 쪽지든 열쇠든, 있는 것만 싣습니다.
 * 서버는 둘 중 하나만 맞으면 엽니다 (keyguard.require_admin).
 */
function head(k?: string, t?: string): Record<string, string> {
  const h: Record<string, string> = {};
  if (t) h["x-admin-token"] = t;
  if (k) h["x-funnel-key"] = k;
  return h;
}

export default function AdminPage() {
  const router = useRouter();
  const s = useSession();
  const [key, setKey] = useState("");
  const [typed, setTyped] = useState("");
  /*
   * ── 주인 문 ─────────────────────────────────────────
   *
   * ★ 문이 둘입니다 (services/api/keyguard.require_admin)
   *
   *     사람 문   아이디 · 비밀번호  →  쪽지(x-admin-token)
   *     기계 문   FUNNEL_KEY         →  도구가 씁니다
   *
   *   난수 스물네 자를 사람이 외워서 칠 수는 없습니다. 그렇다고
   *   도구에 아이디·비밀번호를 심을 수도 없습니다. 쓰는 쪽이 다르니
   *   문을 둘로 내되 지키는 자리는 서버 한 곳입니다.
   *
   * ★ 비밀번호는 **로그인 한 번**에만 오갑니다. 그 뒤로는 쪽지만
   *   오가고, 브라우저에도 쪽지만 남습니다.
   */
  const [token, setToken] = useState("");
  const [gate, setGate] = useState<{ login: boolean; key: boolean } | null>(null);
  const [email, setEmail] = useState("");
  const [pw, setPw] = useState("");
  const [logging, setLogging] = useState(false);
  const [data, setData] = useState<Overview | null>(null);
  const [drama, setDrama] = useState<Drama | null>(null);
  const [openRow, setOpenRow] = useState<string | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  /*
   * ── 실시간 ────────────────────────────────────────────
   *
   * ★ 손님이 시킨 것 (2026-09-03)
   *
   *   "성신당 연출감사표는 항상 관리자페이지에서 실시간으로 연동되어
   *   있는 점수표 볼 수 있게해줘. 수정하면 또 수정한거 파악해서
   *   점수가 매번 실시간으로 연동되어야해."
   *
   * ★ 전에는 **처음 한 번**만 받아 왔습니다.
   *
   *   글을 고치고 화면으로 돌아와도 옛 점수가 그대로 떠 있었습니다.
   *   그러면 도구를 안 믿게 됩니다 — 고쳤는데 안 움직이니까요.
   *   서버는 캐시를 안 거는데(`screens` 가 매번 다시 읽습니다) 화면이
   *   안 물어봤을 뿐입니다.
   *
   * ★ 보고 있을 때만 묻습니다.
   *
   *   탭이 뒤로 가면 멈추고, 돌아오면 곧바로 한 번 묻습니다.
   *   안 보는 화면에 5초마다 요청을 쏘는 건 서버를 괴롭히는 것입니다.
   */
  const [live, setLive] = useState(true);
  const [tick, setTick] = useState(0);

  useEffect(() => {
    try {
      setKey(localStorage.getItem(KEY) ?? "");
      setToken(localStorage.getItem(TOK) ?? "");
    } catch { /* 막힌 브라우저 */ }
  }, []);

  /* 문이 어떤 꼴인지 먼저 묻습니다 — 열쇠 칸을 그릴지, 로그인 칸을
     그릴지 화면이 정해야 합니다. 이 자리는 열쇠 없이 물어볼 수
     있고, 걸렸는지 아닌지만 답합니다 (아이디는 안 흘립니다). */
  useEffect(() => {
    /*
     * ★ 서버가 아직 옛것이면 이 자리가 404 입니다.
     *
     *   그때 `null` 로 두면 화면은 로그인 칸을 그리고, 손님(주인)은
     *   아이디를 넣어 봐야 또 404 를 만납니다. **없는 문을 그리는
     *   것**이라 열쇠 칸으로 물러섭니다 — 옛 서버에서도 열쇠는 됩니다.
     */
    fetch(BASE + "/v1/admin/gate")
      .then((r) => (r.ok ? r.json() : { login: false, key: true }))
      .then(setGate)
      .catch(() => setGate({ login: false, key: true }));
  }, []);

  const load = useCallback(async (k: string, t: string, quiet = false) => {
    if (!k && !t) return;
    // 되풀이해 묻는 자리에서는 「세는 중이오…」 를 안 띄웁니다.
    // 5초마다 글자가 바뀌면 읽고 있는 표가 흔들립니다.
    if (!quiet) setBusy(true);
    setErr(null);
    try {
      const r = await fetch(BASE + "/v1/admin/overview",
                            { headers: head(k, t) });
      if (r.status === 401) {
        // 쪽지가 삭았을 수 있소. 지우고 로그인 칸으로 돌려보냅니다.
        if (t) { try { localStorage.removeItem(TOK); } catch { /* */ } setToken(""); }
        throw new Error("문이 안 열리오. 다시 들어오시오.");
      }
      if (r.status === 503) throw new Error("주인 문이 아직 안 걸렸소.");
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
                              { headers: head(k, t) });
        setDrama(d.ok ? await d.json() : null);
      } catch {
        setDrama(null);
      }
    } catch (e) {
      setErr(e instanceof Error ? e.message : "가져오지 못했습니다.");
      // ★ 되풀이해 묻다 한 번 실패했다고 표를 지우지 않습니다.
      //   서버를 다시 띄우는 몇 초 동안 화면이 비면, 보던 자리를
      //   잃습니다. 이미 받아 둔 것은 그대로 두고 오류만 적습니다.
      if (!quiet) setData(null);
    } finally {
      setBusy(false);
    }
  }, []);

  useEffect(() => { void load(key, token); }, [key, token, load]);

  /* 실시간 — 보고 있을 때만, 5초마다. */
  useEffect(() => {
    if ((!key && !token) || !live) return;
    const t = window.setInterval(() => {
      if (document.visibilityState === "visible") setTick((n) => n + 1);
    }, 5000);
    const wake = () => {
      if (document.visibilityState === "visible") setTick((n) => n + 1);
    };
    document.addEventListener("visibilitychange", wake);
    window.addEventListener("focus", wake);
    return () => {
      window.clearInterval(t);
      document.removeEventListener("visibilitychange", wake);
      window.removeEventListener("focus", wake);
    };
  }, [key, token, live]);

  useEffect(() => {
    if (tick > 0) void load(key, token, true);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tick]);

  /* ── 문 앞 ──────────────────────────────────────────── */
  const signIn = async () => {
    setLogging(true);
    setErr(null);
    try {
      const r = await fetch(BASE + "/v1/admin/login", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ email, password: pw }),
      });
      const got = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(got.detail ?? "들어가지 못했소.");
      // ★ 비밀번호는 여기서 버립니다. 브라우저에도 안 남깁니다.
      setPw("");
      try { localStorage.setItem(TOK, got.token); } catch { /* */ }
      setToken(got.token);
    } catch (e) {
      setErr(e instanceof Error ? e.message : "들어가지 못했소.");
    } finally {
      setLogging(false);
    }
  };

  if ((!key && !token) || (err && !data)) {
    return (
      <main className="adm">
        <h1>성신당 · 주인 자리</h1>
        <p className="sm">
          매출과 이탈은 영업 정보라 문을 겁니다. 들어온 표는 이 기기에만
          남습니다.
        </p>
        {err && <p className="admerr">{err}</p>}

        {/*
          ★ 사람 문 — 아이디와 비밀번호.
            비밀번호는 로그인 한 번에만 오가고, 서버에도 해시만
            있습니다 (services/api/adminauth.py).
        */}
        {gate?.login !== false && (
          <>
            <input className="fld" type="email" autoComplete="username"
                   placeholder="아이디 (이메일)"
                   value={email} onChange={(e) => setEmail(e.target.value)} />
            <input className="fld mt" type="password"
                   autoComplete="current-password" placeholder="비밀번호"
                   value={pw} onChange={(e) => setPw(e.target.value)}
                   onKeyDown={(e) => { if (e.key === "Enter") void signIn(); }} />
            <button className="btn mt" disabled={logging || !email || !pw}
                    onClick={() => void signIn()}>
              {logging ? "여는 중입니다" : "들어가겠습니다"}
            </button>
          </>
        )}

        {/*
          ★ 기계 문 — 도구가 쓰는 열쇠. 사람은 안 씁니다.
            아이디 문이 아직 안 걸린 집에서는 이쪽이 유일한 길이라
            접어 두되 없애지는 않습니다.
        */}
        <details className="admalt" open={gate?.login === false}>
          <summary>열쇠로 열겠습니다 (도구용)</summary>
          <input className="fld mt" type="password" placeholder="FUNNEL_KEY"
                 value={typed} onChange={(e) => setTyped(e.target.value)}
                 onKeyDown={(e) => {
                   if (e.key === "Enter") {
                     try { localStorage.setItem(KEY, typed); } catch { /* */ }
                     setKey(typed);
                   }
                 }} />
          <button className="btn gh mt" onClick={() => {
            try { localStorage.setItem(KEY, typed); } catch { /* */ }
            setKey(typed);
          }}>
            연다
          </button>
        </details>

        {gate && !gate.login && !gate.key && (
          <p className="admbad">
            서버에 문이 하나도 안 걸렸소.
            {" "}<code>.\dev.ps1 admin-pass</code> 로 아이디를 세우시오.
          </p>
        )}
        <Link className="admlink" href="/">손님 화면으로</Link>
      </main>
    );
  }

  const flat = SCREEN_GROUPS.flatMap((g) => g.items);
  const sales = data?.sales;
  const trouble = data?.trouble;
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
        {/*
          ★ 실시간인지 아닌지를 화면이 말해야 합니다. 안 적어 두면
            보고 있는 숫자가 방금 것인지 아까 것인지 모릅니다.
        */}
        <button className="lnk" onClick={() => setLive((v) => !v)}>
          {live ? "실시간 · 5초마다 (멈추기)" : "멈춤 (실시간으로)"}
        </button>
        {" · "}
        <button className="lnk" onClick={() => void load(key, token)}>지금 다시 세기</button>
        {" · "}
        <button className="lnk" onClick={() => {
          // 쪽지는 서버에서도 지웁니다 — 브라우저에서만 지우면
          // 그 쪽지는 하루 동안 살아 있습니다.
          if (token) {
            void fetch(BASE + "/v1/admin/logout",
                       { method: "POST", headers: head("", token) });
          }
          try {
            localStorage.removeItem(KEY);
            localStorage.removeItem(TOK);
          } catch { /* */ }
          setKey("");
          setToken("");
          setData(null);
        }}>나가기</button>
      </p>

      {/* ── 돈 ───────────────────────────────────────── */}
      <section>
        <h2>돈</h2>
        <div className="kpi">
          <div><b>{sales ? won(sales.revenue) : "—"}</b><span>총 매출</span></div>
          <div><b>{sales ? won(sales.revenue_today) : "—"}</b><span>오늘</span></div>
          <div><b>{sales?.paid ?? "—"}</b><span>치른 건</span></div>
          <div><b>{sales?.paid_today ?? "—"}</b><span>오늘 치른 건</span></div>
          {/* ★ 없는 값은 0원으로 적지 않습니다. 치른 건이 없으면
              평균도 없습니다 — 시주를 열두 시로 채우지 않는 것과 같소. */}
          <div><b>{sales?.avg_order == null ? "—" : won(sales.avg_order)}</b>
               <span>건당 평균</span></div>
          <div><b>{sales?.close_rate == null ? "—" : sales.close_rate + "%"}</b>
               <span>주문 → 결제</span></div>
          <div><b>{sales?.pending ?? "—"}</b><span>값만 매기고 안 치른 건</span></div>
          <div><b>{sales?.refunded ?? "—"}</b><span>환불</span></div>
        </div>
        {/*
          ★ 여기가 **늘 0원**이었습니다 (2026-09-03).

            주문에 적는 상태는 우리 말(`pending`/`paid`/`canceled`)인데,
            매출 셈이 토스의 말(`{"DONE"}`)과 견주고 있었습니다. 두
            어휘가 한 번도 안 겹쳐서 19,900원을 치러도 총 매출 0원이
            떴습니다. `payments.ORDER_*` 로 갈랐고
            `tests/test_admin_sales.py` 가 지킵니다.
        */}
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

      {/* ── 막힌 자리 ────────────────────────────────── */}
      {/*
        ★ 주인이 화면을 열고 가장 먼저 묻는 것은 「지금 뭐 터진 거
          없소?」 입니다. 그런데 여기엔 매출과 이탈만 있었고 **막힌
          자리를 볼 데가 없었습니다.** 매출 위에 두지 않고 바로
          아래에 둡니다 — 돈보다 먼저 볼 것은 아니지만, 돈을 보고
          이상하면 곧바로 여기를 봐야 하니까요.
      */}
      <section>
        <h2>막힌 자리</h2>
        {!trouble ? (
          <p className="sm">서버가 아직 이 자리를 안 내주오.</p>
        ) : (
          <>
            <p className={trouble.enabled ? "sm" : "admbad"}>
              <b>결제 문</b> — {trouble.gate}
            </p>
            <div className="kpi">
              <div><b>{trouble.pay_start ?? "—"}</b><span>결제창까지 간 수</span></div>
              <div><b>{trouble.pay_fail ?? "—"}</b><span>깨진 수</span></div>
              <div><b>{trouble.fail_rate == null ? "—" : trouble.fail_rate + "%"}</b>
                   <span>깨진 비율</span></div>
              <div><b>{trouble.stale_pending_all}</b><span>안 치른 주문</span></div>
              <div><b>{trouble.canceled_all}</b><span>물린 주문</span></div>
            </div>

            {trouble.fail_rate != null && trouble.fail_rate >= 10 && (
              <p className="admbad">
                <b>결제가 {trouble.fail_rate}% 깨지고 있소.</b> 열에 하나가
                넘으면 손님 탓이 아니오 — PG 키 · 승인 주소(successUrl) ·
                금액 불일치를 먼저 보시오.
              </p>
            )}

            {trouble.stale_pending.length > 0 && (
              <>
                <p className="sm">
                  값만 매겨 놓고 안 치른 주문. 결제창에서 물러선 자리요 —
                  오래 묵은 것부터 보이오.
                </p>
                <table className="admt">
                  <thead>
                    <tr><th>주문</th><th>상품</th><th className="n">값</th>
                        <th className="n">지난 시간</th></tr>
                  </thead>
                  <tbody>
                    {trouble.stale_pending.map((o) => (
                      <tr key={o.order_id}>
                        <td className="mono">{o.order_id}</td>
                        <td>{o.tier ?? "—"} · {o.lens_id ?? "—"}</td>
                        <td className="n">{won(o.amount)}</td>
                        <td className="n">
                          {o.age_min == null ? "모르오"
                            : o.age_min < 60 ? `${o.age_min}분`
                            : `${Math.floor(o.age_min / 60)}시간`}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </>
            )}

            {trouble.canceled.length > 0 && (
              <>
                <p className="sm">물린 주문 — 환불하거나 PG 에서 취소된 것.</p>
                <table className="admt">
                  <tbody>
                    {trouble.canceled.map((o) => (
                      <tr key={o.order_id}>
                        <td className="mono">{o.order_id}</td>
                        <td>{o.tier ?? "—"}</td>
                        <td className="n">{won(o.amount)}</td>
                        <td className="n">{o.pg_status ?? "—"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </>
            )}

            {trouble.stale_pending_all === 0 && trouble.canceled_all === 0
              && (trouble.pay_fail ?? 0) === 0 && (
              <p className="sm">막힌 자리가 없소.</p>
            )}
          </>
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
          /*
            ★ 「못 가져왔소」 한 줄은 **네트워크 실패**로 읽힙니다.
              실제로는 열쇠가 틀렸거나 서버가 그 자를 안 들고 있는
              것이라, 무엇을 해야 하는지까지 적습니다.
          */
          <p className="sm">
            점수를 못 가져왔소. 열쇠가 맞는지 보시고, 그래도 안 오면
            그 서버에 <b>화면 소스가 없는 것</b>이오 —
            {" "}<code>.\dev.ps1 api</code> 로 띄운 로컬에서 보시오.
          </p>
        ) : drama.summary.source === "none" || !drama.summary.has_source ? (
          /*
            ★ 여기가 **가장 나쁜 자리**였습니다.

              배포본(fly)에는 `apps/web` 이 없어서 27화면 중 엔진이
              짓는 6화면만 잡힙니다. 그런데 화면은 그걸 그대로 그려
              「합 63」 이라고 띄웠습니다. 반쪽짜리 숫자가 멀쩡한
              점수처럼 보이면, 그걸 보고 고칠 자리를 정합니다.

              서버는 `has_source` 로 이미 말하고 있었습니다.
              화면이 안 읽고 있었을 뿐입니다.
          */
          <div className="admbad">
            <p>
              <b>이 서버에서는 연출 점수를 못 재오.</b>
            </p>
            <p className="sm">
              점수는 화면 글을 <b>소스째 읽어서</b> 셉니다. 배포
              이미지에는 <code>apps/web</code> 이 안 들어가서, 스물일곱
              화면 중 엔진이 짓는 {drama.summary.screens}개만 잡히오.
              반쪽으로 낸 숫자는 멀쩡한 점수처럼 보여 더 나쁘니
              안 냅니다.
            </p>
            <p className="sm">
              로컬에서 보시오 — <code>.\dev.ps1 api</code> 로 띄우고
              열쇠를 넣거나, <code>.\dev.ps1 drama --why</code> 를
              돌리면 같은 숫자가 나오오.
            </p>
          </div>
        ) : (
          <>
            {/*
              ★ 배포본은 소스가 없어 **찍어 둔 글**(seed/screen_text.json)
                로 잽니다. 숫자는 같되 낡을 수 있으니, 언제 찍은 것인지를
                숫자 위에 적습니다. 그래야 「고쳤는데 안 움직인다」 를
                버그가 아니라 「다시 찍어야 한다」 로 읽습니다.
            */}
            {drama.summary.source === "snapshot" && (
              <p className="sm">
                이 서버에는 화면 소스가 없어 <b>찍어 둔 글</b>로 쟀소
                {drama.summary.snapshot_at
                  ? ` (${drama.summary.snapshot_at.replace("T", " ")} 에 찍음)`
                  : ""}.
                글을 고쳤으면 <code>.\dev.ps1 drama</code> 를 돌려 다시 찍고
                배포하시오.
              </p>
            )}
            <div className="kpi">
              <div><b>{drama.summary.pull}</b><span>당김</span></div>
              <div><b>{drama.summary.bite}</b><span>팩폭</span></div>
              <div><b>{drama.summary.heart}</b><span>울림</span></div>
              <div><b>{drama.summary.clear}</b><span>명확</span></div>
              <div><b>{drama.summary.plain}</b><span>쉬움</span></div>
              <div><b>{drama.summary.figure}</b><span>비유</span></div>
              <div><b>{drama.summary.measure}</b><span>줄길이</span></div>
              <div><b>{drama.summary.pace}</b><span>읽기속도</span></div>
              <div><b>{drama.summary.total}</b><span>합 (화면 {drama.summary.screens})</span></div>
            </div>
            {(drama.summary.pull ?? 100) < 60 && (
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
                  <th className="n">울림</th><th className="n">명확</th>
                  <th className="n">쉬움</th><th className="n">비유</th>
                  <th className="n">줄길이</th><th className="n">읽기속도</th>
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
                    <td className="n">{r.heart}</td>
                    <td className="n">{r.clear}</td>
                    <td className="n">{r.plain}</td>
                    <td className="n">{r.figure}</td>
                    <td className="n">{r.measure}</td>
                    {/* 읽는 데 걸리는 시간을 함께 냅니다 — 점수만으로는
                        「길다」 가 얼마나 긴지 모릅니다. */}
                    <td className="n" title={`읽는 데 약 ${Math.round(r.secs / 60)}분`}>
                      {r.pace}
                    </td>
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

      {/* ★ 에셋 현황 — 무엇이 아직 없는가.
          장면·캐릭터·신살 인물은 파일이 있으면 쓰고 없으면 자리표시로
          버팁니다. 좋은 구조인데, 그 대가로 **없는 것이 화면에서 티가
          안 납니다.** 여기서 한눈에 봅니다. */}
      <AssetBoard />
    </main>
  );
}
