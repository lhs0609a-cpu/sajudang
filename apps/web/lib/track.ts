"use client";

/**
 * 계측 — 어디서 나가는지 보려고 남깁니다.
 *
 * ★ 보내는 것은 이것뿐입니다
 *     익명 세션 열쇠 · 화면 이름 · 사건 이름 · 숫자 몇 개
 *
 *   이름·생년월일시·고을은 **절대** 실리지 않습니다. 이 파일에서 그 값을
 *   읽지 않습니다. 서버도 화이트리스트로 한 번 더 거릅니다 —
 *   막는 자리를 여기에만 두면 언젠가 샙니다.
 *
 * ★ chart_id 도 안 보냅니다.
 *   생년월일시 해시라서 같은 생일이면 같은 값이 나옵니다. 준식별자입니다.
 *
 * ★ 계측이 화면을 멈추게 하지 않습니다.
 *   실패는 전부 삼킵니다. 모아 두었다가 한 번에 보내고, 창을 닫을 때는
 *   sendBeacon 으로 흘려보냅니다.
 */
import { useEffect, useRef } from "react";
import { API_BASE } from "@/lib/api";

const SID_KEY = "sajudang-sid";
const FLUSH_MS = 4000;
const MAX_QUEUE = 40;

export type EventName =
  | "screen" | "hook_shown" | "hook_answer" | "free_shown" | "free_beat"
  | "tier_view" | "tier_pick" | "pay_start" | "pay_done" | "pay_fail"
  | "relay_take" | "relay_skip" | "share_click" | "share_land" | "drop_guess";

interface Ev {
  name: EventName;
  screen: string;
  sid: string;
  stage?: number;
  ms?: number;
  n?: number;
  yes?: number;
}

/** 브라우저가 만든 난수. 사람과 이어지지 않고, 지우면 끝납니다. */
function sid(): string {
  if (typeof window === "undefined") return "";
  try {
    let v = localStorage.getItem(SID_KEY);
    if (!v) {
      v = (crypto?.randomUUID?.() ?? String(Math.random()).slice(2))
        .replace(/-/g, "").slice(0, 32);
      localStorage.setItem(SID_KEY, v);
    }
    return v;
  } catch {
    return "";                    // 사생활 보호 모드 등 — 조용히 포기합니다
  }
}

let queue: Ev[] = [];
let timer: ReturnType<typeof setTimeout> | null = null;

/**
 * ★ 관리자는 세지 않습니다.
 *
 * 레일은 ?step= 으로 화면을 건너뜁니다. 그대로 세면 a4 를 안 거친
 * 사람이 a6 에 나타나 "직전대비 200%" 같은 숫자가 나옵니다. 실제로
 * 배포 직후 퍼널에 그 값이 찍혔습니다.
 *
 * 고치는 쪽이 자기 손으로 숫자를 망가뜨리게 두면, 그 숫자를 못 믿게
 * 되고 결국 안 보게 됩니다.
 */
function isAdmin(): boolean {
  try {
    const raw = localStorage.getItem("sajudang-session");
    return !!raw && JSON.parse(raw)?.state?.admin === true;
  } catch {
    return false;
  }
}

function send(batch: Ev[], beacon = false) {
  if (!batch.length || !API_BASE) return;
  const url = `${API_BASE}/v1/events`;
  const body = JSON.stringify({ events: batch });
  try {
    if (beacon && navigator.sendBeacon) {
      // 창이 닫히는 중에도 나갑니다. Content-Type 을 맞춰야 서버가 읽습니다.
      navigator.sendBeacon(url, new Blob([body], { type: "application/json" }));
      return;
    }
    void fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body,
      keepalive: true,
    }).catch(() => {});
  } catch {
    /* 계측 실패는 삼킵니다 */
  }
}

export function flush(beacon = false) {
  if (!queue.length) return;
  const batch = queue;
  queue = [];
  if (timer) { clearTimeout(timer); timer = null; }
  send(batch, beacon);
}

export function track(name: EventName, screen: string, extra?: Partial<Ev>) {
  /*
   * ★ 주인 화면은 안 셉니다.
   *
   *   주인이 화면을 훑는 것이 손님 퍼널에 섞이면, 어디서 나가는지를
   *   보려고 만든 숫자가 **주인의 발자국으로 오염**됩니다. 32개 화면을
   *   한 번 훑으면 도달률이 통째로 흔들립니다.
   */
  if (typeof window !== "undefined"
      && window.location.pathname.startsWith("/admin")) return;

  if (typeof window === "undefined") return;
  if (isAdmin()) return;               // 관리자 레일은 퍼널에 안 실린다
  const s = sid();
  if (!s) return;
  queue.push({ name, screen, sid: s, ...extra });
  if (queue.length >= MAX_QUEUE) { flush(); return; }
  if (!timer) timer = setTimeout(() => flush(), FLUSH_MS);
}

/* 창을 닫거나 탭을 옮길 때 남은 것을 흘려보냅니다 */
if (typeof window !== "undefined") {
  const bye = () => flush(true);
  window.addEventListener("pagehide", bye);
  document.addEventListener("visibilitychange", () => {
    if (document.visibilityState === "hidden") bye();
  });
}

/**
 * 화면에 닿았다 + 얼마나 머물렀다.
 *
 * 머문 시간이 있어야 "여기서 나갔다" 와 "여기서 오래 읽다 나갔다" 를
 * 가릅니다. 둘은 고치는 방법이 다릅니다.
 */
export function useScreen(screen: string) {
  const t0 = useRef(0);
  useEffect(() => {
    if (!screen) return;
    t0.current = Date.now();
    track("screen", screen);
    return () => {
      const ms = Date.now() - t0.current;
      if (ms > 250) track("drop_guess", screen, { ms });
    };
  }, [screen]);
}
