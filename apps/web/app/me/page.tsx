"use client";

/**
 * @screen f2 r1
 * F · 모으다 — f2 인장첩 / R · 남기다 — r1 후기
 */
import { Suspense, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Shell from "@/components/Shell";
import RefundHistory from '@/components/RefundHistory';
import Scene from "@/components/scene/Scene";
import ActOut from "@/components/ActOut";
import { Narration, Say } from "@/components/Narration";
import { api, ApiError } from "@/lib/api";
import type { SubView } from "@/lib/api";
import { LENSES } from "@/lib/lenses";
import { useSession } from "@/lib/store";
import { useScreen } from "@/lib/track";

function MeInner() {
  const router = useRouter();
  const params = useSearchParams();
  const s = useSession();
  const asked = params.get("tab");
  const [tab, setTab] = useState<"f2" | "r1">(asked === "r1" ? "r1" : "f2");
  useEffect(() => { if (asked === "r1" || asked === "f2") setTab(asked); }, [asked]);

  /* 주문번호로 치른 것을 되찾는 자리. 로그인이 없어서 필요합니다. */
  const [oid, setOid] = useState("");
  const [finding, setFinding] = useState(false);
  const [say, setSay] = useState<string | null>(null);

  /*
   * 걸어 둔 카드 — 「한 달 듣기」.
   *
   * ★ 그만두는 길은 **시작한 길만큼 쉬워야** 합니다 (docs/11 §5).
   *   전화도 메일도 아니고 버튼 하나입니다. 그리고 자리를 감추지
   *   않습니다 — 찾기 어렵게 두면 안 둔 것과 같습니다.
   */
  const [sub, setSub] = useState<SubView | null>(null);
  const [subBusy, setSubBusy] = useState(false);
  const [subSay, setSubSay] = useState<string | null>(null);
  const [subError, setSubError] = useState(false);
  const [subRetry, setSubRetry] = useState(0);
  useEffect(() => {
    if (!s.sessionId) return;
    let alive = true;
    api.subStatus(s.sessionId)
      .then((r) => { if (alive) {setSub(r);setSubError(false);} })
      .catch(() => { if (alive) setSubError(true); });
    return () => { alive = false; };
  }, [s.sessionId, subRetry]);

  if (tab === "r1") {
    /*
     * ★ 이 화면은 「남길 수 있다」 고만 말하고 **남길 데가 없었습니다.**
     *
     *   고지 세 줄과 「인장첩으로」 버튼 하나가 전부였습니다(73자).
     *   인장을 받은 손님이 「후기를 남기겠습니다」 를 눌러 여기 오면,
     *   후기 칸이 아니라 **규칙 설명**을 만나고 되돌아갑니다.
     *   후기 칸은 여기가 아니라 그 사람의 마지막 자리(c6)에 있습니다.
     *
     * ★ 그리고 적힌 규칙이 틀렸습니다.
     *
     *   「결제하고 끝까지 읽은 분만 남길 수 있습니다」 — 아닙니다.
     *   후기는 끝까지 읽은 사람이면 남깁니다. 값을 치른 분에게만 붙는
     *   것은 **배지**입니다 (`routers/feedback.post_review` 가 주문을
     *   보고 verified 를 정합니다). 못 남긴다고 적어 두면 남길 사람을
     *   돌려보내는 셈입니다.
     */
    const heard = s.seals.length;
    const last = s.seals[s.seals.length - 1];
    return (
      <Shell screen="r1" title="다녀간 사람들" legal>
        <Scene id="wall" />
        <Narration lines={["벽에 종이가 붙어 있소.", "안내묘가 그 아래 앉아 있소."]} />
        <Say who="도령" lens="pungun">
          대문 앞 방명록 같은 것이오. 다녀간 사람이 적고 간 말만 붙소.
          {" "}여기 붙은 말은 다 한 사람이 한 마디씩 남긴 것이오.
          <br />
          {/*
            ★ 68점이던 자리. 「방명록이오」 한 줄이 전부라 **벽 앞에
              선 사람 얘기**가 없었습니다. 팩폭 60 · 비유 0.
              여기 적는 건 이 화면이 이미 세고 있는 수뿐입니다.
          */}
          그대가 여기 선 건 남의 말을 보러 온 것이 아니오. 제 말을
          남길지 말지 재러 온 것이오.
          <br />
          <b>도움이 된 말과 맞지 않았던 말을 함께 남겨도 좋소.</b>
          {" "}별점을 높게 줄 필요도, 억지로 쓸 필요도 없소.
          직접 읽으며 느낀 것만 적어 주시오.
          <br />
          벽에 붙는 몫은 20명이고, 붙는 것은 그중 그대가 끝까지
          들은 사람뿐이오. 1명만 들었어도 1명이 붙소.
          {" "}빈 자리는 비워 두오 — 벽에 안 붙은 종이는 <b>없는
          종이처럼</b> 굴어야지, 자리만 잡아 두면 그건 재촉이오.
        </Say>
        <p className="tx">
          그대가 끝까지 들은 자리는 <b>{heard}곳</b>이오.
          스무 사람 중 <b>{LENSES.length - heard}명</b>은 아직 한 마디도
          안 했소.
        </p>
        <span className="src">
          근거 · 찍힌 인장 {heard}개 — 인장은 그 사람의 마지막 자리를
          지나야 붙소
        </span>
        <p className="sm">
          후기는 여기서 안 받소. <b>그 사람의 마지막 자리</b>에서 받소 —
          다 읽고 인장을 받기 직전이오.
          &quot;결제 확인됨&quot; 배지는 값을 치르고 끝까지 읽은 분의 글에만
          붙소. 대가를 주고받은 글은 싣지 않소.
        </p>

        {/*
          ★ 「그대의 말이 벽에 붙는다」 는 이미 참인 말이오.
            몇 명이 읽는다거나, 남기면 무엇이 좋아진다는 말은 안 씁니다.
        */}
        <ActOut kind="남긴 물음" next={heard > 0 ? "남기다" : "스무 사람"}>
          {heard > 0 ? (
            <>
              여기 붙는 말은 다음 사람이 읽소.<br />
              {heard}곳을 끝까지 들으셨는데, <b>그중 어디가 남을 만했소?</b>
            </>
          ) : (
            <>
              벽은 아직 그대 쪽이 비어 있소. <b>한 사람도 끝까지 안 들었소.</b><br />
              스물 중 <b>누구부터</b> 들으시겠소?
            </>
          )}
        </ActOut>
        {heard > 0 ? (
          <button className="btn mt"
                  onClick={() => router.push("/report/" + last + "?tab=c6")}>
            마지막으로 들은 자리에 남기겠소
          </button>
        ) : (
          <button className="btn mt" onClick={() => router.push("/lobby?tab=b2")}>
            스무 사람을 보겠소
          </button>
        )}
        <button className="btn gh" onClick={() => setTab("f2")}>인장첩으로</button>
      </Shell>
    );
  }

  return (
    <Shell screen="f2" title="인장첩">
      <header className="editorial-heading"><p className="conversion-kicker">나의 서재</p><h1>다시 읽고 싶은 이야기를<br/>여기에 간직하오.</h1><p>구매한 해석과 남긴 인장, 열람 기록을 살펴보시오.</p></header>
      <RefundHistory sessionId={s.sessionId} />
      {subError && <div className="conversion-card" role="alert"><p>구독 상태를 확인하지 못했소. 구독이 없거나 해지됐다는 뜻은 아니오.</p><button className="btn gh" onClick={() => {setSubError(false);setSubRetry(n => n + 1);}}>구독 상태 다시 확인하기</button></div>}
      <Scene id="sealbook" />
      <Narration lines={["첩을 폈소.", "찍힌 인장은 " + s.seals.length + "개."]} />
      {/*
        ★ 첩이 무엇인지 한 번도 안 풀고 있었습니다.
          칸 스물이 그려져 있는데 「받은 인장 / 아직」 두 낱말뿐이라,
          이게 모으는 것인지 잠긴 것인지 알 수가 없었소.
      */}
      <Say who="도령" lens="pungun">
        칸은 스물이오. 도장 찍힌 칸만 다시 펼쳐지오 — 열쇠 꾸러미 같은 것이오.
        <br />
        {/*
          ★ 76점이던 자리. 울림 20 — 칸 20개와 수 둘이 전부라
            **첩을 든 사람 얘기**가 없었소. 모으는 자리는
            자칫 재촉이 되므로, 안 채워도 된다는 말을 함께 답니다.
        */}
        그대가 지나온 자리마다 하나씩 찍힌 것이오. 값을 치른 표가
        아니라 <b>끝까지 읽은 표</b>요 — 값 없이 듣고도 찍히오.
        <br />
        <b>빈 칸을 보고 채우고 싶어지셨소.</b> 스무 칸이 그려져
        있으면 사람은 다 채우려 드오. 그건 이 첩이 그렇게 생겨서지
        그대에게 스물이 필요해서가 아니오.
        {" "}부담스럽다면 이미 읽은 자리 하나만 다시 보아도 좋소.
        <br />
        칸 1개로 끝나도 되오. 두 칸이 붙어 있다고 둘째를 들어야 하는
        건 아니오 — 한 자리에 2명까지만 잇는 것도 그 때문이오.
          <br />
        {" "}한 개를 읽고 오늘 해볼 행동을 하나 골라도 충분하오.
        나머지 칸은 필요할 때 열어 보시오.
      </Say>
      <p className="tx">
        찬 칸이 <b>{s.seals.length}개</b>, 빈 칸이{" "}
        <b>{LENSES.length - s.seals.length}개</b>요.
      </p>
      <span className="src">
        근거 · 인장은 그 사람의 마지막 자리를 지나야 붙소 — 값과는 별개요
      </span>
      <div className="og c2">
        {LENSES.map((l) => {
          const got = s.seals.includes(l.id);
          return (
            <button
              key={l.id}
              className={"op " + (got ? "on" : "off")}
              disabled={!got}
              onClick={() => router.push("/report/" + l.id)}
            >
              <b style={{ color: got ? l.color : "var(--paper3)" }}>{got ? l.name : "○"}</b>
              <span>{got ? "받은 인장" : "아직"}</span>
            </button>
          );
        })}
      </div>
      {/*
        ══════════════════════════════════════════════════════
        걸어 둔 카드 — 「한 달 듣기」
        ══════════════════════════════════════════════════════

        ★ 그만두는 자리를 **감추지 않습니다.**
          정기결제에서 가장 흔한 어긋남이 이것입니다 — 거는 것은 버튼
          하나인데 그만두는 것은 메일이나 전화입니다. 그건 브레이크를
          없앤 것과 같습니다. 여기서는 거는 자리와 그만두는 자리가
          똑같이 버튼 하나입니다 (docs/11 §5).

        ★ 그만둬도 **이미 치른 달은 끝까지** 봅니다. 남은 날을 뺏는
          해지는 값을 치른 사람에게서 도로 가져가는 것입니다.
      */}
      {sub?.has && (
        <div className="ask mt">
          <div className="lab">달마다 듣고 계시오</div>
          <p className="sm">
            {sub.price.toLocaleString()}원 / 달
            {sub.card && <> · 카드 끝자리 <b>{sub.card}</b></>}
            {sub.months && sub.months > 1 && <> · {sub.months}달째</>}
          </p>
          {sub.ending ? (
            <>
              <p className="sm">
                그만두기를 눌러 두셨소. 더 안 빠져나가오 —{" "}
                <b>{(sub.period_end ?? "").slice(0, 10)}</b>까지는 그대로
                보시오.
              </p>
              <button className="btn mt" disabled={subBusy}
                      onClick={async () => {
                        setSubBusy(true); setSubSay(null);
                        try {
                          const r = await api.subResume({ session_id: s.sessionId });
                          setSub(r.sub); setSubSay(r.say);
                        } catch (e) {
                          setSubSay(e instanceof ApiError ? e.message : "무르지 못했소.");
                        } finally { setSubBusy(false); }
                      }}>
                {subBusy ? "무르는 중이오" : "계속 듣겠소"}
              </button>
            </>
          ) : (
            <>
              <p className="sm">
                다음은 <b>{(sub.next_charge ?? "").slice(0, 10)}</b>이오.
                그 뒤로도 서른 날마다요.
              </p>
              {/*
                ★ 그만두기가 유령 버튼이 아닙니다. 누르면 그 자리에서
                  끝납니다 — 「나중에」처럼 레이블과 결과가 어긋나지
                  않게, 무슨 일이 일어나는지 버튼 위에 적어 둡니다.
              */}
              <button className="btn gh mt" disabled={subBusy}
                      onClick={async () => {
                        setSubBusy(true); setSubSay(null);
                        try {
                          const r = await api.subCancel({ session_id: s.sessionId });
                          setSub(r.sub); setSubSay(r.say);
                        } catch (e) {
                          setSubSay(e instanceof ApiError ? e.message : "그만두지 못했소.");
                        } finally { setSubBusy(false); }
                      }}>
                {subBusy ? "그만두는 중이오" : "그만두겠소"}
              </button>
            </>
          )}
          {sub.fails ? (
            <p className="sm">
              카드에서 값이 안 걷혔소 ({sub.fails}번). 사흘은 그대로
              열어 두오 — 그 안에 카드를 다시 걸어 주시오.
            </p>
          ) : null}
          {subSay && <p className="sm mt">{subSay}</p>}
        </div>
      )}

      {/*
        ★ 산 것을 되찾을 길이 없었소.
          로그인이 없어 자격이 이 브라우저의 난수(session_id)에 매여
          있소. 데이터를 지우거나 기기를 바꾸면 치른 값을 통째로
          잃었소 — 99,000원짜리를요. 주문번호는 결제 영수증과 승인
          문자에 남으니, 그걸로 되찾습니다.

        ★ 달삯은 되찾을 때 **주인도 함께 옮깁니다.** 안 옮기면 다음
          달 청구가 옛 브라우저로 가서, 돈은 나가는데 여기서는 안
          열립니다.
      */}
      <div className="ask mt">
        <div className="lab">치른 것을 못 찾겠소?</div>
        <p className="sm">
          기기를 바꾸셨거나 이 브라우저를 비우셨으면 여기서 되찾으시오.
          <b>주문번호</b>는 결제 영수증과 승인 문자에 적혀 있소.
        </p>
        <input className="fld" placeholder="sjd_… 로 시작하는 주문번호"
               value={oid} maxLength={64}
               onChange={(e) => { setOid(e.target.value.trim()); setSay(null); }} />
        <button className="btn mt" disabled={oid.length < 4 || finding}
                onClick={async () => {
                  setFinding(true);
                  setSay(null);
                  try {
                    const r = await api.payRestore({
                      session_id: s.sessionId, order_id: oid });
                    if (r.lens_id && !s.seals.includes(r.lens_id)) {
                      s.set({ seals: [...s.seals, r.lens_id] });
                    }
                    s.set({ tier: r.tier as typeof s.tier, paid: true });
                    setSay(r.say);
                    /*
                     * ★ 달삯이면 **주인까지** 옮깁니다.
                     *   주문만 옮기면 이 기기에서 보이기는 하는데 다음
                     *   달 청구는 옛 브라우저로 갑니다. 돈은 나가고
                     *   자격은 안 오는 자리가 됩니다.
                     */
                    if (r.tier === "sub") {
                      try {
                        const sr = await api.subRestore({
                          session_id: s.sessionId, order_id: oid });
                        setSub(sr.sub);
                        setSay(sr.say);
                      } catch {
                        setSay("치른 것은 찾았소만, 걸어 두신 카드는 못 찾았소. "
                               + "다음 달은 다시 걸어 주시오.");
                      }
                    }
                  } catch (e) {
                    setSay(e instanceof ApiError ? e.message : "찾지 못했소.");
                  } finally {
                    setFinding(false);
                  }
                }}>
          {finding ? "찾는 중이오" : "되찾겠소"}
        </button>
        {say && <p className="sm mt">{say}</p>}
      </div>

      {/*
        ★ 첩이 그냥 끝나고 있었습니다. 빈 칸이 몇인지는 이미 참인 말이고,
          그걸 말하는 것만으로 다음이 생깁니다 — 안 끝난 일이 오래 남습니다.
      */}
      <ActOut kind="끊긴 동작"
              next={s.seals.length < LENSES.length ? "스무 사람" : "이어지다"}>
        {s.seals.length < LENSES.length ? (
          <>
            빈 칸 <b>{LENSES.length - s.seals.length}개</b>는 아직 한 마디도
            안 들은 자리요.<br />
            다만 <b>오늘 앉을 수 있는 자리는 둘</b>이오. 다 채우는 첩이 아니오.
          </>
        ) : (
          <>스무 칸이 다 찼소. <b>같은 여덟 글자를 스무 번 본 셈이오.</b></>
        )}
      </ActOut>
      {/* ★ 「후기를 남기겠습니다」 였는데 정작 그 화면은 후기를 안 받습니다.
            레이블과 결과가 어긋나면 손님은 속았다고 느낍니다. 표지판으로. */}
      <button className="btn gh mt" onClick={() => setTab("r1")}>다녀간 사람들</button>
      <button className="btn gh" onClick={() => router.push("/lobby")}>진열대로</button>
      <button className="btn gh" onClick={() => { s.reset(); router.push("/"); }}>
        처음부터 다시
      </button>
      <p className="sm mt">
        지운 정보는 되돌릴 수 없소. 생년월일시는 사주 계산 목적으로만 쓰오.
      </p>
    </Shell>
  );
}

export default function MePage() {
  useScreen("me");
  return (
    <Suspense fallback={<Shell title="인장첩"><p className="sm">…</p></Shell>}>
      <MeInner />
    </Suspense>
  );
}
