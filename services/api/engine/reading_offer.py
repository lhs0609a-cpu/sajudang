"""Character-specific free depth and the question answered by the paid chapter.

Only advertise chapters actually present in this report. This module never
changes entitlement checks or returns a locked chapter's full text.
"""
import re
from typing import Optional

from . import topic as topic_mod

_TAGS = re.compile(r"<[^>]+>")


def _plain(markup: str) -> str:
    return _TAGS.sub("", markup or "")


QUESTIONS = {
    "pungun": "반복하는 문제에서, 무엇부터 바꿔야 할까?",
    "baegun": "지금 내게 부족한 것을 어떤 순서로 채울까?",
    "cheongam": "내가 오래 힘을 쓸 수 있는 일의 조건은 무엇일까?",
    "sigye": "시기 흐름이 달라질 때, 어떤 선택 기준을 세울까?",
    "eunbyeol": "내가 생각하는 나와 실제로 애쓰는 모습은 어디서 다를까?",
    "jeokhyeol": "끌림을 따라갈 때, 내가 놓치기 쉬운 것은 무엇일까?",
    "monghwa": "사주에 붙은 이름을 내 고민에서는 어떻게 읽어야 할까?",
    "seoyeok": "익숙한 환경을 떠나는 고민을 어떤 관점에서 살펴볼까?",
    "paeseon": "뽑은 패와 사주의 해석을 내 선택에 어떻게 연결할까?",
    "myeonsang": "내가 고른 인상과 사주를 함께 보면 무엇이 다를까?",
    "wolha": "관계에서 내가 원하는 것과 반복하는 행동은 어떻게 다를까?",
    "hongmae": "오래 함께하는 관계를 위해 어떤 조건부터 맞춰볼까?",
    "yeondam": "지나간 관계에서 내가 정리할 몫은 무엇일까?",
    "hwagyeong": "부딪히는 관계에서 내 몫과 상대의 몫을 어떻게 구분할까?",
    "haengsu": "돈을 벌고 지키는 방식을 내 생활에서 어떻게 바꿔볼까?",
    "hunjang": "내가 익히고 실행하는 순서를 어떻게 잡을까?",
    "yakcho": "생활의 균형을 위해 하루에 무엇 하나부터 바꿔볼까?",
    "ilgwan": "날짜를 고를 때 사주가 말하는 범위와 현실 조건을 어떻게 나눌까?",
    "nopa": "갈림길에서 감당할 몫과 내려놓을 몫을 어떻게 정할까?",
    "dongja": "오늘은 무엇 하나를 내려놓아도 괜찮을까?",
}


def free_character_ids(lens_id: str, chapters: list,
                       concern: Optional[str] = None) -> set:
    """
    값을 치르기 전에 열어 줄 그 사람의 컷.

    ★ **물은 자리를 딛는 컷**부터 엽니다 (2026-09-20 · docs/45).

      전에는 「맨 앞에서 셋」이었습니다. 정렬 열쇠로 둔 `asks` 는
      어느 컷에도 없는 키라 정렬이 아무것도 안 했고, 그래서 돈을 물은
      사람에게 「뿌리가 있는가」(620자)와 「힘이 빠져나가는 곳」(494자)이
      맛보기로 나갔습니다 — **둘 다 돈이라는 말을 한 번도 안 합니다.**
      조사에서 나온 불만 그대로입니다: 「돈을 물었는데 돈 얘기가 없다」.

      `report.py` 에 이미 같은 사고가 한 번 적혀 있었습니다(§1502).
      그때 고친 규칙이 지워져 있었던 것이라, 규칙을 자와 함께 둡니다 —
      무엇이 「물은 자리를 딛는 컷」인지는 `engine/topic.mentions` 가
      정하고, `tools/topic_reach` 가 같은 표로 잽니다.

    ★ 안 여는 것이 **덜 주는 것이 아닙니다.** 물은 것과 무관한 긴 글을
      공짜로 얹으면 그건 양이 아니라 소음이고, 「무료와 유료가 같다」는
      말이 거기서 나옵니다. 남는 컷은 값을 치른 자리에서 제 몫을 합니다.
    """
    core = f"lc_{lens_id}_ask2"
    available = [chapter for chapter in chapters if chapter["id"] != core]
    if not available:
        return set()
    if not concern:
        return {chapter["id"] for chapter in available[:1]}

    # 길이로는 못 가릅니다. 관점 컷은 조립 뒤에 괄호 풀이 · 비유 상자 ·
    # 강조가 더 붙어 200자쯤 자랍니다 — 여기서 「짧으니 괜찮다」고 열면
    # 화면에서는 긴 글이 됩니다. **물은 자리를 부르는가**만 봅니다.
    picked = [chapter for chapter in available
              if topic_mod.mentions(_plain(chapter.get("html", "")), concern)][:3]
    # 하나도 못 고르면 **가장 짧은 것** 하나만 엽니다. 긴 것을 억지로
    # 열면 그 자리에서 자가 걸립니다 — 자를 속이지 말고 덜 엽니다.
    if not picked:
        picked = sorted(available,
                        key=lambda c: len(_plain(c.get("html", ""))))[:1]
    return {chapter["id"] for chapter in picked}


def build(lens_id: str, cuts: list, locked: list, sells: bool) -> dict:
    free_ids = [cut["id"] for cut in cuts if cut["id"].startswith(f"lc_{lens_id}_")]
    core_id = f"lc_{lens_id}_ask2"
    core = next((cut for cut in locked if cut["id"] == core_id), None)
    paid = [cut["id"] for cut in locked if cut["id"].startswith(f"lc_{lens_id}_")]
    if core:
        paid = [core_id] + [cid for cid in paid if cid != core_id]
    return {"question": QUESTIONS[lens_id], "free_ids": free_ids,
            "core_id": core_id if core and sells else None,
            "paid_ids": paid if sells else [], "free_only": not sells}
