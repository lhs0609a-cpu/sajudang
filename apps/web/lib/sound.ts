/**
 * 소리 — 배경음(BGM)과 목소리.
 *
 * ★ 왜 이렇게 짰나
 *
 *   1. **소리는 기본 꺼짐입니다.**
 *      브라우저가 사용자의 손짓 없이 나는 소리를 막습니다. 막힌 줄도
 *      모르고 "왜 안 나지" 하다 끝납니다. 그리고 사주를 보는 사람은
 *      회사·지하철·침대 옆인 경우가 많습니다. 갑자기 소리가 나면
 *      그 자리에서 창을 닫습니다. **먼저 묻고, 켜면 켭니다.**
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
 * ★ 파일 두는 곳
 *
 *      /audio/bgm/{이름}.mp3     배경음 — 이어 붙는 고리(loop)
 *      /audio/voice/{장면}.mp3   목소리 — 도령이 하는 말 한 마디
 *
 *   docs/10 에 발주 내용을 적어 둡니다.
 */

const KEY = "sd.sound";       // 켬/끔 — 이 기기에만 남습니다
const VOL_BGM = 0.22;         // 배경음은 말보다 훨씬 아래로
const VOL_VOICE = 0.9;

type State = "on" | "off";

let bgm: HTMLAudioElement | null = null;
let voice: HTMLAudioElement | null = null;
let cur = "";                 // 지금 도는 배경음 이름
const missing = new Set<string>();   // 없는 것으로 확인된 파일
const listeners = new Set<(s: State) => void>();

export function soundState(): State {
  if (typeof window === "undefined") return "off";
  try {
    return localStorage.getItem(KEY) === "on" ? "on" : "off";
  } catch {
    /* 저장을 막아 둔 브라우저가 있습니다. 그럴 땐 꺼진 것으로 봅니다. */
    return "off";
  }
}

export function onSoundChange(fn: (s: State) => void) {
  listeners.add(fn);
  // 리액트의 정리 함수는 아무것도 안 돌려줘야 합니다 (delete 는 boolean)
  return () => { listeners.delete(fn); };
}

function tell(s: State) {
  listeners.forEach((f) => f(s));
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
    bgm?.pause();
    voice?.pause();
  } else if (cur) {
    void bgm?.play().catch(() => {});
  }
  tell(next);
  return next;
}

function src(kind: "bgm" | "voice", name: string) {
  return `/audio/${kind}/${name}.mp3`;
}

/** 배경음을 건다. 같은 것이면 건드리지 않는다 (끊기면 더 거슬린다). */
export function playBgm(name: string) {
  if (typeof window === "undefined") return;
  if (missing.has("bgm:" + name)) return;
  if (cur === name && bgm) {
    if (soundState() === "on" && bgm.paused) void bgm.play().catch(() => {});
    return;
  }
  const el = bgm ?? new Audio();
  el.loop = true;
  el.volume = VOL_BGM;
  el.src = src("bgm", name);
  el.onerror = () => {
    // 아직 안 들어온 파일입니다. 다시 찾지 않습니다.
    missing.add("bgm:" + name);
    cur = "";
  };
  bgm = el;
  cur = name;
  if (soundState() === "on") void el.play().catch(() => {});
}

export function stopBgm() {
  bgm?.pause();
  cur = "";
}

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

/** 소리가 실제로 준비된 파일인지 (발주 상태를 화면에서 보려고) */
export async function hasAudio(kind: "bgm" | "voice", name: string) {
  try {
    const r = await fetch(src(kind, name), { method: "HEAD" });
    return r.ok;
  } catch {
    return false;
  }
}
