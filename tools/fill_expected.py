"""
회귀 50건의 기대값을 채운다 — 손으로 옮겨 적지 않는다.

    python tools/fill_expected.py 받아적은것.txt          # 대조 결과만 보여줌
    python tools/fill_expected.py 받아적은것.txt --write   # fixtures 에 써넣음
    python tools/fill_expected.py --plan                  # 무엇부터 볼지

왜 이 도구가 있는가
    50줄을 손으로 옮기면 반드시 틀립니다. 그리고 어디를 틀렸는지
    알 수도 없습니다. 붙여넣기만 하면 대조까지 해 줍니다.

받아적는 형식 — 한 줄에 한 건. 사이에 뭐가 끼어 있어도 됩니다.

    jieqi-01  戊辰 甲寅 丁巳 己酉  1
    jieqi-02  戊辰 乙卯 辛酉 丁酉
    zi-01     乙丑 己卯 庚戌 丁亥  2

    · 맨 앞이 id, 그 뒤 여덟 글자(네 기둥), 끝에 대운수(있으면).
    · 시각 미상 건의 시주는 ◇◇ 또는 - 로 적으세요.
    · 대운수를 안 적으면 그 항목은 비교하지 않습니다.

★ 두 곳 이상에서 읽으세요.
  한 곳만 보고 맞추면 그 앱의 유파를 그대로 베끼는 것입니다.
"""
from __future__ import annotations

import io
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIX = ROOT / "tests" / "fixtures" / "charts.json"

GAN = "甲乙丙丁戊己庚辛壬癸"
JI = "子丑寅卯辰巳午未申酉戌亥"
GZ = re.compile("[%s][%s]" % (GAN, JI))

# ── 어디부터 봐야 하는가 ──────────────────────────────────
#
# 50건이 다 같은 무게가 아닙니다. 앞의 것부터 보세요.
PRIORITY = [
    ("ipchun", 1, "입춘 경계 — 년주가 통째로 갈립니다. 여기가 틀리면 전부 틀립니다."),
    ("jieqi", 1, "절입 경계 — 월주가 갈립니다. 대운수도 여기서 나옵니다."),
    ("zi", 2, "자시 경계 — 일주가 갈립니다. **유파가 갈리는 자리**(조자시/야자시)."),
    ("dst", 2, "서머타임 — 시주가 한 시간 밀립니다. 안 넣은 앱이 많습니다."),
    ("std1275", 3, "1954~1961 표준시 127.5° — 아주 오래된 건입니다."),
    ("plain", 3, "평범한 건 — 여기가 틀리면 기본이 틀린 것입니다."),
]

# 유파에 따라 갈릴 수 있는 묶음. 여기서 다르다고 곧 버그는 아닙니다.
SCHOOL = {
    "zi": "조자시/야자시 — 우리는 조자시(23시부터 다음 날). 앱이 다르면 일주가 하루 다릅니다.",
    "jieqi": "진태양시 보정 후 절입과 비교합니다(JIEQI_BASIS=corrected). "
             "표준시로 비교하는 앱과는 서울 기준 절입 직후 32분 구간에서 갈립니다.",
}


def cases() -> list:
    return json.loads(FIX.read_text(encoding="utf-8"))


def ours() -> dict:
    sys.path.insert(0, str(ROOT / "services" / "api"))
    from engine.calendar import build_chart          # noqa: E402
    out = {}
    for c in cases():
        i = c["input"]
        ch = build_chart(
            i["year"], i["month"], i["day"],
            i.get("hour") if i.get("hour_known", True) else None,
            i.get("minute") if i.get("hour_known", True) else None,
            i["sex"], hour_known=i.get("hour_known", True),
            city=i.get("city", "서울"))
        p = [x.gz for x in ch.pillars] if hasattr(ch.pillars[0], "gz") else \
            [x["gz"] for x in ch.pillars]
        out[c["id"]] = {
            "pillars": p,
            "hour_known": i.get("hour_known", True),
            # 대운수는 첫 대운의 시작 나이입니다 (fixture_sheet.py 와 같은 자리)
            "daeun_start_age": ch.daeun[0].start_age if ch.daeun else None,
        }
    return out


def plan() -> int:
    by = Counter(c["id"].rsplit("-", 1)[0] for c in cases())
    print("=" * 70)
    print("  회귀 50건 — 무엇부터 보면 되는가")
    print("=" * 70)
    print()
    print("  한 번에 다 하지 마세요. 1순위 20건만 맞아도 8글자는 믿을 만합니다.")
    print()
    for group, pri, why in PRIORITY:
        print("  [%d순위] %-9s %2d건" % (pri, group, by.get(group, 0)))
        print("           %s" % why)
        if group in SCHOOL:
            print("           ※ %s" % SCHOOL[group])
        print()
    print("  " + "-" * 66)
    print()
    print("  ① 대조표.md 를 여세요 (없으면: python tools/fixture_sheet.py)")
    print("  ② 만세력 앱 **두 곳 이상**에서 같은 생일을 넣고 여덟 글자를 읽으세요")
    print("  ③ 아래 형식으로 받아적고 이 도구에 물리세요")
    print()
    print("       jieqi-01  戊辰 甲寅 丁巳 己酉  1")
    print()
    print("     python tools/fill_expected.py 받아적은것.txt")
    print()
    return 0


def parse(path: Path) -> dict:
    ids = {c["id"] for c in cases()}
    out = {}
    for lineno, raw in enumerate(io.open(path, encoding="utf-8"), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        head = line.split()[0].strip(":|,")
        if head not in ids:
            continue
        gz = GZ.findall(line)
        unknown = bool(re.search(r"◇◇|시각\s*미상", line))
        if len(gz) == 3 and unknown:
            gz = gz + [None]
        if len(gz) != 4:
            print("  %d행 %s — 기둥을 %d개만 읽었습니다. 건너뜁니다."
                  % (lineno, head, len(gz)))
            continue
        # 대운수는 **마지막 기둥 뒤**에서 찾습니다. 줄 끝만 보면 뒤에
        # 메모가 붙었을 때 못 읽고, 줄 전체를 보면 생년월일의 숫자를 줍습니다.
        # 시각 미상이면 gz[-1] 이 None 이므로 **실제로 읽은 마지막 기둥**을
        # 씁니다. 줄 전체를 훑으면 id 의 "plain-03" 에서 3 을 집어 옵니다.
        last = next((g for g in reversed(gz) if g), None)
        after = line[line.rindex(last) + 2:] if last else line
        tail = re.findall(r"(?<![0-9])([0-9]{1,2})(?![0-9])", after)
        out[head] = {"pillars": gz,
                     "daeun_start_age": int(tail[0]) if tail else None}
    return out


# ══════════════════════════════════════════════════════════
# 독립 계산으로 채우기
# ══════════════════════════════════════════════════════════
#
# ★ 이건 만세력 앱 대조를 **대신하지 않습니다.**
#
#   tools/crosscheck.py 는 sxtwl 을 한 줄도 쓰지 않는 두 번째 계산으로
#   여덟 글자를 다시 짭니다(절입은 Meeus 로 직접 품). 그게 엔진과
#   전부 일치하면, 그 값을 기대값으로 박아 **회귀를 잠글** 수 있습니다.
#   앞으로 엔진을 고치다 여덟 글자가 달라지면 테스트가 잡습니다.
#   지금처럼 50건이 통째로 skip 되는 것보다는 확실히 낫습니다.
#
#   다만 두 계산은 **같은 유파를 공유합니다** — 조자시 정책과 절입
#   비교 기준(진태양시 보정 후). 그건 계산이 아니라 **선택**이라
#   바깥에서 봐야 압니다. 그래서 유파가 갈리는 건에는 표를 남기고,
#   `--plan` 이 계속 그 건들을 1·2순위로 세웁니다.
#
#       python tools/fill_expected.py --from-crosscheck          # 보기만
#       python tools/fill_expected.py --from-crosscheck --write  # 써넣음

SOURCE_CROSSCHECK = "crosscheck"      # 독립 계산
SOURCE_APP = "만세력앱"                # 사람이 바깥에서 읽어온 값


def from_crosscheck() -> tuple[dict, list]:
    """(id → 기대값, 어긋난 건). crosscheck 의 독립 계산을 씁니다."""
    sys.path.insert(0, str(ROOT))
    sys.path.insert(0, str(ROOT / "services" / "api"))
    from engine.calendar import build_chart              # noqa: E402
    from tools import crosscheck as CC                   # noqa: E402

    out, bad = {}, []
    for c in cases():
        i = c["input"]
        ch = build_chart(
            i["year"], i["month"], i["day"],
            i.get("hour") if i.get("hour_known", True) else None,
            i.get("minute") if i.get("hour_known", True) else None,
            i["sex"], hour_known=i.get("hour_known", True),
            city=i.get("city", "서울"))
        theirs = CC.rebuild(ch).split()
        mine_gz = [p.gz for p in ch.pillars]
        if theirs != mine_gz:
            bad.append((c["id"], mine_gz, theirs))
            continue
        out[c["id"]] = {
            "pillars": theirs + ([None] if len(theirs) == 3 else []),
            "daeun_start_age": ch.daeun[0].start_age if ch.daeun else None,
        }
    return out, bad


def write_expected(filled: dict, source: str) -> int:
    data = cases()
    n = 0
    for c in data:
        w = filled.get(c["id"])
        if not w:
            continue
        p = w["pillars"]
        c["expected"] = {
            "year": p[0], "month": p[1], "day": p[2],
            "hour": p[3] if len(p) > 3 else None,
            "daeun_start_age": w["daeun_start_age"],
        }
        c["expected_source"] = source
        group = c["id"].rsplit("-", 1)[0]
        if group in SCHOOL:
            # 유파가 갈리는 자리. 독립 계산으로 채워도 **바깥 확인은 남습니다.**
            c["needs_external_check"] = SCHOOL[group]
        n += 1
    io.open(FIX, "w", encoding="utf-8", newline="\n").write(
        json.dumps(data, ensure_ascii=False, indent=1) + "\n")
    return n


def run_crosscheck_fill() -> int:
    filled, bad = from_crosscheck()
    print("=" * 74)
    print("  독립 계산으로 채우기 — tools/crosscheck.py 의 두 번째 계산")
    print("=" * 74)
    print()
    print("  일치 %d건 · 어긋남 %d건" % (len(filled), len(bad)))
    if bad:
        print()
        print("  ── 두 계산이 다른 건 — 채우지 않습니다 ──")
        for cid, a, b in bad:
            print("  %-11s 엔진 %s" % (cid, " ".join(a)))
            print("  %-11s 독립 %s" % ("", " ".join(b)))
        print()
        print("  ★ 먼저 왜 다른지 보세요. 여기가 어긋나면 나머지가 무의미합니다.")
        return 1

    school = sorted({c["id"].rsplit("-", 1)[0] for c in cases()} & set(SCHOOL))
    n_school = sum(1 for c in cases() if c["id"].rsplit("-", 1)[0] in SCHOOL)
    print()
    print("  ★ 이걸로 끝난 게 아닙니다.")
    print("    두 계산은 같은 유파를 씁니다. 유파가 갈리는 %d건(%s)은"
          % (n_school, ", ".join(school)))
    print("    만세력 앱 두 곳 이상에서 확인해야 합니다. 표를 남겨 둡니다.")
    print("    (.\\dev.ps1 plan · .\\dev.ps1 sheet)")
    print()

    if "--write" not in sys.argv:
        print("  아직 아무것도 안 썼습니다. 넣으려면 --write 를 붙이세요.")
        return 0
    n = write_expected(filled, SOURCE_CROSSCHECK)
    print("  %d건을 채웠습니다 → %s" % (n, FIX))
    return 0


def main() -> int:
    if "--from-crosscheck" in sys.argv:
        return run_crosscheck_fill()
    if "--plan" in sys.argv or len(sys.argv) < 2:
        return plan()

    src = Path(sys.argv[1])
    if not src.exists():
        print("파일이 없습니다: %s" % src)
        return 1

    got = parse(src)
    mine = ours()
    if not got:
        print("읽어낸 게 없습니다. 형식을 보세요:")
        print("  jieqi-01  戊辰 甲寅 丁巳 己酉  1")
        return 1

    print("=" * 74)
    print("  대조 — 받아적은 %d건" % len(got))
    print("=" * 74)
    print()
    same, diff, dae_diff = [], [], []
    for cid, want in sorted(got.items()):
        ourp = mine[cid]["pillars"]
        theirs = want["pillars"]
        bad = [i for i in range(4)
               if theirs[i] is not None and theirs[i] != ourp[i]]
        if bad:
            diff.append((cid, ourp, theirs, bad))
        else:
            same.append(cid)
        w = want["daeun_start_age"]
        if w is not None and mine[cid]["daeun_start_age"] != w:
            dae_diff.append((cid, mine[cid]["daeun_start_age"], w))

    print("  맞음 %d · 다름 %d · 대운수 다름 %d" % (len(same), len(diff), len(dae_diff)))
    LABEL = ["년주", "월주", "일주", "시주"]
    if diff:
        print()
        print("  ── 여덟 글자가 다른 건 ──")
        for cid, ourp, theirs, bad in diff:
            group = cid.rsplit("-", 1)[0]
            print("  %-11s 우리 %s" % (cid, " ".join(ourp)))
            print("  %-11s 받아 %s   ← %s 다름"
                  % ("", " ".join(x or "◇◇" for x in theirs),
                     "·".join(LABEL[i] for i in bad)))
            if group in SCHOOL:
                print("              ※ %s" % SCHOOL[group])
            print()
    if dae_diff:
        print("  ── 대운수가 다른 건 ──")
        for cid, o, w in dae_diff:
            print("  %-11s 우리 %s · 받아 %s" % (cid, o, w))
        print()

    if "--write" not in sys.argv:
        print("  아직 아무것도 안 썼습니다. 넣으려면 --write 를 붙이세요.")
        if diff:
            print("  ★ 다른 건이 있습니다. 먼저 왜 다른지 보고 나서 쓰세요.")
        return 0

    if diff:
        print("  ★ 다른 건이 남아 있어 쓰지 않았습니다.")
        print("    유파 차이라면 그 건을 받아적은 파일에서 빼고 다시 쓰세요.")
        return 1

    # 사람이 바깥에서 읽어온 값입니다. 독립 계산으로 채운 것과 구별해
    # 표시하고, 유파 표시는 지웁니다 — 이 건은 실제로 바깥에서 봤습니다.
    n = write_expected(got, SOURCE_APP)
    data = cases()
    for c in data:
        if c["id"] in got:
            c.pop("needs_external_check", None)
    io.open(FIX, "w", encoding="utf-8", newline="\n").write(
        json.dumps(data, ensure_ascii=False, indent=1) + "\n")
    print("  %s 에 %d건을 채웠습니다." % (FIX.relative_to(ROOT), n))
    print()
    print("  이제:  .\\dev.ps1 engine-check")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
