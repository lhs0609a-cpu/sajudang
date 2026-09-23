"""A free, complete action for the selected concern, not a chart prediction.

Only the selected rendered suggestion is returned; the bank stays server-side.
"""
from engine import guard

VERSION = 2
SOURCE = "선택한 고민에 따른 일반적인 실천 제안 · 사주 계산 결과가 아니오"
PRACTICES = {
    "love": ("서운함과 바라는 행동을 나눠보시오",
             "최근 관계에서 마음에 남은 장면이 있다면, 상대를 설명하기 전에 내 경험부터 적어보시오.",
             "서운했던 사실 한 문장과 다음에 원하는 행동 한 문장을 따로 적어보시오. 그런 장면이 없다면 이 제안은 건너뛰어도 괜찮소."),
    "work": ("잘하는 일과 맡은 일을 구분해보시오",
             "남이 더 맡긴 일 때문에 내 일이 밀렸던 적이 있다면, 내 실력보다 내가 맡은 일이 어디까지인지 먼저 확인해볼 수 있소.",
             "이번 주 담당 업무와 추가로 받은 요청을 나눠 적고, 함께 끝내기 어렵다면 어느 일을 먼저 할지 확인해보시오."),
    "money": ("소비 직전의 상황을 적어보시오",
              "작은 보상 같은 소비가 반복된다면 금액만큼 그때의 상황도 살펴볼 수 있소.",
              "최근 소비 하나를 골라 필요했던 이유와 당시 기분을 적어보시오. 다음 구매 전에 확인할 기준 하나만 정해보시오."),
    "health": ("오늘의 끝을 작게 정해보시오",
               "쉬는 시간에도 남은 일을 자꾸 세고 있다면, 하루를 몇 시에 끝낼지 먼저 정해볼 수 있소.",
               "오늘 마칠 일 하나와 내일로 미룰 일 하나를 구분해 적어보시오. 이 제안은 질병이나 몸 상태에 대한 판단이 아니오."),
    "people": ("내가 할 수 있는 범위를 말해보시오",
               "부탁을 받은 뒤 내 일정이 자주 밀렸다면, 거절 여부보다 가능한 범위를 먼저 정해볼 수 있소.",
               "부탁 하나를 떠올리고 해줄 수 있는 범위와 어려운 부분을 한 문장씩 적어보시오. 상대를 평가하는 말 대신 내 시간과 상황을 설명해보시오."),
    "dir": ("고른 뒤에 내려놓을 것을 적어보시오",
            "견줄수록 고르기가 어려웠다면, 아는 게 모자란 것인지 포기할 것이 아까운 것인지 나눠볼 수 있소.",
            "두 선택에서 지키고 싶은 것 하나와 포기할 것 하나를 적어보시오. 되돌릴 수 있는 작은 시도를 정하고 언제 돌아볼지도 적어두시오."),
}


STEPS = {
    'money': ('최근 결제 내역 하나를 펴고, 물건 이름 옆에 사기 직전의 상황을 적으시오.', '“지금 필요한 것인가, 오늘의 기분을 바꾸고 싶은 것인가”를 묻고 다음 구매의 기준을 한 줄 적으시오.', '오늘 밤에는 덜 쓴 금액보다 구매 전에 한 번 멈춰봤는지 확인하시오.'),
    'work': ('오늘 받은 요청 하나와 원래 하던 일의 마감 시각을 나란히 적으시오.', '“이 일을 먼저 하면 기존 일은 내일 끝납니다. 어느 쪽부터 할까요?”처럼 순서를 확인할 문장을 만들어 보시오.', '오늘 밤에는 일을 모두 끝냈는지보다, 끝낼 범위와 순서를 확인했는지 보시오.'),
    'love': ('마음에 남은 대화 하나에서 실제로 들은 말만 적으시오. 상대의 속뜻은 빈칸으로 두시오.', '“연락이 없어서 서운했어. 바쁜 날에는 나중에 연락한다고 알려줄 수 있어?”처럼 바라는 행동을 한 가지로 좁혀보시오.', '오늘은 상대를 설득했는지가 아니라 내 마음과 요청을 구분했는지 확인하시오. 말하기 어렵다면 적어두는 데서 마쳐도 되오.'),
    'people': ('부탁 하나를 고르고, 도울 수 있는 시간과 범위를 먼저 적으시오.', '“오늘은 30분만 도울 수 있어. 나머지는 함께 나눠야 해”처럼 가능한 몫을 말할 문장을 만들어 보시오.', '오늘 밤에는 상대가 좋아했는지보다 내 일정까지 포함해 답했는지 돌아보시오.'),
    'dir': ('두 선택을 종이에 쓰고 각각 얻을 것 하나와 내려놓을 것 하나를 적으시오.', '돈이나 긴 약속을 걸기 전에 확인할 작은 경험을 정하시오. 관련 일을 하는 사람에게 하루 일과를 묻는 것도 시작이오.', '다시 볼 날짜를 적고, 그때 새로 알게 된 사실로 비교하시오. 오늘 최종 결정을 내리지 않아도 첫 확인을 했다면 충분하오.'),
    'health': ('오늘 남은 일을 적고 내일로 넘겨도 되는 것 하나에 표시하시오.', '그 일을 다시 볼 시각을 적은 뒤 오늘 일정을 닫을 때를 정하시오. 머릿속으로 계속 기억할 필요가 없게 종이에 남기는 것이오.', '오늘 밤에는 얼마나 알차게 쉬었는지 채점하지 마시오. 정한 때에 한 가지를 내려놓았는지만 확인하시오.'),
}


def build(concern: str, flow: str | None = None) -> dict | None:
    row = PRACTICES.get(concern)
    if row is None:
        return None
    title, scene, action = row
    from .reading_workbook import GUIDES, EXERCISES, angle
    guide = GUIDES[concern]
    return {"id": f"practice:{VERSION}:{concern}", "version": VERSION,
            "focus": guard.enforce(angle(flow, concern), {"cut":"practice"}),
            "example":guard.enforce(EXERCISES[concern], {"cut":"practice"}),
            **{key:guard.enforce(guide[key], {"cut":"practice"}) for key in ('decision','trap','review')},
            "steps": [guard.enforce(text, {"cut": "practice"}) for text in STEPS[concern]],
            "source_kind": "general_practice", "source": SOURCE,
            **{key: guard.enforce(text, {"cut": "practice"})
               for key, text in (("title", title), ("scene", scene), ("action", action))}}
