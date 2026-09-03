"""
뱅크를 하오체 한 벌로 되돌린다.

    python tools/to_hao.py seed/lens_cuts.json          # 대조만
    python tools/to_hao.py seed/lens_cuts.json --write  # 써넣기

★ 왜 되돌리는가 (2026-09-03)

  이 집의 규칙은 「뱅크는 하오체 한 벌로 쓰고 `engine.voice.speak` 가
  맨 끝에서 어미만 갈아 끼운다」 입니다. 그런데 관점 컷 여섯 사람 분이
  **손으로 그 사람 말투에 가깝게** 쓰여 있었습니다. 그러면 두 가지가
  깨집니다 —

    ① speak 가 손댈 자리가 없어 그 문장만 굳습니다
    ② 손으로 쓴 것이라 한 사람 안에서 결이 섞입니다
       은별 무녀(해요체)의 컷은 합쇼체 198 · 해요체 123 이었고,
       한 문장 안에서도 「…편이에요. …다닙니다. …반복돼요.」 였습니다

★ 어간을 지어내지 않습니다 — 못 돌리면 그대로 둡니다.

  되돌리기는 활용을 **거꾸로** 푸는 일이라 불규칙이 더 위험합니다.
  「들어요」 를 「들소」 로 돌리면 비문이 됩니다(듣다 → 드오). 그래서
  받침이 ㄷ·ㅅ·ㅂ·ㅎ·ㄹ 인 어간은 손대지 않습니다. 못 돌린 것은
  세어서 알려 줍니다 — 그건 사람이 고쳐야 하는 자리입니다.
"""
from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services" / "api"))

from engine import voice as V                          # noqa: E402

_BASE, _LAST, _JONG = 0xAC00, 0xD7A3, 28

# 「지」 로 끝나는 이름 — 어미로 잘못 읽으면 안 된다
_NOUN_JI = ("일지", "월지", "년지", "시지", "간지", "지지")

# 되돌리면 불규칙이 튀는 받침 — ㄷ ㄹ ㅂ ㅅ ㅎ
_UNSAFE_JONG = {7, 8, 17, 19, 27}


def _jong(ch: str):
    o = ord(ch)
    if not (_BASE <= o <= _LAST):
        return None
    return (o - _BASE) % _JONG


def _drop_bieup(ch: str):
    """ㅂ 받침을 뗀다. 합 → 하 · 릅 → 르"""
    o = ord(ch)
    if not (_BASE <= o <= _LAST) or (o - _BASE) % _JONG != 17:
        return None
    return chr(o - 17)


def _plain(stem: str):
    """어간에 하오체 어미를 단다. 못 달면 None."""
    j = _jong(stem[-1]) if stem else None
    if j is None:
        return None
    return stem + ("소" if j else "오")


# 통째로 바꾸는 것 — 줄어드는 꼴이라 규칙으로는 못 푼다
_WHOLE = {
    "해요": "하오", "해": "하오", "돼요": "되오", "예요": "요",
    "이에요": "이오", "이야": "이오", "거지": "것이오", "거예요": "것이오",
    "일세": "이오", "입니다": "이오", "입니까": "이오", "이네": "이오",
    "거야": "것이오", "겁니다": "것이오", "건가": "것이오",
    "아니에요": "아니오", "봐요": "보오", "와요": "오오",
}


def to_hao(w: str):
    """낱말 하나를 하오체로. 못 돌리면 None."""
    # ★ 태그 밖에 어미만 남은 자리 — 「<b>나무</b>야.」 「<b>酉</b>야.」
    #   받침 있는 이름 뒤에는 「이야」 로 쓰므로, 홀로 남은 「야」 는
    #   언제나 받침 없는 이름 뒤입니다. 그래서 「요」 로 돌립니다.
    #   「네 · 지 · 죠」 는 어간이 태그 안에 있어 받침을 못 보므로
    #   손대지 않습니다 — 「있네」 를 「있오」 로 만들면 비문입니다.
    if w == "야":
        return "요"
    if len(w) < 2:
        return None
    for tail, rep in _WHOLE.items():
        if w.endswith(tail) and len(w) > len(tail):
            return w[:-len(tail)] + rep
        if w == tail:
            return rep

    # ── 합쇼체 ─────────────────────────────────────────
    for tail in ("습니다", "습니까"):
        if w.endswith(tail):
            return w[:-3] + "소"
    for tail in ("니다", "니까"):
        # ★ 「셉니다 · 봅니다 · 갑니다」 는 세 글자입니다. >3 으로 두면
        #   가장 잦은 꼴이 통째로 안 돌아갑니다.
        if w.endswith(tail) and len(w) >= 3:
            made = _drop_bieup(w[-3])
            if made:
                return w[:-3] + made + "오"
    if w.endswith("십시오"):
        return w[:-3] + "시오"
    if w.endswith("세요"):
        return w[:-2] + "시오"

    # ── 하게체 · 해요체 · 반말의 종결 ───────────────────
    # 반말의 「…야」 — 자리야 · 아니야 · 戊야 · 때야
    if w.endswith("야") and len(w) > 1:
        stem = w[:-1]
        j = _jong(stem[-1])
        return stem + ("이오" if j else "요")

    # ★ 「지」 로 끝나는 **이름**이 있습니다 — 일지 · 월지 · 년지 · 시지.
    #   「일지예요」 에서 지를 떼면 「일소」 가 됩니다. 실제로 두 자리를
    #   그렇게 망가뜨렸습니다. 이름은 건너뜁니다.
    if any(w.startswith(x) for x in _NOUN_JI):
        for tail in ("예요", "이에요", "요", "입니다"):
            if w.endswith(tail):
                return w[:-len(tail)] + "요"
        return None

    for tail in ("지요", "네요", "나요", "네", "나", "죠", "지"):
        if w.endswith(tail) and len(w) > len(tail):
            return _plain(w[:-len(tail)])

    # ── 아요 / 어요 · 반말의 아 / 어 — 받침이 성한 어간만 ──
    if len(w) > 2 and w[-1] == "요" and w[-2] in "아어":
        j = _jong(w[-3])
        if j and j not in _UNSAFE_JONG:
            return w[:-2] + "소"
    if len(w) > 1 and w[-1] in "아어":
        j = _jong(w[-2])
        if j and j not in _UNSAFE_JONG:
            return w[:-1] + "소"
    return None


# ★ 되돌릴 때는 **진짜 문장부호가 있는 자리**만 봅니다.
#
#   voice._ENDING 은 태그 앞(글 조각의 끝)도 문장 끝으로 셉니다.
#   내보낼 때는 그게 맞습니다 — 「…이렇소<b>」 처럼 끝나니까요.
#   그런데 되돌릴 때 같은 자리를 보면 「…하지 <b>않소</b>」 의
#   **연결어미 「하지」** 를 종결로 잘못 읽어 「하오 않소」 가 됩니다.
#   되돌리기는 한 번 틀리면 사람이 못 찾으므로 좁게 봅니다.
_ENDING = re.compile(r"([^\s.!?…—–〔]+)(?=\s*(?:[.!?…]|〔))")
_TAG = re.compile(r"<[^>]*>")


def fix(html: str, stats: Counter):
    """HTML 안쪽 문장 끝만 하오체로. 태그는 손대지 않는다."""
    def one(text):
        def sub(m):
            w = m.group(1)
            if V._word(w, V.HAPSYO) != w:
                stats["이미 하오체"] += 1
                return w                       # 이미 speak 가 손대는 꼴
            got = to_hao(w)
            if got is None:
                stats["못 돌림"] += 1
                stats["못 돌림 낱말:" + w] += 1
                return w
            stats["돌림"] += 1
            return got
        return _ENDING.sub(sub, text)

    out, last = [], 0
    for m in _TAG.finditer(html):
        out.append(one(html[last:m.start()]))
        out.append(m.group(0))
        last = m.end()
    out.append(one(html[last:]))
    return "".join(out)


def walk(o, stats):
    if isinstance(o, str):
        return fix(o, stats)
    if isinstance(o, dict):
        return {k: walk(v, stats) for k, v in o.items()}
    if isinstance(o, list):
        return [walk(v, stats) for v in o]
    return o


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    path = Path(sys.argv[1])
    write = "--write" in sys.argv
    only = [a for a in sys.argv[2:] if not a.startswith("--")]

    data = json.loads(path.read_text(encoding="utf-8"))
    cuts = data.get("cuts", data)
    stats = Counter()
    changed = []
    for lid in list(cuts):
        if lid == "_" or (only and lid not in only):
            continue
        before = json.dumps(cuts[lid], ensure_ascii=False)
        s = Counter()
        cuts[lid] = walk(cuts[lid], s)
        after = json.dumps(cuts[lid], ensure_ascii=False)
        stats.update(s)
        if before != after:
            changed.append((lid, s["돌림"], s["못 돌림"]))

    print("=" * 72)
    print("  하오체로 되돌리기 — %s" % path)
    print("=" * 72)
    print()
    for lid, ok, no in sorted(changed, key=lambda r: -r[1]):
        print("     %-11s 돌림 %4d   못 돌림 %4d" % (lid, ok, no))
    print()
    print("     돌림 %d · 못 돌림 %d · 이미 하오체 %d"
          % (stats["돌림"], stats["못 돌림"], stats["이미 하오체"]))
    print()
    stuck = Counter({k.split(":", 1)[1]: v for k, v in stats.items()
                     if k.startswith("못 돌림 낱말:")})
    if stuck:
        print("  ★ 못 돌린 낱말 %d가지 — 사람이 고쳐야 하는 자리입니다"
              % len(stuck))
        for w, n in stuck.most_common(30):
            print("       %4d  %s" % (n, w))
    print()
    if write:
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n",
                        encoding="utf-8")
        print("  써넣었습니다: %s" % path)
    else:
        print("  대조만 했습니다. 써넣으려면 --write")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
