"""A free, complete action for the selected concern, not a chart prediction.

Only the selected rendered suggestion is returned; the bank stays server-side.
"""
from engine import guard

VERSION = 1
SOURCE = "선택한 고민에 따른 일반적인 실천 제안 · 사주 계산 결과가 아닙니다"
PRACTICES = {
    "love": ("서운함과 바라는 행동을 나눠보세요",
             "최근 관계에서 마음에 남은 장면이 있다면, 상대를 설명하기 전에 내 경험부터 적어보세요.",
             "서운했던 사실 한 문장과 다음에 원하는 행동 한 문장을 따로 적어보세요. 그런 장면이 없다면 이 제안은 건너뛰어도 괜찮아요."),
    "work": ("잘하는 일과 맡은 일을 구분해보세요",
             "추가 요청 때문에 내 일이 밀렸던 경험이 있다면, 능력보다 담당 범위를 확인해볼 수 있어요.",
             "이번 주 담당 업무와 추가로 받은 요청을 나눠 적고, 함께 끝내기 어렵다면 어느 일을 먼저 할지 확인해보세요."),
    "money": ("소비 직전의 상황을 적어보세요",
              "작은 보상 같은 소비가 반복된다면 금액만큼 그때의 상황도 살펴볼 수 있어요.",
              "최근 소비 하나를 골라 필요했던 이유와 당시 기분을 적어보세요. 다음 구매 전에 확인할 기준 하나만 정해보세요."),
    "health": ("오늘의 끝을 작게 정해보세요",
               "쉬는 시간에도 남은 일을 계산하는 경험이 있다면, 하루의 경계를 먼저 정해볼 수 있어요.",
               "오늘 마칠 일 하나와 내일로 미룰 일 하나를 구분해 적어보세요. 이 제안은 질병이나 몸 상태에 대한 판단이 아닙니다."),
    "people": ("내가 할 수 있는 범위를 말해보세요",
               "부탁을 받은 뒤 내 일정이 자주 밀렸다면, 거절 여부보다 가능한 범위를 먼저 정해볼 수 있어요.",
               "부탁 하나를 떠올리고 해줄 수 있는 범위와 어려운 부분을 한 문장씩 적어보세요. 상대를 평가하는 말 대신 내 시간과 상황을 설명해보세요."),
    "dir": ("선택 뒤에 남는 비용을 적어보세요",
            "비교할수록 결정이 어려웠다면, 정보가 부족한지 포기할 것이 부담스러운지 나눠볼 수 있어요.",
            "두 선택에서 지키고 싶은 것 하나와 포기할 것 하나를 적어보세요. 되돌릴 수 있는 작은 시도를 정하고 언제 돌아볼지도 적어두세요."),
}


def build(concern: str) -> dict | None:
    row = PRACTICES.get(concern)
    if row is None:
        return None
    title, scene, action = row
    return {"id": f"practice:{VERSION}:{concern}", "version": VERSION,
            "source_kind": "general_practice", "source": SOURCE,
            **{key: guard.enforce(text, {"cut": "practice"})
               for key, text in (("title", title), ("scene", scene), ("action", action))}}
