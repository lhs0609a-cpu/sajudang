# -*- coding: utf-8 -*-
"""
화면에서 되돌아갈 길이 있는가.

★ 왜 이걸 지키나

  진입 흐름(a1~a7)은 주소가 `/` 하나 위의 일곱 단계입니다. 상단 화살표가
  `router.back()` 이면 **한 단계 뒤가 아니라 사이트 밖으로** 나갑니다.
  성향 넉 자는 열여섯 칸이 한 줄에 넷씩 붙어 있어 손가락이 미끄러지는데,
  누르는 순간 셈 화면으로 넘어가고 고칠 길이 없었습니다.

  그리고 오류 화면에 버튼이 하나도 없으면 그것도 막다른 길입니다.
  값을 치른 손님일 수 있습니다.
"""
import re
from pathlib import Path

WEB = Path(__file__).resolve().parents[1] / "apps" / "web"


def _screens():
    for p in sorted(list((WEB / "app").rglob("*.tsx")) +
                    list((WEB / "components").rglob("*.tsx"))):
        if p.name == "DevRail.tsx":
            continue
        src = p.read_text(encoding="utf-8")
        src = re.sub(r"/\*.*?\*/", lambda m: "\n" * m.group(0).count("\n"),
                     src, flags=re.S)
        yield p, re.sub(r"//[^\n]*", "", src)


def test_entry_flow_walks_back_one_step():
    """한 주소 위 여러 단계인 화면은 제 손으로 뒤를 잡는다."""
    src = (WEB / "app" / "page.tsx").read_text(encoding="utf-8")
    assert "onBack={back}" in src, "진입 흐름에 되돌아가는 길이 없다"
    # 앞으로 가는 자리는 발자국을 남겨야 한다
    raw = re.sub(r"/\*.*?\*/", " ", src, flags=re.S)
    stray = re.findall(r'setStep\("a\w+"\)', raw)
    # ★ 맨 앞으로 되돌리는 자리는 예외요 (2026-09-05).
    #
    #   진입 흐름은 주소가 `/` 하나요. `?step=` 이 사라지면 맨 앞으로
    #   가야 하는데, 전에는 그걸 안 봐서 `router.push("/")` 를 해도
    #   훅 5단에 그대로 서 있었소 — 손님이 짚은 자리요.
    #
    #   그건 **앞으로 가는 것이 아니라 처음으로 되돌리는 것**이라
    #   발자국을 남기는 게 아니라 비워야 맞소. 비우는지를 봅니다.
    stray = [x for x in stray if x != 'setStep("a1")']
    assert not stray, "발자국 없이 넘어가는 자리: %s" % stray
    reset = re.search(r'setStep\("a1"\);\s*setTrail\(\[\]\);', raw)
    assert reset, "맨 앞으로 되돌리면서 발자국을 안 비우오"


def test_주소가_없으면_맨_앞이다():
    """
    ★ 손님이 짚은 것 (2026-09-05)
      "다음으로 버튼 누르면 맨처음화면으로 가야 하는데 중간지점으로
       가는 포인터가 있어."

      진입 흐름은 주소가 `/` **하나** 위의 여덟 화면이오. 그러니
      `/?step=a7` 에서 `/` 로 밀면 **같은 길이라 화면이 다시 안
      그려지고**, `step` 은 화면이 들고 있는 값이라 아무도 안
      되돌려서 훅 5단에 그대로 서 있었소.

      주소가 곧 자리라야 하오 — 없으면 맨 앞.
    """
    src = (WEB / "app" / "page.tsx").read_text(encoding="utf-8")
    assert "else if (!asked)" in src, "주소가 없을 때를 안 보오"

    # 갈 데를 또렷이 적었는가 — 그냥 `/` 로 밀면 같은 길이라 안 바뀌오
    shell = (WEB / "components" / "Shell.tsx").read_text(encoding="utf-8")
    assert 'router.push("/")' not in shell, "Shell 이 아직 맨 주소로 미오"

    # 자산 판의 포인터도 자리를 또렷이 가리켜야 하오
    board = (WEB / "components" / "AssetBoard.tsx").read_text(encoding="utf-8")
    import re as _re
    a_rows = _re.findall(r'\{ at: "(a\w+)[^"]*", href: "([^"]+)"', board)
    assert a_rows, "자산 판에서 A 구간을 못 찾았소"
    bad = [(i, h) for i, h in a_rows if h != "/?step=%s" % i]
    assert not bad, "가리키는 데가 틀린 포인터: %s" % bad


def test_no_error_screen_is_a_dead_end():
    """오류만 있고 버튼이 없는 화면은 나갈 길이 없다."""
    bad = []
    for p, code in _screens():
        for m in re.finditer(
                r"if\s*\(\s*(?:err|error)\s*\)\s*\{\s*return\s*\(?(.{0,900}?)\n\s*\}",
                code, re.S):
            blk = m.group(1)
            if "<button" not in blk and "router.push" not in blk and \
                    "<Link" not in blk:
                bad.append("%s:%d" % (p.name, code.count("\n", 0, m.start()) + 1))
    assert not bad, "나갈 길 없는 오류 화면: %s" % bad


def test_extra_ask_is_fresh_for_each_character():
    """앞 사람에게 고른 것이 다음 사람에게 실려 가면 안 된다."""
    src = (WEB / "app" / "report" / "[id]" / "page.tsx").read_text(encoding="utf-8")
    assert "key={lensId" in src, "추가 입력 폼이 캐릭터마다 새로 서지 않는다"
    assert "seenLens" in src, "캐릭터가 바뀔 때 앞사람 상태를 안 지운다"


def test_choices_failure_is_not_swallowed():
    """고를 것을 못 받으면 영영 「펴는 중」 이었다."""
    code = dict((p.name, c) for p, c in _screens())["ExtraAsk.tsx"]
    assert ".catch(() => {})" not in code, "실패를 통째로 삼킨다"
    src = (WEB / "components" / "ExtraAsk.tsx").read_text(encoding="utf-8")
    # ★ 문구가 아니라 **길**을 지킵니다.
    #   전에는 "다시 펴 본다" 를 글자 그대로 찾았습니다. 2026-09-02 에
    #   버튼 말투를 합쇼체로 바꾸자("다시 펴 보겠습니다") 길은 그대로인데
    #   검사가 깨졌습니다. 검사가 지켜야 하는 것은 말투가 아닙니다.
    assert "다시 펴" in src, "다시 해 볼 길이 없다"
