"use client";

/**
 * @screen f2 r1
 * F · 모으다 — f2 인장첩 / R · 남기다 — r1 후기
 */
import { Suspense, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Shell from "@/components/Shell";
import Scene from "@/components/scene/Scene";
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
    return (
      <Shell title="남기다" legal>
        <Scene id="wall" />
        <Narration lines={["벽에 종이가 붙어 있다.", "검은 고양이가 그 아래 앉아 있다."]} />
        <p className="sm">
          후기는 결제하고 끝까지 읽은 분만 남길 수 있습니다.
          &quot;결제 확인됨&quot; 배지는 그 경우에만 붙습니다.
          대가를 주고받은 글은 싣지 않습니다.
        </p>
        {s.seals.length === 0 && (
          <Say who="도령" lens="pungun">아직 남기실 자리가 없소. 한 사람이라도 끝까지 들어보시오.</Say>
        )}
        <button className="btn gh mt" onClick={() => setTab("f2")}>인장첩으로</button>
      </Shell>
    );
  }

  return (
    <Shell title="인장첩">
      <Scene id="sealbook" />
      <Narration lines={["첩을 폈다.", "찍힌 인장은 " + s.seals.length + "개."]} />
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
                  } catch (e) {
                    setSay(e instanceof ApiError ? e.message : "찾지 못했소.");
                  } finally {
                    setFinding(false);
                  }
                }}>
          {finding ? "찾는 중이오" : "되찾는다"}
        </button>
        {say && <p className="sm mt">{say}</p>}
      </div>

      <button className="btn gh mt" onClick={() => setTab("r1")}>후기를 남긴다</button>
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
