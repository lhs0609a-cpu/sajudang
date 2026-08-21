/*
 * 에셋 제작 프롬프트 전량을 한 장의 텍스트로 뽑는다.
 *
 *   node tools/prompt_sheet.js reference/sajudang.html 에셋_프롬프트_전체.txt
 *
 * 왜 손으로 안 옮기는가
 *   프롬프트는 40장이고 한 장이 900자를 넘습니다. 손으로 옮기면 반드시
 *   어긋납니다. 참조 구현체를 실제로 평가해서 뽑습니다.
 *
 * 두 가지를 특히 조심합니다
 *   ① 대문(gate)만 계절을 탑니다. 만드는 것은 **한 장이면 됩니다** —
 *      앱이 계절 폴더가 비면 기본 폴더로 내려옵니다. 나머지 세 계절
 *      프롬프트는 나중에 쓰고 싶어질 때를 위해 붙임 4 에 실어 둡니다.
 *      SEA 를 네 번 갈아 끼워야 넷을 다 얻습니다.
 *   ② 참조 구현체는 hg 안에 달러-중괄호로 감싼 ANIMBASE 를 문자열로
 *      적어 두어, 화면에 그 글자가 그대로 남습니다. 그걸 복사해
 *      힉스필드에 넣으면 영상 앵커가 빠지고 docs/10 §2 대로 3초 안에
 *      얼굴이 사진처럼 변합니다. 여기서 실제 문구로 바꿔 넣습니다.
 */
const fs = require("fs");
const vm = require("vm");

const SRC = process.argv[2] || "reference/sajudang.html";
const OUT = process.argv[3] || "에셋_프롬프트_전체.txt";
const FIGJSON = "apps/web/public/asset-prompts.json";

const js = fs.readFileSync(SRC, "utf8");
const NL = String.fromCharCode(10);
const ANCHOR = "$" + "{ANIMBASE}";   // 치환할 자리표시. 소스에 그대로 남아 있다.

function at(m) {
  const i = js.indexOf(m);
  if (i < 0) throw new Error("못 찾음: " + m);
  return i;
}
// b 는 a 이후에서 찾아야 한다. 처음부터 찾으면 엉뚱한 데를 잘라 빈 조각이 나온다.
function cut(a, b) {
  const i = at(a);
  const j = js.indexOf(b, i + a.length);
  if (j < 0) throw new Error("끝을 못 찾음: " + b);
  return js.slice(i, j);
}

const PARTS = [
  cut("const SCN={", "const SEASON"),
  cut("const SEASON", "function setSea"),
  cut("const ANIMBASE", "const MO="),
  cut("const MO=", NL + "const CAM="),
  cut("const CAM=", NL + "/*"),
];

/** SEA 를 갈아 끼우고 한 번 평가한다. const 는 스크립트 스코프라 한 덩어리여야 한다. */
function evalWith(sea) {
  const sb = { cat: () => "", console };
  vm.createContext(sb);
  vm.runInContext(
    PARTS.join(NL + ";" + NL) + NL +
    ";SEA=" + JSON.stringify(sea) + ";" + NL +
    ";globalThis.__x={SCN,MO,SEASON,ANIMBASE,TINT,PIPE};", sb);
  return sb.__x;
}

const SEASONS = [
  { k: "spring", ko: "봄 · 벚꽃" },
  { k: "summer", ko: "여름 · 능소화" },
  { k: "autumn", ko: "가을 · 국화" },
  { k: "winter", ko: "겨울 · 매화" },
];

/*
 * 한 장만 만들 때 쓸 그림. 참조 구현체의 SEA 기본값과 같게 둡니다.
 * 다른 계절 그림이 더 마음에 들면 붙임 4 에서 골라 쓰면 됩니다.
 */
const DEFAULT_SEASON = { k: "summer", ko: "여름 · 능소화" };

const base = evalWith("summer");
const { SCN, MO, ANIMBASE, TINT } = base;
const bySeason = {};
for (const s of SEASONS) bySeason[s.k] = evalWith(s.k).SCN;

function rawPrompt(scn, id) {
  const p = scn[id].prompt;
  return (typeof p === "function" ? p() : p) || "";
}

/** 계절을 타는 장면을 찾아낸다 — 표에 박아두면 나중에 늘었을 때 조용히 빠진다. */
const SEASONAL = Object.keys(SCN).filter((id) =>
  new Set(SEASONS.map((s) => rawPrompt(bySeason[s.k], id))).size > 1);

function motionOf(id) {
  const hg = (MO[id] || {}).hg;
  return hg ? hg.split(ANCHOR).join(ANIMBASE) : "";
}

/* ── 화면 순서 ─────────────────────────────────────────────
   기계로는 뽑을 수 없습니다. 한 장면이 여러 화면에 나오기 때문입니다.
   apps/web/app 아래 page.tsx 들의 Scene 등장 순서대로 적었습니다.
   ---------------------------------------------------------- */
const ORDER = [
  ["1부 · 진입 — 첫 화면부터 명식 세우기까지", [
    ["gate", "a1 골목 — 맨 처음 보는 화면 · 공유 링크로 들어와도 여기"],
    ["door", "a1 골목 — 문이 열리는 순간 (★ 붙임 3 참고)"],
    ["desk", "a2 이름을 적다"],
    ["ink", "a3 생년월일시 · a5 고민 고르기"],
    ["room", "a4 방 안"],
    ["fork", "a6 갈림길"],
    ["altar", "a7 상 위"],
    ["facing", "a8 마주 앉다"],
  ]],
  ["2부 · 진열대 — 캐릭터 고르기", [
    ["hall", "b1 진열대 들머리"],
    ["seat", "b2 자리"],
    ["shelf", "b3 걸린 목패"],
  ]],
  ["3부 · 리포트", [
    ["scroll", "c1 두루마리 · c7 분석지"],
    ["roadmap", "c2 길 그림"],
    ["fold", "c3 접힌 데"],
    ["cardbg", "c4 패 뒷면"],
    ["wall", "c5 벽 · m1 인장첩"],
    ["oldpaper", "c6 낡은 종이 · p1 값"],
  ]],
  ["4부 · 결제", [
    ["coin", "p2 엽전"],
    ["untie", "p3 매듭을 풀다"],
    ["tray", "p4 소반"],
  ]],
  ["5부 · 릴레이", [
    ["handle", "r1 손잡이"],
  ]],
  ["6부 · 오늘의 일진", [
    ["banner", "d1 현수막"],
    ["tea", "d2 차 한 잔"],
  ]],
  ["7부 · 인장첩", [
    ["sealbook", "m2 인장첩"],
  ]],
];

/* ── 신살 인물 (docs/16) ── */
const FIG_ORDER = [
  "cheoneul", "taegeuk", "munchang", "geumyeo", "amrok",
  "yangin", "baekho", "wonjin", "dohwa", "yeokma",
  "hwagae", "gwaegang", "gongmang",
];
const FIGS = JSON.parse(fs.readFileSync(FIGJSON, "utf8")).figures;

/* ── 빠진 것이 없는지 먼저 센다 ── */
const listed = new Set(ORDER.flatMap(([, rows]) => rows.map((r) => r[0])));
const missing = Object.keys(SCN).filter((id) => !listed.has(id));
if (missing.length) {
  console.error("차례에 빠진 장면이 있습니다: " + missing.join(", "));
  process.exit(1);
}
const figMissing = FIG_ORDER.filter((k) => !FIGS[k]);
if (figMissing.length) {
  console.error("인물 프롬프트가 없습니다: " + figMissing.join(", "));
  process.exit(1);
}

/* ── 항목을 펼친다. 대문은 계절만큼 늘어난다 ── */
const items = [];
for (const [group, rows] of ORDER) {
  for (const [id, where] of rows) {
    const mo = MO[id] || {};
    const seasonal = SEASONAL.includes(id);
    items.push({
      group, id, key: id, title: SCN[id].t, where,
      dir: "public/scene/" + id + "/",
      image: rawPrompt(bySeason[DEFAULT_SEASON.k], id),
      motion: motionOf(id),
      mo, hint: SCN[id].hint || null,
      extra: seasonal
        ? ("한 장만 만드시오. 이 그림이 사계절 내내 나옵니다." + NL +
           "         ★ 위 '메모' 는 계절 4종을 만들라고 하지만 그러지" + NL +
           "         않아도 됩니다. 계절판을 넣고 싶어지면 그때 붙임 4 를" + NL +
           "         보시오 — 넣기만 하면 코드 고칠 것 없이 우선합니다." + NL +
           "         아래 프롬프트는 " + DEFAULT_SEASON.ko + " 입니다.")
        : null,
    });
  }
}
for (const k of FIG_ORDER) {
  const f = FIGS[k];
  items.push({
    group: "8부 · 신살 인물 — 분석지에 나오는 사람들",
    id: k, key: k, title: f.title,
    where: (f.who || "") + " — 명식에 이 신살이 있는 사람에게만 나옵니다",
    dir: "public/sinsal/" + k + "/",
    image: f.image || "", motion: f.motion || "",
    mo: { ps: f.preset, ar: f.ratio, du: f.duration,
          loop: f.loop, tint: f.tint, still: f.still },
    hint: null, extra: null,
  });
}

/* ── 글로 뽑는다 ── */
const W = 74;
const bar = (c) => c.repeat(W);
/** HTML 을 걷어내고, 이어지는 줄을 라벨 아래로 가지런히 들여 쓴다. */
const strip = (h) => (h || "")
  .replace(/<br\s*\/?>/g, NL)
  .replace(/<[^>]+>/g, "")
  .split(NL)
  .map((x) => x.trim())
  .filter((x) => x.length)
  .join(NL + "         ");

function spec(m) {
  const out = [m.ar || "16:9", m.du || "3s", "프리셋 " + (m.ps || "Static")];
  out.push(m.loop ? "이어붙여 반복" : "한 번만");
  if (m.tint) out.push("★ 앱이 흑백으로 바꾼 뒤 캐릭터 색을 입힙니다");
  if (m.still) out.push("PNG 정지컷도 함께");
  return out.join(" · ");
}

const L = [];
const P = (s) => L.push(s === undefined ? "" : s);

const total = items.length;
const nScene = items.filter((x) => x.dir.indexOf("/scene/") >= 0).length;
const nTint = items.filter((x) => x.mo.tint).length;

P(bar("="));
P("  사주당 · 에셋 제작 프롬프트 전량");
P("  reference/sajudang.html 과 docs/16 에서 그대로 뽑은 것입니다");
P(bar("="));
P();
P("  이미지 " + total + "장  (장면 " + nScene + " + 신살 인물 " + FIG_ORDER.length + ")");
P("  영상 " + items.filter((x) => x.motion).length + "편");
P();
P("  한 항목마다 이 순서입니다");
P();
P("    ① 제미나이   [① 이미지] 를 그대로 붙여 넣어 그림 한 장을 뽑는다");
P("    ② 힉스필드   그 그림을 올리고 [② 모션] + 적힌 프리셋을 넣는다");
P("    ③ 내려받는다  webm(VP9) · mp4(H.264) · poster.jpg 세 벌로 만든다");
P("    ④ 넣는다     적힌 폴더에 넣으면 코드는 안 고쳐도 바뀝니다");
P();
P(bar("-"));
P("  지우면 안 되는 것 세 가지");
P(bar("-"));
P();
P("  1. [② 모션] 끝에 붙은 긴 영어 문단");
P();
P("     This is a 2D hand-drawn animation... 으로 시작하는 대목입니다.");
P("     통째로 같이 넣으시오. 빼면 3초 안에 그림이 실사 사진처럼");
P("     변합니다. 얼굴이 특히 심합니다. (docs/10 §2)");
P();
P("  2. '앱이 흑백으로 바꾼다' 고 적힌 장면 — " + nTint + "장입니다");
P();
P("     앱이 grayscale(1) 을 걸고 그 위에 캐릭터 색을 덮습니다.");
P("     그림에 넣은 색은 어차피 지워집니다. 색으로 분위기를 내려");
P("     하지 말고 명암·형태·질감으로 승부하시오. 클립 한 벌이");
P("     캐릭터 스무 명의 색을 전부 감당하는 구조입니다.");
P("     쓰이는 CSS 는 붙임 1 에 있습니다.");
P();
P("  3. 대문 (01) — 한 장이면 됩니다");
P();
P("     참조 구현체 메모에는 계절 4종을 만들라고 적혀 있으나");
P("     그러지 않아도 됩니다. 한 장을 넣으면 사계절 내내 나옵니다.");
P("     나중에 계절판을 넣고 싶어지면 붙임 4 의 프롬프트로 만들어");
P("     계절 폴더에 넣기만 하면 그때부터 그게 우선합니다.");
P();
P(bar("-"));
P("  차례");
P(bar("-"));
{
  let i = 0, g = null;
  for (const it of items) {
    if (it.group !== g) { g = it.group; P(); P("  " + g); }
    i += 1;
    P("    " + String(i).padStart(2, "0") + "  " +
      it.title.padEnd(24) + "  " + it.dir);
  }
}
P();

let n = 0, g = null;
for (const it of items) {
  n += 1;
  if (it.group !== g) {
    g = it.group;
    P(); P(); P(bar("#")); P("  " + g); P(bar("#"));
  }
  P();
  P(bar("="));
  P("  " + String(n).padStart(2, "0") + " / " + total + "   " + it.title);
  P(bar("="));
  P("  화면   " + it.where);
  P("  폴더   " + it.dir);
  P("  규격   " + spec(it.mo));
  if (it.mo.note) P("  메모   " + strip(it.mo.note));
  if (it.hint) P("  참고   " + strip(it.hint));
  if (it.extra) P("  참고   " + it.extra);
  P();
  P(bar("-"));
  P("  ① 이미지 · 제미나이");
  P(bar("-"));
  P();
  P(it.image.replace(/\s+$/, ""));
  P();
  P(bar("-"));
  P("  ② 모션 · 힉스필드   (프리셋 " + (it.mo.ps || "Static") +
    " · " + (it.mo.ar || "16:9") + " · " + (it.mo.du || "3s") + ")");
  P(bar("-"));
  P();
  P(it.motion.replace(/\s+$/, ""));
  P();
}

P();
P();
P(bar("#"));
P("  붙임 1 · 착색 CSS");
P(bar("#"));
P();
P("  '무채색' 이라고 적힌 장면에만 씁니다. 이미 앱에 들어가 있으니");
P("  따로 붙일 일은 없고, 왜 색 없이 뽑아야 하는지 확인용입니다.");
P();
P(TINT.replace(/\s+$/, ""));
P();
P(bar("#"));
P("  붙임 2 · 다 만들었는지 세는 표");
P(bar("#"));
P();
P("  폴더마다 세 개가 있어야 합니다 — clip.webm · clip.mp4 · poster.jpg");
P("  하나라도 없으면 그 화면은 자리표시 그림으로 남습니다.");
P();
for (const it of items) {
  P("  [ ]  " + it.dir.padEnd(30) + it.title);
}
P();
P(bar("#"));
P("  붙임 3 · 만들어도 지금은 화면에 안 나오는 것");
P(bar("#"));
P();
P("  02 열리는 문 (public/scene/door/)");
P();
P("    참조 구현체는 a1 서사 세 번째 칸에서 대문을 '열리는 문' 으로");
P("    바꿔 끼웁니다. 옮기는 과정에서 그 교체가 빠졌습니다.");
P("    그림은 만들어 두시오 — 코드는 따로 이어 붙이겠습니다.");
P();

P(bar("#"));
P("  붙임 4 · 나중에 계절판을 넣고 싶어지면 (안 만들어도 됩니다)");
P(bar("#"));
P();
P("  대문은 한 장이면 충분합니다. 이 붙임은 '봄에는 벚꽃, 겨울에는");
P("  매화' 를 하고 싶어질 때만 보시오.");
P();
P("  넣는 자리");
P();
for (const sN of SEASONS) {
  P("    public/scene/gate/" + (sN.k + "/").padEnd(10) + "  " + sN.ko);
}
P();
P("  계절 폴더에 그림이 있으면 앱이 그걸 먼저 씁니다. 없으면");
P("  public/scene/gate/ 로 내려옵니다. 한 계절만 만들어 넣어도");
P("  나머지는 기본 그림으로 굴러갑니다.");
P();
P("  ② 모션 프롬프트는 넷 다 같습니다 — 본문 01 번 것을 그대로 쓰시오.");
P("  달라지는 것은 ① 이미지뿐이고, 꽃과 하늘색만 바뀝니다.");
P();
for (const sN of SEASONS) {
  P(bar("-"));
  P("  ① 이미지 · 제미나이 · " + sN.ko +
    (sN.k === DEFAULT_SEASON.k ? "   (본문 01 번과 같은 것)" : ""));
  P("  " + "public/scene/gate/" + sN.k + "/");
  P(bar("-"));
  P();
  P(rawPrompt(bySeason[sN.k], "gate").replace(/\s+$/, ""));
  P();
}
P();
fs.writeFileSync(OUT, L.join(NL) + NL, "utf8");

const text = L.join(NL);
console.log("썼습니다: " + OUT);
console.log("  항목 " + total + " (장면 " + nScene + " · 인물 " + FIG_ORDER.length + ")");
console.log("  계절을 타는 장면: " + (SEASONAL.join(", ") || "없음"));
console.log("  이미지 프롬프트 빠진 것: " +
  (items.filter((x) => !x.image).map((x) => x.key).join(", ") || "없음"));
console.log("  모션 프롬프트 빠진 것: " +
  (items.filter((x) => !x.motion).map((x) => x.key).join(", ") || "없음"));
console.log("  치환 안 된 자리표시: " +
  (text.indexOf(ANCHOR) >= 0 ? "★ 있음 — 확인하시오" : "없음"));
console.log("  영상 앵커가 든 항목: " +
  items.filter((x) => x.motion.indexOf("2D hand-drawn animation") >= 0).length +
  " / " + items.filter((x) => x.motion).length);
