"use client";

/**
 * @screen f2 r1
 * F · 모으다 — f2 인장첩 / R · 남기다 — r1 후기
 */
import { Suspense, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Shell from "@/components/Shell";
import Scene from "@/components/scene/Scene";
import ActOut from "@/components/ActOut";
import { Narration, Say } from "@/components/Narration";
import { api, ApiError } from "@/lib/api";
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
        <Narration lines={["벽에 종이가 붙어 있다.", "검은 고양이가 그 아래 앉아 있다."]} />
        <Say who="도령" lens="pungun">
          대문 앞 방명록 같은 것이오. 다녀간 사람이 적고 간 말만 붙소.
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
          붙습니다. 대가를 주고받은 글은 싣지 않습니다.
        </p>

        {/*
          ★ 「그대의 말이 벽에 붙는다」 는 이미 참인 말입니다.
            몇 명이 읽는다거나, 남기면 무엇이 좋아진다는 말은 안 씁니다.
        */}
        <ActOut kind="남긴 물음" next={heard > 0 ? "남기다" : "스무 사람"}>
          {heard > 0 ? (
            <>
              여기 붙는 말은 <b>다음 사람이 읽소.</b><br />
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
            마지막으로 들은 자리에 남기겠습니다
          </button>
        ) : (
          <button className="btn mt" onClick={() => router.push("/lobby?tab=b2")}>
            스무 사람을 보겠습니다
          </button>
        )}
        <button className="btn gh" onClick={() => setTab("f2")}>인장첩으로</button>
      </Shell>
    );
  }

  return (
    <Shell screen="f2" title="인장첩">
      <Scene id="sealbook" />
      <Narration lines={["첩을 폈다.", "찍힌 인장은 " + s.seals.length + "개."]} />
      {/*
        ★ 첩이 무엇인지 한 번도 안 풀고 있었습니다.
          칸 스물이 그려져 있는데 「받은 인장 / 아직」 두 낱말뿐이라,
          이게 모으는 것인지 잠긴 것인지 알 수가 없었습니다.
      */}
      <Say who="도령" lens="pungun">
        칸은 스물이오. 도장 찍힌 칸만 다시 펼쳐지오 — 열쇠 꾸러미 같은 것이오.
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
        ★ 산 것을 되찾을 길이 없었습니다.
          로그인이 없어 자격이 이 브라우저의 난수(session_id)에 매여
          있습니다. 데이터를 지우거나 기기를 바꾸면 치른 값을 통째로
          잃었습니다 — 24,900원짜리를요. 주문번호는 결제 영수증과 승인
          문자에 남으니, 그걸로 되찾습니다.
      */}
      <div className="ask mt">
        <div className="lab">치른 것을 못 찾겠습니다?</div>
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
                  } catch (e) {
                    setSay(e instanceof ApiError ? e.message : "찾지 못했소.");
                  } finally {
                    setFinding(false);
                  }
                }}>
          {finding ? "찾는 중입니다" : "되찾겠습니다"}
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
        지운 정보는 되돌릴 수 없습니다. 생년월일시는 사주 계산 목적으로만 씁니다.
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
