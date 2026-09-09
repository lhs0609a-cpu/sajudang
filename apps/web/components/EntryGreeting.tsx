"use client";

import { useEffect, useRef, useState } from "react";
import CharArt from "./CharArt";
import { LENS_BY_ID } from "@/lib/lenses";
import { ENTRY_MEDIA } from "@/lib/entry-media";
import { enableSound, onSoundChange, playBgm, setBgmDucked } from "@/lib/sound";

const SEEN = "sd.entry-greeting.v1";

/** Optional greeting: no automatic speech, forced wait, or substitute old portrait video. */
export default function EntryGreeting() {
  const video = useRef<HTMLVideoElement>(null);
  const audio = useRef<HTMLAudioElement | null>(null);
  const [playing, setPlaying] = useState(false);
  const [seen, setSeen] = useState(false);
  const [music, setMusic] = useState(false);
  const [error, setError] = useState("");
  const ready = !!(ENTRY_MEDIA.video && ENTRY_MEDIA.voice);
  const active = useRef(false);

  function finish() {
    active.current = false;
    audio.current?.pause();
    video.current?.pause();
    setBgmDucked(false);
    setPlaying(false);
  }

  useEffect(() => {
    try { setSeen(sessionStorage.getItem(SEEN) === "1"); } catch {}
    const unsub = onSoundChange(state => {
      if (state === "off") { finish(); setMusic(false); }
    });
    const hide = () => { if (document.hidden) finish(); };
    document.addEventListener("visibilitychange", hide);
    return () => {
      active.current = false;
      audio.current?.pause();
      video.current?.pause();
      setBgmDucked(false);
      unsub();
      document.removeEventListener("visibilitychange", hide);
    };
  }, []);

  function start() {
    enableSound();
    playBgm("outside");
    setMusic(true);
    if (!ready || seen || !ENTRY_MEDIA.voice) return;
    setError("");
    active.current = true;
    const voice = new Audio(ENTRY_MEDIA.voice);
    voice.volume = 0.9;
    audio.current = voice;
    voice.onended = finish;
    voice.onerror = () => {
      finish(); setError("인사 소리를 불러오지 못했소. 글로 읽고 이어가시오.");
    };
    setBgmDucked(true);
    setPlaying(true);
    if (video.current && !window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      video.current.currentTime = 0;
      void video.current.play().catch(() => { /* The same portrait and caption remain. */ });
    }
    void voice.play().then(() => {
      if (!active.current) { voice.pause(); return; }
      setSeen(true);
      try { sessionStorage.setItem(SEEN, "1"); } catch {}
    }).catch(() => {
      finish(); setError("소리를 재생하지 못했소. 다시 누르거나 글로 이어가시오.");
    });
  }

  return <>
    <div className="entry-greeting-portrait">
      {ready ? <video ref={video} src={ENTRY_MEDIA.video!} poster="/char/pungun/bust.webp"
        muted playsInline preload="none" aria-label="풍운도령의 첫 인사" />
        : <CharArt lens={LENS_BY_ID.pungun} size="talk" />}
    </div>
    <div><p className="conversion-kicker">성신당 길잡이 · 풍운도령</p>
      <p>“{ENTRY_MEDIA.caption}”</p>
      <p className="conversion-note">첫 해석은 내가 맡겠소. 다른 관점이 궁금하면 스무 해석자 중에서 고르면 되오.</p>
      <div className="entry-greeting-actions">
        {playing ? <button type="button" onClick={finish}>인사 건너뛰기</button>
          : (!music || (ready && !seen)) && <button type="button" onClick={start}>
            {ready && !seen ? "목소리와 함께 인사 듣기" : "배경음 켜기"}
          </button>}
        {music && !playing && <span className="conversion-note">소리는 위쪽 ♪에서 끌 수 있소.</span>}
      </div>
      {error && <p role="status" className="conversion-note">{error}</p>}
    </div>
  </>;
}
