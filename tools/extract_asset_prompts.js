// 참조 구현체에서 에셋 프롬프트만 뽑아낸다. 손으로 옮기면 어긋난다.
//
//   node extract.js ref.js out.json
//
// 평가 순서가 중요하다. SCN 의 prompt 는 SEASON 을 참조하고,
// MO 의 hg 는 ANIMBASE 를 참조한다.
const fs = require("fs");
const vm = require("vm");
const js = fs.readFileSync(process.argv[2], "utf8");

const sandbox = { cat: () => "", console };
vm.createContext(sandbox);

function at(marker) {
  const i = js.indexOf(marker);
  if (i < 0) throw new Error("못 찾음: " + marker);
  return i;
}
// b 는 a 이후에서 찾아야 한다. 처음부터 찾으면 엉뚱한 데를 잘라 빈 조각이 나온다.
function cut(a, b) {
  const i = at(a);
  const j = js.indexOf(b, i + a.length);
  if (j < 0) throw new Error("끝을 못 찾음: " + b);
  return js.slice(i, j);
}

const parts = [
  cut("const SCN={", "const SEASON"),        // 장면 (art·prompt 정의만)
  cut("const SEASON", "function setSea"),    // 계절 + let SEA — prompt 가 참조
  cut("const ANIMBASE", "const MO="),        // ANIMBASE · PIPE · TINT
  cut("const MO=", "\nconst CAM="),
  cut("const CAM=", "\n/*"),
];

// const 는 스크립트 스코프에 갇히므로 한 덩어리로 평가하고 끝에서 내보낸다
const NL = String.fromCharCode(10);
const source = parts.join(NL + ";" + NL) + NL +
  ";globalThis.__x = {SCN, MO, CAM, ANIMBASE, TINT, PIPE};";

try {
  vm.runInContext(source, sandbox);
} catch (e) {
  console.error("평가 실패:", e.message);
  process.exit(1);
}

/*
 * ★ 대문(gate)은 계절을 탑니다. 한 번만 평가하면 SEA 의 초기값(여름)
 *   하나만 나오고 봄·가을·겨울이 통째로 빕니다. 화면에서 계절을 바꿔도
 *   여름 프롬프트가 뜨고, 그걸 복사해 만든 그림은 나머지 세 계절에
 *   쓰이지 않습니다. SEA 를 갈아 끼워 네 번 평가합니다.
 */
const SEASON_KEYS = ["spring", "summer", "autumn", "winter"];
function promptsFor(sea) {
  const sb = { cat: () => "", console };
  vm.createContext(sb);
  vm.runInContext(
    parts.join(NL + ";" + NL) + NL + ";SEA=" + JSON.stringify(sea) + ";" +
    NL + ";globalThis.__y = {SCN};", sb);
  const out = {};
  for (const id of Object.keys(sb.__y.SCN)) {
    const p = sb.__y.SCN[id].prompt;
    out[id] = (typeof p === "function" ? p() : p) || null;
  }
  return out;
}
const BY_SEASON = {};
for (const k of SEASON_KEYS) BY_SEASON[k] = promptsFor(k);
/** 표에 박아두면 계절 장면이 늘었을 때 조용히 빠집니다. 세어서 찾습니다. */
const SEASONAL = new Set(
  Object.keys(BY_SEASON.spring).filter(
    (id) => new Set(SEASON_KEYS.map((k) => BY_SEASON[k][id])).size > 1));

const { SCN, MO, CAM, ANIMBASE, TINT, PIPE } = sandbox.__x;

/*
 * 신살 인물 13종은 참조 구현체에 없습니다 (docs/16 에서 나왔습니다).
 * 원본은 seed/figure_prompts.json 이고 여기서는 합치기만 합니다.
 * 산출물에서 거꾸로 읽어 오면 추출기를 다시 돌릴 때마다 인물이
 * 통째로 날아갑니다 — 한 번 그럴 뻔했습니다.
 */
const FIG_SRC = "seed/figure_prompts.json";
const figSrc = JSON.parse(fs.readFileSync(FIG_SRC, "utf8"));
const figures = {};
for (const k of Object.keys(figSrc)) {
  if (k === "_") continue;                       // 머리말
  const f = figSrc[k];
  if (!f.image || !f.motion) {
    console.error("인물 프롬프트가 비었습니다: " + k);
    process.exit(1);
  }
  figures[k] = { note: null, hint: null, ...f };
}

const out = { ANIMBASE, TINT, PIPE, CAM, scenes: {}, figures };
for (const id of Object.keys(SCN)) {
  const s = SCN[id];
  const mo = MO[id] || {};
  let image = null;
  try {
    image = typeof s.prompt === "function" ? s.prompt() : (s.prompt || null);
  } catch (e) {
    console.error("  prompt 평가 실패:", id, e.message);
  }
  // ★ 참조 구현체는 hg 안에 ${'${ANIMBASE}'} 로 적어 두어 **문자 그대로**
  //   "${ANIMBASE}" 가 남습니다. 그대로 복사하면 영상 앵커가 빠지고,
  //   docs/10 §2 가 경고한 대로 3초 안에 얼굴이 사진처럼 변합니다.
  //   여기서 실제 앵커 문구로 바꿔 넣습니다.
  const motion = (mo.hg || null) &&
    mo.hg.split("${ANIMBASE}").join(ANIMBASE);

  const seasonal = SEASONAL.has(id);
  const seasons = seasonal
    ? Object.fromEntries(SEASON_KEYS.map((k) => [k, BY_SEASON[k][id]]))
    : null;

  out.scenes[id] = {
    title: s.t,
    seasonal,
    seasons,
    spec: s.spec || null,
    hint: s.hint || null,
    image,
    motion,
    preset: mo.ps || "Static",
    ratio: mo.ar || "16:9",
    duration: mo.du || "3s",
    loop: !!mo.loop,
    tint: !!mo.tint,
    still: !!mo.still,
    note: mo.note || null,
  };
}
/*
 * ★ 있던 것을 지우면서 덮어쓰지 않는다.
 *
 *   2026-09-02 에 hall 프롬프트 한 줄을 고치려고 이걸 통째로 다시
 *   돌렸더니, **캐릭터 초상 프롬프트 20종과 mirror 장면이 함께
 *   사라졌습니다.** 그 둘은 참조 구현체에 없고 이 파일에만 삽니다
 *   (mirror 는 발주서가 쓰인 뒤에 붙은 화면이고, chars 는 여기서
 *   따로 씁니다). 재생성은 **참조 구현체에 있는 것만** 압니다.
 *
 *   그래서 있던 열쇠가 빠지면 멈춥니다. 한 덩이만 고칠 거면 이 도구를
 *   돌리지 말고 그 값만 갈아 끼우세요.
 */
const OUT = process.argv[3];
if (fs.existsSync(OUT)) {
  const prev = JSON.parse(fs.readFileSync(OUT, "utf8"));
  const lost = [];
  for (const k of Object.keys(prev)) {
    if (!(k in out)) { lost.push(k); continue; }
    if (prev[k] && typeof prev[k] === "object" && !Array.isArray(prev[k])) {
      for (const sub of Object.keys(prev[k])) {
        if (!(sub in (out[k] || {}))) lost.push(k + "." + sub);
      }
    }
  }
  if (lost.length) {
    console.error("덮어쓰면 사라지는 것 " + lost.length + " 개:");
    console.error("  " + lost.join(", "));
    console.error("참조 구현체에 없는 것들입니다. 여기서만 사는 값이라");
    console.error("통째로 다시 뽑으면 잃습니다. 고칠 값만 갈아 끼우세요.");
    console.error("정말 버리려면 --force 를 주세요.");
    if (!process.argv.includes("--force")) process.exit(1);
  }
}
fs.writeFileSync(OUT, JSON.stringify(out, null, 1), "utf8");
const v = Object.values(out.scenes);
console.log(
  `장면 ${v.length}개 · 이미지 프롬프트 ${v.filter((x) => x.image).length}` +
  ` · 모션 프롬프트 ${v.filter((x) => x.motion).length}`);
console.log("신살 인물:", Object.keys(figures).length, "종 (" + FIG_SRC + ")");
console.log("계절을 타는 장면:",
  [...SEASONAL].join(", ") || "없음",
  "→ 계절별 프롬프트를 따로 실었습니다");
console.log("없는 것:",
  v.filter((x) => !x.image || !x.motion).map((x) => x.title).join(", ") || "없음");
