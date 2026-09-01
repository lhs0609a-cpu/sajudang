"use client";

/**
 * 소리 켜고 끄기 — 상단바에 한 칸.
 *
 * ★ 기본은 꺼짐입니다.
 *   사주를 보는 사람은 회사·지하철·자기 전 침대인 경우가 많습니다.
 *   갑자기 소리가 나면 그 자리에서 창을 닫습니다. 게다가 브라우저가
 *   손짓 없는 소리를 막아서, 자동으로 켜 봐야 나지도 않습니다.
 *
 * ★ 처음 온 사람에게 한 번만 알립니다.
 *   꺼져 있는 줄 모르면 소리가 있다는 것도 모릅니다. 첫 방문에만
 *   작게 붙였다가, 한 번 누르면 다시 안 붙습니다.
 */
import { useEffect, useState } from "react";
import { onSoundChange, soundState, toggleSound } from "@/lib/sound";

const HINT = "sd.sound.hint";

export default function SoundToggle() {
  const [on, setOn] = useState(false);
  const [hint, setHint] = useState(false);

  useEffect(() => {
    setOn(soundState() === "on");
    try {
      setHint(!localStorage.getItem(HINT));
    } catch { /* 저장을 막아 둔 브라우저 */ }
    return onSoundChange((s) => setOn(s === "on"));
  }, []);

  return (
    <button
      className={`tb snd ${on ? "on" : ""}`}
      aria-label={on ? "소리 끄기" : "소리 켜기"}
      aria-pressed={on}
      onClick={() => {
        // ★ 손짓 안에서 불러야 브라우저가 소리를 허락합니다.
        toggleSound();
        setHint(false);
        try { localStorage.setItem(HINT, "1"); } catch { /* 못 남겨도 됨 */ }
      }}
    >
      {on ? "♪" : "♪̸"}
      {hint && !on && <i className="sndhint">소리</i>}
    </button>
  );
}
