"""
쉬운 말 다시 쓰기 — 나누고 · 검사하고 · 합친다.

    python tools/plain_split.py split DIR [--budget 40000]
    python tools/plain_split.py check DIR          # 고쳐 쓴 것 검사만
    python tools/plain_split.py merge DIR --write  # 검사를 통과한 줄만 써넣음

★ 왜 나누나 (2026-09-11)

  손님이 짚었습니다 — "모든 캐릭터든 모든 말을 다 쉽게 설명해 줘.
  어려운 단어 쓰지 말고, 쓸 때는 반드시 쉬운 말로 설명하고."

  말 뱅크가 23만 자입니다(lens_cuts 16만 · topic 3.5만 · bank 1.6만 …).
  여럿이 **같은 파일을 동시에** 고치면 서로 덮어씁니다. 그래서 문자열을
  `id`(JSON 경로)와 함께 조각 파일로 떼어 내고, 각자 제 조각만 고친 뒤
  여기서 합칩니다.

★ 합치기 전에 줄마다 봅니다 — 하나라도 어긋나면 **그 줄은 원문을 둡니다**

  · `{자리표시}` 가 그대로인가         엔진이 채워 넣는 자리요
  · 태그(<b> <br /> …) 수가 같은가      굵게 칠한 자리가 곧 훑어읽기 자리요
  · 한자·숫자가 그대로인가             셈에서 온 것이라 글쓴이가 못 바꾸오
  · 가드(적중률·과학·반드시·병명 …)     새로 들어오면 안 되오
  · 「그대로」 가 없는가               호칭 층이 「그대」 로 읽어 갈아 끼우오
  · 문장이 「~인지.」 로 끝나지 않는가   말투 감사가 반말로 잡소

★ 문서 열쇠(`_` 로 시작)와 손님이 누르는 말(버튼·보기), 이름·호칭,
  근거 줄(`source`)은 안 뗍니다.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services" / "api"))

SEED = ROOT / "seed"
H = re.compile(r"[가-힣]")

# 파일마다 무엇을 떼나. None 이면 한글 든 문자열 전부(아래 SKIP 제외).
FILES = {
    "lens_cuts": None,
    "topic": None,
    "bank": None,
    "spine": None,
    "sinsal": None,
    "extras": None,
    "lens_view": None,
    "lenses": {"opening_quote", "specialty"},
    "relay_rules": {"reason"},
}
# 안 떼는 열쇠 — 이름·호칭·근거 줄·손님의 말
SKIP = {"source", "name", "hanja", "group", "archetype", "you_word", "call",
        "you", "you_else", "value", "id", "label", "opts", "el", "seat",
        "topics", "key", "axis", "voice"}

PH = re.compile(r"\{[A-Za-z_0-9]*\}|%[sd]")
TAG = re.compile(r"<\s*/?\s*([a-zA-Z]+)[^>]*>")
HANJA = re.compile(r"[一-鿿]")
DIGIT = re.compile(r"\d+")
BAD_END = re.compile(r"인지[.!?]?\s*(</[a-z]+>)*\s*$")
BANNED = re.compile(r"적중|과학적|통계|반드시|입증|그대로")


def _walk(o, path, out, only):
    if isinstance(o, dict):
        for k, v in o.items():
            if str(k).startswith("_") or k in SKIP:
                continue
            _walk(v, path + [str(k)], out, only)
    elif isinstance(o, list):
        for i, v in enumerate(o):
            _walk(v, path + [str(i)], out, only)
    elif isinstance(o, str) and H.search(o):
        if only is None or (path and path[-1] in only):
            out.append(("/".join(path), o))


def strings(name: str) -> list:
    d = json.loads((SEED / f"{name}.json").read_text("utf-8"))
    out: list = []
    _walk(d, [], out, FILES[name])
    return out


def split(dirp: Path, budget: int) -> None:
    dirp.mkdir(parents=True, exist_ok=True)
    chunks, cur, size = [], [], 0
    for name in FILES:
        for sid, t in strings(name):
            if size + len(t) > budget and cur:
                chunks.append(cur)
                cur, size = [], 0
            cur.append({"f": name, "id": sid, "t": t})
            size += len(t)
    if cur:
        chunks.append(cur)
    manifest = []
    for i, ch in enumerate(chunks):
        p = dirp / ("chunk_%02d.jsonl" % i)
        p.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in ch),
                     "utf-8")
        files = Counter(r["f"] for r in ch)
        manifest.append({"chunk": p.name, "lines": len(ch),
                         "chars": sum(len(r["t"]) for r in ch),
                         "files": dict(files)})
    (dirp / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=1), "utf-8")
    for m in manifest:
        print("%s  %4d줄  %6d자  %s" % (m["chunk"], m["lines"], m["chars"],
                                      m["files"]))


def problems(old: str, new: str) -> list:
    from engine import guard
    bad = []
    if Counter(PH.findall(old)) != Counter(PH.findall(new)):
        bad.append("자리표시")
    if Counter(TAG.findall(old)) != Counter(TAG.findall(new)):
        bad.append("태그")
    if Counter(HANJA.findall(old)) != Counter(HANJA.findall(new)):
        bad.append("한자")
    if Counter(DIGIT.findall(old)) != Counter(DIGIT.findall(new)):
        bad.append("숫자")
    ok, hits = guard.check(new)
    if not ok:
        bad.append("가드:%s" % hits)
    m = BANNED.search(new)
    if m and not BANNED.search(old):
        bad.append("금지어:%s" % m.group(0))
    if BAD_END.search(re.sub(r"<[^>]+>", "", new)) and not BAD_END.search(
            re.sub(r"<[^>]+>", "", old)):
        bad.append("「~인지.」 끝")
    if len(new) > max(len(old) * 1.8, len(old) + 80):
        bad.append("너무 길어짐 %d→%d" % (len(old), len(new)))
    if not new.strip():
        bad.append("빈 글")
    return bad


def load_out(dirp: Path) -> dict:
    """chunk_XX.out*.jsonl 을 전부 읽는다 — 여러 조각으로 나눠 써도 됩니다."""
    got = {}
    for p in sorted(dirp.glob("chunk_*.out*.jsonl")):
        for n, line in enumerate(p.read_text("utf-8").splitlines(), 1):
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
                got[(r["f"], r["id"])] = r["t"]
            except Exception as e:
                print("  ! %s:%d 못 읽음 — %s" % (p.name, n, e))
    return got


def check(dirp: Path) -> tuple[dict, dict]:
    orig = {}
    for p in sorted(dirp.glob("chunk_??.jsonl")):
        for line in p.read_text("utf-8").splitlines():
            r = json.loads(line)
            orig[(r["f"], r["id"])] = r["t"]
    got = load_out(dirp)
    good, bad = {}, {}
    for k, new in got.items():
        if k not in orig:
            bad[k] = ["모르는 id"]
            continue
        if new == orig[k]:
            continue
        pr = problems(orig[k], new)
        if pr:
            bad[k] = pr
        else:
            good[k] = new
    miss = len(orig) - len(set(orig) & set(got))
    print("원문 %d줄 · 받은 줄 %d · 바뀐 줄 %d 통과 · %d 거절 · 안 온 줄 %d"
          % (len(orig), len(got), len(good), len(bad), miss))
    for k, pr in list(bad.items())[:40]:
        print("  ✗ %s/%s — %s" % (k[0], k[1], ", ".join(pr)))
    return good, bad


def _set(d, path: list, val):
    cur = d
    for k in path[:-1]:
        cur = cur[int(k)] if isinstance(cur, list) else cur[k]
    last = path[-1]
    if isinstance(cur, list):
        cur[int(last)] = val
    else:
        cur[last] = val


def _indent(text: str) -> int:
    for line in text.splitlines()[1:]:
        if line.strip():
            return len(line) - len(line.lstrip(" "))
    return 1


def merge(dirp: Path, write: bool) -> None:
    good, _ = check(dirp)
    by_file: dict = {}
    for (f, sid), t in good.items():
        by_file.setdefault(f, []).append((sid, t))
    for f, rows in by_file.items():
        p = SEED / f"{f}.json"
        raw = p.read_text("utf-8")
        d = json.loads(raw)
        for sid, t in rows:
            _set(d, sid.split("/"), t)
        print("  %s — %d줄" % (p.name, len(rows)))
        if write:
            p.write_text(json.dumps(d, ensure_ascii=False, indent=_indent(raw))
                         + "\n", "utf-8")
    if not write:
        print("(--write 없이 돌렸소 — 아무것도 안 썼소)")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["split", "check", "merge"])
    ap.add_argument("dir")
    ap.add_argument("--budget", type=int, default=40000)
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args()
    d = Path(a.dir)
    if a.cmd == "split":
        split(d, a.budget)
    elif a.cmd == "check":
        check(d)
    else:
        merge(d, a.write)
    return 0


if __name__ == "__main__":
    sys.exit(main())
