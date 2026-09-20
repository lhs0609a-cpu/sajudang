"""Character-specific free depth and the question answered by the paid chapter.

Only advertise chapters actually present in this report. This module never
changes entitlement checks or returns a locked chapter's full text.
"""
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


def free_character_ids(lens_id: str, chapters: list) -> set:
    """Keep the old free sample, then open up to two complete supporting chapters."""
    core = f"lc_{lens_id}_ask2"
    available = [chapter for chapter in chapters if chapter["id"] != core]
    available.sort(key=lambda chapter: not bool(chapter.get("asks")))
    return {chapter["id"] for chapter in available[:3]}


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
