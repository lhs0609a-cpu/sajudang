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

const { SCN, MO, CAM, ANIMBASE, TINT, PIPE } = sandbox.__x;
const out = { ANIMBASE, TINT, PIPE, CAM, scenes: {} };
for (const id of Object.keys(SCN)) {
  const s = SCN[id];
  const mo = MO[id] || {};
  let image = null;
  try {
    image = typeof s.prompt === "function" ? s.prompt() : (s.prompt || null);
  } catch (e) {
    console.error("  prompt 평가 실패:", id, e.message);
  }
  out.scenes[id] = {
    title: s.t,
    spec: s.spec || null,
    hint: s.hint || null,
    image,
    motion: mo.hg || null,
    preset: mo.ps || "Static",
    ratio: mo.ar || "16:9",
    duration: mo.du || "3s",
    loop: !!mo.loop,
    tint: !!mo.tint,
    still: !!mo.still,
    note: mo.note || null,
  };
}
fs.writeFileSync(process.argv[3], JSON.stringify(out, null, 1), "utf8");
const v = Object.values(out.scenes);
console.log(
  `장면 ${v.length}개 · 이미지 프롬프트 ${v.filter((x) => x.image).length}` +
  ` · 모션 프롬프트 ${v.filter((x) => x.motion).length}`);
console.log("없는 것:",
  v.filter((x) => !x.image || !x.motion).map((x) => x.title).join(", ") || "없음");
