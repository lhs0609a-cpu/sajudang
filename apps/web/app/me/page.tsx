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
import { LENSES } from "@/lib/lenses";
import { useSession } from "@/lib/store";

function MeInner() {
  const router = useRouter();
  const params = useSearchParams();
  const s = useSession();
  const asked = params.get("tab");
  const [tab, setTab] = useState<"f2" | "r1">(asked === "r1" ? "r1" : "f2");
  useEffect(() => { if (asked === "r1" || asked === "f2") setTab(asked); }, [asked]);

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
          <Say who="도령">아직 남기실 자리가 없소. 한 사람이라도 끝까지 들어보시오.</Say>
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
  return (
    <Suspense fallback={<Shell title="인장첩"><p className="sm">…</p></Shell>}>
      <MeInner />
    </Suspense>
  );
}
