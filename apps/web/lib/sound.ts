/**
 * 소리 — 배경음(BGM)과 목소리.
 *
 * ★ 왜 이렇게 짰나
 *
 *   1. **소리는 기본 켜짐입니다** (2026-09-07 에 뒤집었습니다).
 *      장면이 스물여섯인데 소리가 꺼져 있으면 손님은 이 집에 소리가
 *      있다는 것조차 모릅니다. 그리고 스위치가 하나인데 기본값이
 *      둘(배경음 꺼짐 · 영상 켜짐)이면 ♪ 가 거짓말을 합니다.
 *
 *      그래도 **갑자기 나지는 않습니다.** 브라우저가 손짓 없는 소리를
 *      막아서, 첫 화면은 조용하고 손님이 처음 건드릴 때 열립니다.
 *      회사·지하철에서 연 사람은 그때 ♪ 를 누르면 됩니다 — 끈 것은
 *      그 기기에 남습니다.
 *
 *   2. **없어도 돌아갑니다.**
 *      파일이 아직 없는 자리가 대부분입니다(장면 에셋과 같은 사정).
 *      없으면 조용히 넘어갑니다 — 소리 때문에 화면이 멈추면 안 됩니다.
 *
 *   3. **고른 것은 기억합니다.**
 *      켠 사람에게 매번 묻지 않고, 끈 사람에게 매번 소리 내지 않습니다.
 *
 *   4. **배경음은 이어집니다.**
 *      화면을 옮길 때마다 처음부터 다시 나면 그게 더 거슬립니다.
 *      한 벌만 두고 화면이 바뀌어도 끊지 않습니다.
 *
 * ─────────────────────────────────────────────────────────────
 * ★ 무한반복 — `audio.loop = true` 로는 **안 됩니다**
 *
 *   배경음은 손님이 앉아 있는 내내 돕니다. 90초짜리면 한 시간에 마흔
 *   번 다시 돌고, 손님이 실제로 듣는 것은 「90초짜리 가락」이 아니라
 *   **이음새 마흔 번**입니다. 여기서 딸깍하면 그 소리만 남습니다.
 *
 *   그런데 `<audio loop>` 는 이음새를 못 맞춥니다. 두 가지 이유입니다.
 *
 *     ① **mp3 는 앞뒤에 없던 무음이 붙습니다.** 인코더가 프레임을
 *        1152 샘플로 끊느라 앞에 1,000샘플 남짓, 뒤에 그만큼을 채웁니다.
 *        원본이 아무리 이어져 있어도 mp3 로 굽는 순간 앞뒤에 0.05초쯤
 *        되는 침묵이 생깁니다. 돌 때마다 **0.1초씩 소리가 빕니다.**
 *
 *     ② **되도는 자리를 브라우저가 스케줄링합니다.** 끝에 닿아야
 *        처음으로 되돌리므로 한 박자 늦습니다. 기기마다 다르고,
 *        탭이 뒤에 있다 돌아오면 더 벌어집니다.
 *
 *   그래서 **받아서 풀어 놓고**(decodeAudioData) 직접 돌립니다.
 *   AudioBufferSourceNode 의 loop 는 샘플 단위라 한 톨도 안 빕니다.
 *
 * ★ 그래도 남는 것 — 원본의 끝과 처음이 다르면
 *
 *   샘플이 딱 붙어도 파형이 어긋나면 「툭」 하고 걸립니다. 그래서 푼
 *   뒤에 **세 손질**을 합니다. 이 순서라야 합니다.
 *
 *     1. 앞뒤 무음을 **깎습니다** (mp3 가 붙인 것).
 *        먼저 안 깎으면 다음 단계에서 침묵을 섞게 됩니다.
 *     2. 끝자락을 첫머리에 **겹칩니다** — 등출력(equal-power)으로.
 *        선형으로 섞으면 겹치는 동안 소리가 옴폭 꺼집니다.
 *     3. 그 결과를 **샘플 단위로** 돌립니다.
 *
 *   덕분에 **발주가 이음새를 못 맞춰 와도** 앱에서 이어집니다.
 *   (영상 쪽도 같은 손질을 합니다 — `tools/loop_seam.py`)
 *
 * ★ 켜기 전에는 **받지도 않습니다**
 *
 *   배경음을 켜는 손님은 소수입니다. 안 켤 사람에게 1MB 를 미리
 *   내려보내면 그건 첫 화면 값을 남한테 물리는 것입니다. 이름만
 *   적어 두었다가 **켜는 순간** 받습니다.
 *
 * ★ 못 하면 물러섭니다
 *
 *   Web Audio 가 없거나(아주 옛 브라우저) 푸는 데 실패하면 예전처럼
 *   `<audio loop>` 로 냅니다. 이음새는 거칠어도 **소리는 납니다.**
 * ─────────────────────────────────────────────────────────────
 *
 * ★ 파일 두는 곳
 *
 *      /audio/bgm/{이름}.mp3     배경음 — 이어 붙는 고리(loop)
 *      /audio/voice/{장면}.mp3   목소리 — 도령이 하는 말 한 마디
 *
 *   docs/10 에 발주 내용을 적어 둡니다.
 */

// api.ts 와 **같은** 기본값이어야 합니다. 다르면 소리만 딴 데를 봅니다.
const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";
const KEY = "sd.sound";       // 켬/끔 — 이 기기에만 남습니다
const VOL_BGM = 0.22;         // 배경음은 말보다 훨씬 아래로
const VOL_VOICE = 0.9;

/**
 * 이음새에 겹치는 길이(초).
 *
 * 짧으면 파형이 어긋난 자리가 그대로 드러나고, 길면 겹치는 동안
 * 가락이 두 겹으로 들립니다. 결만 있고 가락이 옅은 음(발주서가
 * 「가락보다 결」이라 적은 이유)에서는 1.5초가 안 들립니다.
 */
const SEAM = 1.5;

/** 켜고 끌 때 소리가 오르내리는 길이(초). 딸깍 소리를 없앱니다. */
const FADE = 0.8;

/** 이보다 작으면 무음으로 봅니다 (mp3 가 앞뒤에 붙이는 것). */
const SILENCE = 0.002;

type State = "on" | "off";

let voice: HTMLAudioElement | null = null;
let cur = "";                 // 지금 걸린 배경음 이름 (아직 안 났을 수도)
const missing = new Set<string>();   // 없는 것으로 확인된 파일
const listeners = new Set<(s: State) => void>();

/**
 * 소리가 켜져 있는가. **기본은 켜짐입니다.**
 *
 * ★ 왜 뒤집었나 (2026-09-07)
 *
 *   손님이 말했습니다 — "애니메이션에 있는 소리는 (…) 전부 다 켜줘
 *   기본값이". 그 전까지는 배경음이 기본 꺼짐, 영상 소리가 기본
 *   켜짐이라 **스위치 하나에 기본값이 둘**이었습니다. 그러면 상단바의
 *   ♪ 가 「꺼짐」을 그리고 있는데 영상은 소리를 내는 일이 생깁니다 —
 *   손님은 무엇이 켜져 있는지 알 수가 없습니다.
 *
 *   이제 한 벌입니다. 켜져 있고, ♪ 를 누르면 다 꺼집니다.
 *
 * ★ 갑자기 소리가 나지는 않습니다
 *
 *   브라우저가 손짓 없는 소리를 막습니다. 그래서 첫 화면은 조용하고,
 *   손님이 처음 화면을 건드리는 순간 열립니다 (`resumeOnGesture`).
 *   회사·지하철에서 연 사람이 놀랄 일은 없고, 그때 ♪ 를 누르면
 *   그 기기에 기억됩니다.
 *
 * ★ 서버에서도 「켜짐」으로 봅니다 — 처음 오는 사람의 값이 그것이라
 *   첫 그림이 브라우저와 같아집니다 (끈 사람만 한 번 깜빡입니다).
 */
export function soundState(): State {
  if (typeof window === "undefined") return "on";
  try {
    // 끈 적이 없으면 켭니다.
    return localStorage.getItem(KEY) === "off" ? "off" : "on";
  } catch {
    /* 저장을 막아 둔 브라우저. 처음 온 사람과 같이 봅니다. */
    return "on";
  }
}

/**
 * 영상이 소리를 낼 것인가.
 *
 * ★ 배경음과 **같은 스위치**이오 (2026-09-07).
 *   전에는 따로 봤는데, 기본값이 둘로 갈려 ♪ 가 거짓말을 했습니다.
 *   지금은 한 벌이라 ♪ 하나가 소리 전부를 말합니다.
 *
 * ★ 못 켜도 그림은 돕니다. 브라우저가 막으면 조용히 물러섭니다
 *   (`useSound.playSafely`).
 */
export function videoSoundOn(): boolean {
  if (typeof window === "undefined") return false;
  return soundState() === "on";
}

export function onSoundChange(fn: (s: State) => void) {
  listeners.add(fn);
  // 리액트의 정리 함수는 아무것도 안 돌려줘야 합니다 (delete 는 boolean)
  return () => { listeners.delete(fn); };
}

function tell(s: State) {
  listeners.forEach((f) => f(s));
}

function src(kind: "bgm" | "voice", name: string) {
  return `/audio/${kind}/${name}.mp3`;
}

/* ══════════════════════════════════════════════════════════════
   배경음 — 푼 소리를 샘플 단위로 돌린다
   ══════════════════════════════════════════════════════════════ */

type Ctor = typeof AudioContext;

let ac: AudioContext | null = null;
let acDead = false;           // Web Audio 가 없는 브라우저

/** 소리 상자. 손짓 안에서 처음 만들어야 브라우저가 허락합니다. */
function audioCtx(): AudioContext | null {
  if (acDead) return null;
  if (ac) return ac;
  if (typeof window === "undefined") return null;
  const w = window as unknown as {
    AudioContext?: Ctor; webkitAudioContext?: Ctor;
  };
  const C = w.AudioContext ?? w.webkitAudioContext;
  if (!C) { acDead = true; return null; }
  try {
    ac = new C();
  } catch {
    acDead = true;
    return null;
  }
  return ac;
}

/**
 * 손짓을 한 번 기다렸다 상자를 연다.
 *
 * ★ 소리를 켜 둔 채 다시 온 손님은 **손짓 없이** 화면부터 뜹니다.
 *   그때 만든 상자는 `suspended` 로 서 있고 `resume()` 도 안 먹습니다.
 *   기다렸다가 손님이 처음 화면을 건드릴 때 엽니다 — 안 그러면
 *   「켜 뒀는데 소리가 안 난다」가 됩니다.
 */
let waitingForGesture = false;

function resumeOnGesture(ctx: AudioContext) {
  if (waitingForGesture) return;
  waitingForGesture = true;
  const go = () => {
    waitingForGesture = false;
    off();
    if (soundState() === "on") void ctx.resume().catch(() => {});
  };
  const off = () => {
    window.removeEventListener("pointerdown", go);
    window.removeEventListener("keydown", go);
    window.removeEventListener("touchstart", go);
  };
  window.addEventListener("pointerdown", go, { once: true });
  window.addEventListener("keydown", go, { once: true });
  window.addEventListener("touchstart", go, { once: true });
}

/**
 * 앞뒤 무음을 깎는다 — mp3 인코더가 붙인 것.
 *
 * 겹치기 **전에** 해야 합니다. 안 깎고 겹치면 침묵을 섞게 되어
 * 이음새에서 소리가 옴폭 꺼집니다.
 */
function trimEnds(buf: AudioBuffer): [number, number] {
  const chans: Float32Array[] = [];
  for (let c = 0; c < buf.numberOfChannels; c++) chans.push(buf.getChannelData(c));
  const loud = (i: number) => {
    let m = 0;
    for (const ch of chans) { const v = Math.abs(ch[i]); if (v > m) m = v; }
    return m;
  };
  let a = 0;
  let b = buf.length - 1;
  while (a < b && loud(a) < SILENCE) a++;
  while (b > a && loud(b) < SILENCE) b--;
  return [a, b + 1];
}

/**
 * 끝자락을 첫머리에 겹쳐 **어디서 잘라도 안 걸리는** 소리로 만든다.
 *
 *   본문   src[F ‥ n-F-1]                      → out[0 ‥ n-2F-1]
 *   겹침   blend(src[n-F ‥ n-1], src[0 ‥ F-1]) → out[n-2F ‥ n-F-1]
 *
 *   · out 의 첫 샘플 = src[F]
 *   · 본문 끝 src[n-F-1] → 겹침 첫 ≈ src[n-F]     이어짐
 *   · 겹침 끝 ≈ src[F-1] → 다시 첫 샘플 src[F]     이어짐
 *
 * ★ 등출력(cos/sin)으로 섞습니다. 선형(1-t, t)으로 섞으면 서로 무관한
 *   두 소리가 가운데서 −3dB 꺼져 「숨 쉬는」 자리가 생깁니다.
 */
function seamless(ctx: AudioContext, buf: AudioBuffer,
                  from: number, to: number): AudioBuffer {
  const n = to - from;
  const F = Math.min(Math.round(SEAM * buf.sampleRate), Math.floor(n / 3));
  if (F < 64) {
    // 너무 짧아 겹칠 수가 없습니다. 자른 것만 돌려줍니다.
    const raw = ctx.createBuffer(buf.numberOfChannels, n, buf.sampleRate);
    for (let c = 0; c < buf.numberOfChannels; c++) {
      raw.getChannelData(c).set(buf.getChannelData(c).subarray(from, to));
    }
    return raw;
  }

  const out = ctx.createBuffer(buf.numberOfChannels, n - F, buf.sampleRate);
  for (let c = 0; c < buf.numberOfChannels; c++) {
    const s = buf.getChannelData(c);
    const d = out.getChannelData(c);
    d.set(s.subarray(from + F, from + n - F), 0);
    for (let i = 0; i < F; i++) {
      const t = (i + 1) / (F + 1);
      const a = Math.cos((t * Math.PI) / 2);   // 끝자락이 물러나고
      const b = Math.sin((t * Math.PI) / 2);   // 첫머리가 올라온다
      d[n - 2 * F + i] = s[from + n - F + i] * a + s[from + i] * b;
    }
  }
  return out;
}

/** 이름 → 손질 끝난 소리. 두 번 받지 않습니다. */
const loops = new Map<string, Promise<AudioBuffer | null>>();

function loadLoop(ctx: AudioContext, name: string): Promise<AudioBuffer | null> {
  const hit = loops.get(name);
  if (hit) return hit;
  const job = (async () => {
    try {
      const r = await fetch(src("bgm", name));
      if (!r.ok) { missing.add("bgm:" + name); return null; }
      const raw = await ctx.decodeAudioData(await r.arrayBuffer());
      const [a, b] = trimEnds(raw);
      if (b - a < ctx.sampleRate * 0.5) return null;   // 사실상 빈 파일
      return seamless(ctx, raw, a, b);
    } catch {
      // 못 풀면 아래에서 <audio loop> 로 물러섭니다.
      return null;
    }
  })();
  loops.set(name, job);
  return job;
}

/** 지금 도는 것. 갈아 끼울 때는 겹쳐 넘깁니다. */
let node: AudioBufferSourceNode | null = null;
let gain: GainNode | null = null;
/** 물러섬 — Web Audio 가 안 될 때만 씁니다. */
let fallback: HTMLAudioElement | null = null;
/** 지금 실제로 소리 내고 있는 이름 (걸린 이름 `cur` 과 다를 수 있음) */
let playing = "";
/** 겹치는 사이에 또 부르면 앞선 요청을 버립니다. */
let epoch = 0;

function rampDown(g: GainNode, s: AudioBufferSourceNode, ctx: AudioContext) {
  const t = ctx.currentTime;
  try {
    g.gain.cancelScheduledValues(t);
    g.gain.setValueAtTime(g.gain.value, t);
    g.gain.linearRampToValueAtTime(0, t + FADE);
    s.stop(t + FADE + 0.05);
  } catch { /* 이미 멎었으면 그만입니다 */ }
}

/**
 * 물러섬 — 예전 방식(`<audio loop>`).
 *
 * 이음새는 거칠어도 **소리는 납니다.** Web Audio 가 없거나 푸는 데
 * 실패했을 때만 여기로 옵니다.
 */
function playFallback(name: string) {
  if (missing.has("bgm:" + name)) return;
  if (playing === name && fallback) {
    void fallback.play().catch(() => {});
    return;
  }
  const el = fallback ?? new Audio();
  el.loop = true;
  el.volume = VOL_BGM;
  el.src = src("bgm", name);
  el.onerror = () => { missing.add("bgm:" + name); playing = ""; };
  fallback = el;
  playing = name;
  void el.play().catch(() => {});
}

async function startBgm(name: string) {
  const mine = ++epoch;
  const ctx = audioCtx();

  if (!ctx) { playFallback(name); return; }

  if (ctx.state === "suspended") {
    await ctx.resume().catch(() => {});
    // 손짓 밖이라 안 열렸습니다. 손님이 화면을 처음 건드릴 때 엽니다.
    if (ctx.state === "suspended") resumeOnGesture(ctx);
  }
  if (mine !== epoch) return;
  if (missing.has("bgm:" + name)) return;

  const buf = await loadLoop(ctx, name);
  if (mine !== epoch || soundState() !== "on") return;
  if (!buf) { playFallback(name); return; }

  const old = node;
  const oldGain = gain;

  const g = ctx.createGain();
  g.gain.setValueAtTime(0, ctx.currentTime);
  g.gain.linearRampToValueAtTime(VOL_BGM, ctx.currentTime + FADE);
  g.connect(ctx.destination);

  const s = ctx.createBufferSource();
  s.buffer = buf;
  s.loop = true;              // ★ 샘플 단위. 여기서 한 톨도 안 빕니다.
  s.loopStart = 0;
  s.loopEnd = buf.duration;
  s.connect(g);
  s.start();

  node = s;
  gain = g;
  playing = name;

  if (old && oldGain) rampDown(oldGain, old, ctx);
  if (fallback) { fallback.pause(); fallback = null; }
}

function pauseBgm() {
  epoch++;
  const ctx = ac;
  if (node && gain && ctx) {
    rampDown(gain, node, ctx);
    node = null;
    gain = null;
    playing = "";
  }
  if (fallback) { fallback.pause(); playing = ""; }
}

/**
 * 배경음을 건다. 같은 것이면 건드리지 않는다 (끊기면 더 거슬린다).
 *
 * ★ 소리가 꺼져 있으면 **이름만 적어 둡니다.** 파일은 켜는 순간
 *   받습니다 — 안 켤 사람에게 1MB 를 물리지 않습니다.
 */
export function playBgm(name: string) {
  if (typeof window === "undefined") return;
  if (cur === name && playing === name) return;
  cur = name;
  if (soundState() !== "on") return;
  void startBgm(name);
}

export function stopBgm() {
  cur = "";
  pauseBgm();
}

/**
 * 켜고 끄기. **손짓 안에서 불러야** 합니다 — 브라우저가 그때만
 * 소리를 허락합니다.
 */
export function toggleSound(): State {
  const next: State = soundState() === "on" ? "off" : "on";
  try {
    localStorage.setItem(KEY, next);
  } catch { /* 못 남겨도 이번 방문 동안은 돕니다 */ }

  if (next === "off") {
    pauseBgm();
    voice?.pause();
  } else if (cur) {
    // 이 손짓 안에서 상자를 엽니다. 나중에 열면 브라우저가 막습니다.
    audioCtx();
    void startBgm(cur);
  }
  tell(next);
  return next;
}

/* ══════════════════════════════════════════════════════════════
   목소리 — 한 번 나고 마는 소리라 고리를 만들 일이 없습니다
   ══════════════════════════════════════════════════════════════ */

/**
 * 한 마디를 읽어 준다.
 *
 * 앞말이 아직 돌고 있으면 끊습니다 — 두 사람이 겹쳐 말하는 것보다
 * 낫습니다.
 */
export function speak(name: string) {
  if (typeof window === "undefined") return;
  if (soundState() !== "on") return;
  if (missing.has("voice:" + name)) return;
  voice?.pause();
  const el = new Audio(src("voice", name));
  el.volume = VOL_VOICE;
  el.onerror = () => missing.add("voice:" + name);
  voice = el;
  void el.play().catch(() => {});
}

/**
 * 서버가 만들어 준 소리를 낸다.
 *
 * ★ 훅은 사람마다 문장이 달라 미리 만들어 둘 수 없습니다. 서버가 그때
 *   만들어 곳간에 두고 주소를 줍니다 (services/api/voice.py). 같은 말은
 *   두 번 안 만들므로 값이 트래픽이 아니라 **서로 다른 말의 수**에
 *   묶이오.
 *
 * ★ 소리가 꺼져 있으면 **청하지도** 않습니다. 값이 나가는 자리라
 *   안 들을 소리를 만들면 안 됩니다.
 */
export async function speakRemote(
  ask: () => Promise<{ url: string | null; ready: boolean }>,
) {
  if (typeof window === "undefined") return;
  if (soundState() !== "on") return;
  try {
    const r = await ask();
    if (!r.ready || !r.url) return;
    if (soundState() !== "on") return;   // 기다리는 새 껐을 수 있습니다
    voice?.pause();
    const el = new Audio(API_BASE + r.url);
    el.volume = VOL_VOICE;
    voice = el;
    void el.play().catch(() => {});
  } catch {
    /* 소리는 곁가지입니다. 실패가 글을 막아서는 안 됩니다. */
  }
}

/** 소리가 실제로 준비된 파일인지 (발주 상태를 화면에서 보려고) */
export async function hasAudio(kind: "bgm" | "voice", name: string) {
  try {
    const r = await fetch(src(kind, name), { method: "HEAD" });
    return r.ok;
  } catch {
    return false;
  }
}
