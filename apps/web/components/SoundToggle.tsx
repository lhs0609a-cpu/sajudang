"use client";

/**
 * 소리 끄기 — 상단바에 한 칸.
 *
 * ★ 기본은 **켜짐**입니다 (2026-09-07 에 뒤집었습니다).
 *
 *   손님이 시킨 것 — "애니메이션에 있는 소리는 (…) 전부 다 켜줘
 *   기본값이, 처음이나 아니면 상단 플로우에 소리끄기 버튼 하나
 *   만들고".
 *
 *   그 전까지는 기본이 꺼짐이었고, 게다가 **스위치 하나에 기본값이
 *   둘**이었습니다 — 배경음은 꺼짐, 영상 소리는 켜짐. 그래서 이
 *   버튼이 「꺼짐」을 그리고 있는데 영상은 소리를 내는 일이 생겼고,
 *   손님은 무엇이 켜져 있는지 알 수가 없었습니다. 이제 한 벌입니다.
 *
 * ★ 그래도 갑자기 나지는 않습니다
 *
 *   브라우저가 손짓 없는 소리를 막습니다. 첫 화면은 조용하고, 손님이
 *   처음 화면을 건드리는 순간 열립니다 (`sound.resumeOnGesture`).
 *   회사·지하철에서 연 사람은 그때 이걸 누르면 되고, 끈 것은 그
 *   기기에 남습니다.
 *
 * ★ 처음 온 사람에게 한 번만 알립니다.
 *   소리가 난다는 것과 **끌 데가 여기라는 것**을 같이 알려야 합니다.
 *   첫 방문에만 작게 붙였다가, 한 번 누르면 다시 안 붙습니다.
 *
 * ★ 첫 그림은 「켜짐」으로 시작합니다.
 *   그게 처음 오는 사람의 값이라 서버가 그린 것과 같습니다. 끈 사람만
 *   한 번 깜빡입니다 — `localStorage` 는 브라우저에만 있어서 서버는
 *   그 사람이 껐는지 알 길이 없습니다.
 */
import { useEffect, useState } from "react";
import { onSoundChange, soundState, toggleSound } from "@/lib/sound";

const HINT = "sd.sound.hint";

export default function SoundToggle() {
  const [on, setOn] = useState(true);
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
      {/* 켜져 있는 사람에게는 **끌 데**를 알려 줍니다. 껐다 켜려는
          사람에게는 켤 데를요. */}
      {hint && <i className="sndhint">{on ? "소리 끄기" : "소리 켜기"}</i>}
    </button>
  );
}
