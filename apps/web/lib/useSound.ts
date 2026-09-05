"use client";

/**
 * 영상이 소리를 낼 것인가 — 화면이 구독하는 자리.
 *
 * ★ 소리는 **스위치 한 벌**을 봅니다 (상단바의 ♪).
 *   영상마다 따로 두면 하나는 나고 하나는 안 나서, 손님은 무엇을
 *   껐는지 모릅니다.
 *
 * ★ 서버에서 그릴 때는 꺼진 것으로 봅니다.
 *   `localStorage` 는 브라우저에만 있습니다. 서버와 브라우저의 첫
 *   그림이 다르면 리액트가 어긋났다고 합니다.
 */
import { useEffect, useState } from "react";

import { onSoundChange, videoSoundOn } from "@/lib/sound";

export function useSoundOn(): boolean {
  const [on, setOn] = useState(false);
  useEffect(() => {
    setOn(videoSoundOn());
    return onSoundChange(() => setOn(videoSoundOn()));
  }, []);
  return on;
}

/**
 * 영상을 튼다. 소리가 막히면 **조용히 물러서서** 그림만 돌린다.
 *
 * 브라우저는 손짓 없는 소리를 막습니다. 막힌 채로 두면 그림까지
 * 멈춰서 화면이 정지 사진이 됩니다 — 그건 못 씁니다.
 */
export function playSafely(v: HTMLVideoElement | null, wantSound: boolean) {
  if (!v) return;
  v.muted = !wantSound;
  v.play().catch(() => {
    if (wantSound) {
      v.muted = true;
      v.play().catch(() => { /* 그래도 안 되면 포스터가 남습니다 */ });
    }
  });
}
