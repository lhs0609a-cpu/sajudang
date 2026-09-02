"""
a1~a7 이 사람을 데려가는가 — 심리 장치 전수조사.

    python tools/persuasion_audit.py
    python tools/persuasion_audit.py --why    각 장치가 왜 있는지

★ 왜 이 도구가 필요한가

  「결제율을 올리자」 는 말로는 아무것도 안 고쳐집니다. 무엇을 고칠지
  정하려면 **지금 무엇이 붙어 있고 무엇이 없는지**부터 알아야 합니다.

  그리고 이 집에는 못 쓰는 수단이 있습니다 — 적중률·과학·통계·
  반드시 는 금지고(docs/11), 브레이크는 못 뗍니다. 그러니 남은 수단을
  **하나도 빠뜨리지 않는 것**이 유일한 길입니다.

★ 무엇을 세나 — 열 가지

  진입 흐름 일곱 화면 각각에서, 아래 장치가 실제 글에 있는지 봅니다.
  없다고 다 나쁜 것은 아닙니다(장치마다 맞는 자리가 있습니다). 다만
  **한 화면에 하나도 없으면** 그 화면은 사람을 안 데려갑니다.

★ 결제율에 대하여

  이 도구는 결제율을 예측하지 않습니다. 그건 실측으로만 압니다
  (/v1/funnel). 여기서는 **장치가 붙어 있는가**만 셉니다.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "apps" / "web" / "app" / "page.tsx"

# ★ 화면이 부르는 부품도 함께 봅니다.
#
#   a7 은 훅을 HookSegments 가 그립니다. 공감률·노출 수·「그렇소/아니오」
#   가 전부 거기 있는데, page.tsx 만 보면 그 화면이 텅 빈 것으로 나옵니다.
#   실제로 「증거 0」 이라고 잘못 찍었습니다.
PARTS = {
    "a7": [ROOT / "apps" / "web" / "components" / "HookSegments.tsx"],
    "a6": [ROOT / "apps" / "web" / "components" / "Chart.tsx"],
}

# 진입 흐름 일곱 화면
STEPS = ["a1", "a2", "a3", "a4", "a4b", "a5", "a6", "a7"]
KO = {"a1": "골목", "a2": "이름", "a3": "날·고을", "a4": "때",
      "a4b": "성향 넉 자", "a5": "걸리는 것", "a6": "글자가 서다",
      "a7": "도령이 말하다"}

# ── 심리 장치 열 가지 ───────────────────────────────────────
#
#   말뭉치는 **실제로 그 뜻으로 쓰이는 말**만 넣습니다. 넓게 잡으면
#   아무 화면이나 통과해서 도구가 쓸모없어집니다.
LEVERS = {
    "손실": (
        "손실 회피 — 안 하면 무엇을 잃는가",
        r"잃|놓치|사라지|닫히|없어지|지나가|늦|못 보|다시 못|마지막",
        "사람은 얻는 것보다 잃는 것에 두 배쯤 민감합니다. "
        "「얻는다」로만 말하면 안 눌러도 그만입니다."),
    "궁금": (
        "정보 격차 — 열어 놓고 안 닫은 고리",
        r"있소\?|아시오\?|왜 하필|무엇이|어디|언제 바뀌|뒤에 있|남은|아직",
        "사람은 **열린 고리**를 못 견딥니다. 다 말해 주면 덮습니다."),
    "개입": (
        "일관성 — 작은 「그렇소」를 쌓는다",
        r"그렇소|아니오|맞는지|물어보|고르|적으시|적었|대시오|눌러",
        "제 손으로 답한 것은 제 것이 됩니다. 답이 쌓일수록 "
        "「내가 여기까지 했는데」 가 생깁니다."),
    "구체": (
        "구체성 — 나이·해·개수",
        r"\d+\s*(살|세|년|해|번|명|자|컷|글자|가지)|여덟 글자|넉 자|다섯 마디",
        "「크게 움직이오」 는 아무 말도 아닙니다. 수가 박혀야 "
        "「어떻게 알았지」 가 나옵니다."),
    "증거": (
        "사회적 증거 — 남들은 어떠했는가",
        r"명이 받아|응답|공감|사람이 (?:같|이걸)|중 \d|열에",
        "혼자 판단하게 두면 안 삽니다. 다만 **지어내면 안 됩니다** — "
        "실제 응답이 쌓이기 전에는 노출 수만 냅니다."),
    "진척": (
        "들인 것 — 여기까지 왔다",
        r"Progress|progressAt|여기까지|다 적|남은 자리",
        "들인 수고가 보이면 그만두기 어려워집니다. 진행 막대가 "
        "그 일을 합니다."),
    "선물": (
        "상호성 — 먼저 준다",
        r"값 없이|공짜|먼저|안 받|무료|여기선 값을",
        "받은 것이 있으면 갚고 싶어집니다. 값을 묻기 전에 "
        "**먼저 주는 것**이 이 집의 순서입니다."),
    "희소": (
        "희소도 — 이 배치가 몇 명인가",
        r"드물|희소|몇 명|만에 하나|흔치|보기 드문|드문",
        "「나만 그런가」 는 강한 감정입니다. 다만 **세는 값**이라야 "
        "합니다 — 골라 담으면 누구나 드물어집니다."),
    "자기": (
        "자기 개방 — 손님이 무언가를 내놓았다",
        r"적으신|고르신|그대가 (?:말|적|고)|들었소|말씀하신|오셨다 했|라 했지|고 했지",
        "제 입으로 말한 뒤에는 태도가 바뀝니다. 말하게 하고, "
        "말한 것을 **되짚어** 줍니다."),
    "끝": (
        "정점·종점 — 마지막에 무엇이 남는가",
        r"마지막|이제 마지막|끝|남은 것|여기까지가",
        "기억은 **가장 센 순간과 마지막**이 지배합니다. 끝을 흐리면 "
        "그 앞이 다 좋아도 안 남습니다."),
}


def screens() -> dict:
    """화면마다 손님이 실제로 읽는 글."""
    src = PAGE.read_text(encoding="utf-8")
    code = re.sub(r"/\*.*?\*/", " ", src, flags=re.S)
    code = re.sub(r"//[^\n]*", " ", code)

    out = {}
    marks = [(m.group(1), m.start())
             for m in re.finditer(r'step === "(\w+)"', code)]
    marks.append(("__end__", len(code)))
    for i in range(len(marks) - 1):
        sid, a = marks[i]
        b = marks[i + 1][1]
        if sid not in STEPS:
            continue
        out.setdefault(sid, "")
        out[sid] += code[a:b]

    # ★ 모든 화면이 `step === "xx"` 로 갈리지는 않습니다.
    #
    #   a1 은 맨 위 기본값으로, a7 은 **맨 끝 기본 반환**으로 그려집니다.
    #   처음 판은 그걸 몰라서 둘 다 「장치 0개」 라고 찍었습니다 —
    #   실제로는 훅 머리말·마감이 다 거기 있는데도요.
    #
    #   나누는 표(step === ...)의 앞과 뒤를 각각 a1 · a7 로 봅니다.
    if marks:
        head = code[:marks[0][1]]
        tail_at = marks[-2][1] if len(marks) >= 2 else 0
        last_close = code.rfind("if (step ===")
        tail = code[last_close:] if last_close > 0 else ""
        # 마지막 `if (step === ...)` 블록 **뒤**가 기본 반환입니다
        end = code.find("return (", last_close)
        out["a1"] = out.get("a1", "") + head
        if end > 0:
            out["a7"] = out.get("a7", "") + code[end:]
    return out


def visible(block: str) -> str:
    """태그와 코드를 걷고 사람이 읽는 글만."""
    t = re.sub(r"<[^>]*>", " ", block)
    t = re.sub(r"\{[^{}]*\}", " ", t)
    return " ".join(t.split())


def main() -> int:
    why = "--why" in sys.argv
    sc = screens()

    print("=" * 76)
    print("  a1~a7 — 심리 장치가 붙어 있는가")
    print("=" * 76)
    print()
    print("  %-4s %-11s %s" % ("", "", "  ".join(k for k in LEVERS)))
    print("  " + "-" * 72)

    miss = {}
    for sid in STEPS:
        raw = sc.get(sid, "")
        for extra in PARTS.get(sid, []):
            if extra.exists():
                raw += " " + extra.read_text(encoding="utf-8")
        # 코드도 함께 봅니다 — Progress 같은 장치는 글이 아니라 부품입니다
        txt = visible(raw) + " " + raw
        row, gone = [], []
        for key, (_, pat, _) in LEVERS.items():
            hit = bool(re.search(pat, txt))
            row.append(" ○ " if hit else " · ")
            if not hit:
                gone.append(key)
        miss[sid] = gone
        print("  %-4s %-11s %s" % (sid, KO[sid], "".join(row)))

    print()
    print("  ○ 있음 · (빈칸) 없음")
    print()

    weak = [(s, g) for s, g in miss.items() if len(g) >= 6]
    if weak:
        print("  ★ 장치가 넷 이하인 화면 — 여기서 사람이 나갑니다")
        for s, g in weak:
            print("     %-4s %-11s 없는 것: %s"
                  % (s, KO[s], " · ".join(g)))
        print()

    if why:
        print("  " + "-" * 72)
        for key, (name, _, note) in LEVERS.items():
            print("\n  [%s] %s" % (key, name))
            for line in note.split(" "):
                pass
            print("      " + note)

    print("-" * 76)
    tot = sum(len(g) for g in miss.values())
    print("  화면 %d개 × 장치 %d가지 = %d칸 중 %d칸이 비었습니다"
          % (len(STEPS), len(LEVERS), len(STEPS) * len(LEVERS), tot))
    print("  ※ 다 채우는 것이 목표가 아닙니다. 장치마다 맞는 자리가")
    print("    있습니다. 다만 **한 화면에 서넛뿐이면** 그 화면은")
    print("    사람을 다음으로 안 데려갑니다.")
    print("-" * 76)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
