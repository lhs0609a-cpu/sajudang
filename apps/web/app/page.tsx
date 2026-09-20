"use client";
/**
 * 진입부 — A1~A7 (docs/45).
 *
 * ★ 이 파일이 스스로 화면을 밝히지 않아 `.\dev.ps1 screens` 가
 *   「구현이 확인되지 않은 화면」으로 여덟 칸을 잡고 있었습니다.
 *   화면 글을 EntryFlow 로 옮기면서 태그가 같이 안 따라왔습니다.
 *
 * @screen a1 a2 a3 a4 a4b a5 a6 a7
 */

import { Suspense, useEffect, useRef, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Shell from "@/components/Shell";
import EntryFlow, { type EntryStep } from "@/components/EntryFlow";
import { Narration } from "@/components/Narration";
import { api, ApiError } from "@/lib/api";
import { birthMessageFrom, birthProblem } from "@/lib/birth";
import { needsGuardian } from "@/lib/biz";
import { useSession } from "@/lib/store";
import { track, useScreen } from "@/lib/track";
import { exposeEntry } from "@/lib/experiment";
import type { HookSegment } from "@shared/chart";

type Step = EntryStep;
const STEPS: Step[] = ["a1", "a5", "a3", "a4", "a4b", "a6", "a7", "a2"];

function EntryInner() {

  const router = useRouter();
  const params = useSearchParams();
  const s = useSession();
  const activeIdentity = `${s.chartId}:${s.concern}:${s.cur}:${s.name}`;
  const identityRef = useRef(activeIdentity);
  identityRef.current = activeIdentity;
  const chartRequest = useRef(0);
  useEffect(() => () => { chartRequest.current++; }, []);

  const asked = params.get("step") as Step | null;
  const [step, setStep] = useState<Step>(
    asked && STEPS.includes(asked) ? asked : "a1");

  const [trail, setTrail] = useState<Step[]>([]);

  useEffect(() => {
    if (asked && STEPS.includes(asked)) {
      setStep(asked);
      setError(null);
    } else if (!asked) {
      setStep("a1");
      setTrail([]);
    }
  }, [asked]);

  const go = (next: Step) => {
    setError(null);
    setTrail((t) => [...t, step]);
    setStep(next);

    router.replace("/?step=" + next, { scroll: false });
  };
  const back = trail.length
    ? () => {
        setTrail((t) => t.slice(0, -1));
        setStep(trail[trail.length - 1]);
        router.replace("/?step=" + trail[trail.length - 1], { scroll: false });
      }
    : undefined;
  const [busy, setBusy] = useState(false);

  const [error, setError] = useState<string | null>(null);
  const [hookRetry, setHookRetry] = useState(0);
  const [segments, setSegments] = useState<HookSegment[] | null>(null);
  const [hookDone, setHookDone] = useState(false);

  const [misses, setMisses] = useState(0);
  const [turned, setTurned] = useState(false);
  useEffect(() => {
    setSegments(null);setHookDone(false);setMisses(0);setTurned(false);
  }, [s.chartId,s.concern,s.cur,s.name]);

  useScreen(step);
  useEffect(() => { if (step === "a1") exposeEntry(); }, [step]);

  const buildChart = async () => {

    const { year, month, day } = s;
    const problem = birthProblem(year, month, day);
    if (problem) { setError(problem); return; }
    if (!s.sexSet) { setError("여성·남성 중 하나를 선택해 주시오. 대운이 앞으로 가는지 뒤로 가는지가 그것으로 갈리오."); return; }
    if (s.hourKnown && s.hour === null) { setError("태어난 시간을 입력하거나 시간 모름을 선택해 주세요."); return; }
    if (year === null || month === null || day === null) {
      setError("날을 다 적어야 명식을 세우오.");
      return;
    }

    if (needsGuardian(year, month, day)) {
      setError(
        "만 열네 살이 안 되었소. 그 나이에는 부모님 동의가 있어야 "
        + "생년월일을 받을 수 있소 — 법이 그러하오. 어른과 함께 오시오."
      );
      return;
    }
    setBusy(true);
    setError(null);
    const requestId = ++chartRequest.current;
    const inputKey = JSON.stringify([year, month, day, s.hour, s.minute, s.hourKnown, s.sex, s.city]);
    try {
      const res = await api.chart({
        year, month, day,
        hour: s.hourKnown ? s.hour : null,
        minute: s.hourKnown ? s.minute : null,
        hour_known: s.hourKnown,
        sex: s.sex, birth_city: s.city,
      });
      const latest = useSession.getState();
      if (requestId !== chartRequest.current || inputKey !== JSON.stringify([latest.year, latest.month, latest.day, latest.hour, latest.minute, latest.hourKnown, latest.sex, latest.city])) return;
      s.set({ chartId: res.chart_id, features: res.features,
              rarity: res.rarity ?? null,
              divergence: res.divergence ?? null });
    } catch (e) {
      if (requestId !== chartRequest.current) return;

      const raw = e instanceof ApiError ? e.message : "";
      setError(e instanceof ApiError && e.status < 500
        ? (birthMessageFrom(raw) ?? raw)
        : "계산 서버에 연결하지 못했소. 입력은 그대로 남아 있으니 잠시 후 다시 계산해 주시오.");
    } finally {
      if (requestId === chartRequest.current) setBusy(false);
    }
  };

  useEffect(() => {
    if (step !== "a6" || s.features || busy) return;

    const bad = birthProblem(s.year, s.month, s.day);
    if (bad) { setError(bad); return; }
    void buildChart();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [step]);

  useEffect(() => {
    if (step === "a6" && s.features) {
      track("chart_completed", "a6");
    }
  }, [step, s.features]);

  useEffect(() => {
    if (step !== "a7" || !s.chartId || segments) return;
    let alive = true;
    const previousMisses = s.hookReview?.edition === "entry3" && s.hookReview.chartId === s.chartId && s.hookReview.concern === s.concern && s.hookReview.lensId === s.cur
      ? Object.values(s.hookReview.answers).filter(answer => answer === false).length : 0;
    if (previousMisses > misses) setMisses(previousMisses);
    api.hook({
      edition: "entry2",
      chart_id: s.chartId, concern: s.concern, axis4: s.axis4,
      name: s.name, lens_id: s.cur,
      misses: Math.max(misses, s.hookReview?.edition === "entry3" && s.hookReview.chartId === s.chartId && s.hookReview.concern === s.concern && s.hookReview.lensId === s.cur
        ? Object.values(s.hookReview.answers).filter(answer=>answer===false).length : 0),
    })
      .then((r) => alive && setSegments(r.segments))
      .catch((e) => alive && setError(e instanceof ApiError ? e.message : "훅을 만들지 못했소."));
    return () => { alive = false; };
  }, [step, s.chartId, s.concern, s.axis4, s.name, s.cur, segments, misses, hookRetry]);

  const onMiss = (n: number) => {
    if (n !== 1 || turned) return;
    setTurned(true);
    setMisses(n);
    if (!s.chartId) return;
    const startedFor = activeIdentity;
    api.hook({
      edition: "entry2",
      chart_id: s.chartId, concern: s.concern, axis4: s.axis4,
      name: s.name, lens_id: s.cur, misses: n,
    })
      // ★ **이미 읽은 장은 갈아 끼우지 않습니다.** 셈(0)과 방금 아니라고
      //   답한 장면(1)은 그대로 두고, 그 뒤부터 축을 바꿉니다. 본 글이
      //   몰래 바뀌면 손님은 자기가 무엇에 아니라고 했는지 알 수 없습니다.
      .then((r) => { if (startedFor === identityRef.current) setSegments((prev) =>
        prev ? prev.map((seg, i) => (i <= 1 ? seg : r.segments[i] ?? seg)) : r.segments); })
      .catch(() => {  });
  };

  return <EntryFlow step={step} go={go} back={back} error={error} busy={busy}
    calculate={() => void buildChart()} segments={segments} done={hookDone}
    onDone={() => setHookDone(true)} onMiss={() => onMiss(1)} misses={misses}
    retry={() => { setError(null); setHookRetry(n => n + 1); }} />;
}

export default function EntryPage() {
  return (
    <Suspense fallback={<Shell bare><Narration lines={["대문을 여는 중이오."]} /></Shell>}>
      <EntryInner />
    </Suspense>
  );
}
