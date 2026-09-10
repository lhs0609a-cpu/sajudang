"""Illustrated choices: fixed IDs in, guarded reading out. No uploads or storage.

The face deck is a creative symbolic reading, not a validated classification of
personality. Body selections describe the user's report, never a diagnosis.
Only labels, visual descriptions and asset paths are public; reading text stays here.
"""
from html import escape

from . import guard


class VisualInputError(ValueError):
    pass


def _option(id, label, image, detail="", reading=""):
    return dict(id=id, label=label, image="/choices/" + image,
                detail=detail, reading=reading)


FACE = [
    _option("oval", "타원형", "face-oval.webp", "광대에서 턱으로 완만하게 좁아짐", "완만한 윤곽을 유연함의 상징으로 읽어 보겠소. 여러 입장을 살필 때도 자신의 기준 하나는 남겨 두시오."),
    _option("round", "둥근형", "face-round.webp", "가로·세로 길이가 비슷하고 윤곽이 둥긂", "둥근 윤곽을 어울림의 상징으로 읽어 보겠소. 편안한 관계를 원하는 마음과 혼자 쉴 필요를 함께 살펴보시오."),
    _option("square", "네모형", "face-square.webp", "이마와 턱 너비가 비슷하고 턱 모서리가 각짐", "각진 윤곽을 기준의 상징으로 읽어 보겠소. 지키려는 원칙 하나와 조정할 수 있는 방법 하나를 나눠 보시오."),
    _option("long", "긴 타원형", "face-long.webp", "세로로 길고 턱 끝은 둥긂", "길게 이어지는 윤곽을 깊이의 상징으로 읽어 보겠소. 오래 생각한 일이 있다면 작은 첫 행동도 함께 정해 보시오."),
    _option("heart", "역삼각형", "face-heart.webp", "이마가 넓고 턱 끝으로 많이 좁아짐", "위가 넓고 아래가 모이는 윤곽을 발상의 상징으로 읽어 보겠소. 떠오른 생각 중 지금 손에 잡을 하나를 고르시오."),
    _option("diamond", "마름모형", "face-diamond.webp", "광대가 가장 넓고 이마와 턱이 좁음", "가운데가 도드라지는 윤곽을 초점의 상징으로 읽어 보겠소. 눈에 걸리는 일과 실제로 중요한 일이 같은지 살펴보시오."),
    _option("triangle", "삼각형", "face-triangle.webp", "이마보다 아래턱이 넓음", "아래가 넓은 윤곽을 기반의 상징으로 읽어 보겠소. 익숙해서 지키는 것인지, 여전히 필요해서 지키는 것인지 물어보시오."),
    _option("rectangle", "긴 네모형", "face-rectangle.webp", "세로로 길고 양옆과 턱이 각짐", "길고 각진 윤곽을 지속의 상징으로 읽어 보겠소. 끝까지 이어갈 일과 도중에 조정할 일을 따로 적어 보시오."),
]

# Each SVG changes only the feature named here; all six variants share one viewBox.
FEATURES = {
    "eyes": ("눈", [
        ("open", "세로로 큰 눈", "눈의 세로 폭이 큼", "열림"),
        ("narrow", "가느다란 눈", "눈의 세로 폭이 작음", "집중"),
        ("long", "가로로 긴 눈", "양끝 사이 길이가 김", "조망"),
        ("round", "둥근 눈", "눈의 위아래 곡선이 둥긂", "호기심"),
        ("up", "눈꼬리가 올라간 눈", "바깥 눈꼬리가 안쪽보다 높음", "의지"),
        ("down", "눈꼬리가 내려간 눈", "바깥 눈꼬리가 안쪽보다 낮음", "공감"),
    ]),
    "brows": ("눈썹", [
        ("straight", "일자 눈썹", "높이 변화가 작은 직선", "일관성"),
        ("arched", "활 모양 눈썹", "가운데가 높게 휘어진 곡선", "표현"),
        ("thick", "두꺼운 눈썹", "눈썹 띠의 폭이 넓음", "추진"),
        ("thin", "가는 눈썹", "눈썹 띠의 폭이 좁음", "세심함"),
        ("long", "긴 눈썹", "눈보다 바깥으로 길게 이어짐", "연결"),
        ("short", "짧은 눈썹", "눈보다 짧게 끝남", "선택"),
    ]),
    "nose": ("코", [
        ("high", "높은 콧대", "옆모습에서 콧대가 앞으로 높이 나옴", "방향"),
        ("low", "낮은 콧대", "옆모습에서 콧대가 얼굴 가까이에 있음", "조율"),
        ("wide", "넓은 콧방울", "정면에서 코 아래 너비가 넓음", "수용"),
        ("narrow", "좁은 콧방울", "정면에서 코 아래 너비가 좁음", "정돈"),
        ("round", "둥근 코끝", "정면에서 코끝이 둥글게 보임", "여유"),
        ("long", "긴 코", "미간에서 코끝까지의 길이가 김", "계획"),
    ]),
    "mouth": ("입", [
        ("full", "도톰한 입술", "위아래 입술 두께가 두꺼움", "나눔"),
        ("thin", "얇은 입술", "위아래 입술 두께가 얇음", "절제"),
        ("wide", "가로로 넓은 입", "입 양끝 사이 거리가 넓음", "소통"),
        ("narrow", "가로로 좁은 입", "입 양끝 사이 거리가 좁음", "숙고"),
        ("up", "입꼬리가 올라간 입", "입 양끝이 중앙보다 높음", "격려"),
        ("down", "입꼬리가 내려간 입", "입 양끝이 중앙보다 낮음", "신중함"),
    ]),
    "jaw": ("턱", [
        ("round", "둥근 턱", "아래 윤곽이 둥근 곡선", "유연함"),
        ("square", "각진 턱", "양쪽 아래턱 모서리가 뚜렷함", "기준"),
        ("pointed", "뾰족한 턱", "턱 끝이 좁고 뾰족함", "초점"),
        ("wide", "넓은 턱", "아래턱의 가로 폭이 넓음", "기반"),
        ("narrow", "좁은 턱", "아래턱의 가로 폭이 좁음", "선별"),
        ("long", "긴 턱", "입 아래부터 턱 끝까지 김", "지속"),
    ]),
}

BODY_REGIONS = [
    ("head", "머리"), ("neck", "목"), ("shoulder", "어깨"),
    ("chest", "가슴"), ("abdomen", "배"), ("back", "등"),
    ("waist", "허리"), ("arm", "팔·팔꿈치"), ("hand", "손·손목"),
    ("hip", "골반·엉덩이"), ("leg", "다리·무릎"), ("foot", "발·발목"),
    ("whole", "전반적인 컨디션"),
]
BODY_STATES = [
    _option("pain", "아프거나 불편합니다", "body-front.svg", reading="불편한 위치와 시작한 때를 따로 적어 두시오. 원인은 여기서 판단할 수 없소."),
    _option("tired", "쉽게 지칩니다", "tired.webp", reading="하루 중 유난히 지치는 때와 그전에 한 일을 적어 보시오. 피로를 의지의 문제로 단정하지 마시오."),
    _option("sleep", "잠이 신경 쓰입니다", "sleep.webp", reading="잠자리에 든 시각과 깬 시각, 낮 동안 느낀 상태를 함께 돌아보시오."),
    _option("rest", "쉬어도 여유가 없습니다", "heal.webp", reading="쉬는 동안에도 마음에 남은 일을 적어 보시오. 오늘 마칠 일과 다음으로 넘길 일을 나눠 보는 자리요."),
]
DURATIONS = [("today", "오늘부터"), ("days", "며칠 전부터"),
             ("long", "오래되거나 반복됨"), ("unknown", "잘 모르겠습니다")]
IMPACTS = [("mild", "일상은 할 수 있습니다"), ("disrupt", "일상에 지장이 있습니다"),
           ("severe", "심하거나 갑자기 시작됐습니다")]


def _scene(id, label, image, reading):
    return _option(id, label, image + ".webp", reading=reading)


# Choices are about reported circumstances, never an inference from an illustration.
SCENES = {
    "pungun": ("되풀이되는 장면이 있소?", [
        _scene("overwork", "일이 늘 제게 몰립니다", "tired", "반복되는 일의 이름과 누가 맡기는지를 나눠 적어 보시오. 해야 할 일과 습관처럼 떠맡은 일이 갈릴 수 있소."),
        _scene("silence", "같은 대화에서 막힙니다", "silence", "대화가 끊기는 순간에 실제로 오간 말부터 살펴보시오. 상대의 속마음을 대신 정하지는 마시오."),
        _scene("choice", "선택 앞에서 망설입니다", "road", "후보를 늘리기 전에 고를 기준 두 개를 정해 보시오. 무엇을 포기하기 어려운지도 같이 적으시오."),
    ]),
    "baegun": ("요즘 무엇을 채우고 싶소?", [
        _scene("rest", "쉴 여유가 필요합니다", "heal", "하루 중 아무 일을 맡지 않는 짧은 구간을 찾아보시오. 빈 시간을 또 할 일로 채우지 않아도 되오."),
        _scene("people", "사람과 나누고 싶습니다", "meet", "새 인맥의 수보다 편히 말할 수 있는 한 사람을 떠올려 보시오."),
        _scene("movement", "일상에 변화를 주고 싶습니다", "walk", "생활에서 바꿀 수 있는 작은 동선 하나를 골라 보시오. 바꾼 뒤 어떤 기분이 드는지 살펴보시오."),
    ]),
    "cheongam": ("어떤 일을 할 때 손이 가오?", [
        _scene("make", "직접 만드는 일이 좋습니다", "craft", "만든 결과물 중 다시 해보고 싶은 것을 골라 보시오. 즐거운 과정과 잘하는 과정을 따로 살펴보는 것이오."),
        _scene("analyze", "비교하고 분석하는 일이 좋습니다", "analyze", "끝까지 파고들었던 질문을 떠올려 보시오. 분석의 결과를 누가 어떻게 쓸지도 함께 보시오."),
        _scene("lead", "설명하고 이끄는 일이 좋습니다", "lead", "설득했던 경험에서 말의 내용과 듣는 사람의 필요가 어떻게 만났는지 돌아보시오."),
        _scene("care", "사람을 돕는 일이 좋습니다", "care", "돕고 난 뒤에도 힘이 남았던 경험을 찾아보시오. 자신의 몫을 지킬 경계도 필요하오."),
    ]),
    "sigye": ("어떤 변화의 때를 보고 있소?", [
        _scene("job", "이직을 생각합니다", "job", "옮기고 싶은 이유와 준비된 조건을 나눠 적으시오. 사주의 시기 해석과 실제 채용 일정은 따로 확인해야 하오."),
        _scene("start", "새 일을 시작하려 합니다", "start", "원하는 시작일에서 거꾸로 준비할 일을 적어 보시오. 지금 할 수 있는 첫 단계를 정하는 것이오."),
        _scene("hold", "잠시 머물며 준비하려 합니다", "heal", "기다림이 준비가 되려면 확인할 조건이 있어야 하오. 무엇이 갖춰지면 움직일지 적어 보시오."),
    ]),
    "eunbyeol": ("평소의 나와 다른 장면이 있소?", [
        _scene("social", "밖에서는 더 적극적입니다", "meet", "밖에서 맡은 역할 때문에 달라진 반응인지 살펴보시오. 성향과 상황이 항상 같은 모습을 만들지는 않소."),
        _scene("quiet", "혼자일 때 더 편합니다", "heal", "혼자 있으면 돌아오는 힘이 무엇인지 적어 보시오. 피하고 싶은 일과 필요한 휴식도 나눠 보시오."),
        _scene("plan", "생각보다 계획에 매달립니다", "analyze", "계획이 도움이 되는 순간과 결정을 미루게 하는 순간을 각각 떠올려 보시오."),
    ]),
    "jeokhyeol": ("끌리는 사람이 생기면 어찌하오?", [
        _scene("approach", "제가 먼저 다가갑니다", "meet", "먼저 다가간 뒤 상대의 답을 들을 자리도 남겨 보시오. 끌림과 동의는 따로 확인하는 것이오."),
        _scene("watch", "거리를 두고 살핍니다", "distance", "관찰로 알 수 있는 사실과 추측한 마음을 나눠 보시오. 필요한 말은 직접 물어야 하오."),
        _scene("talk", "대화하며 알아갑니다", "talk", "서로 편히 말할 수 있었던 주제부터 돌아보시오. 맞추기 위해 감춘 자기 생각은 없는지도 보시오."),
    ]),
    "seoyeok": ("어느 쪽으로 자리를 넓히려 하오?", [
        _scene("move", "멀리 이주를 생각합니다", "move", "이주의 이유와 생활 조건을 각각 적어 보시오. 출생지로 계산한 배치가 새 지역의 현실 조건을 대신하지는 않소."),
        _scene("work", "다른 곳에서 일하고 싶습니다", "job", "지역을 바꾸면 얻는 것과 새로 준비할 자격을 나눠 살펴보시오."),
        _scene("explore", "먼저 가서 경험하고 싶습니다", "walk", "머릿속 기대를 확인할 짧은 경험부터 생각해 보시오. 다녀온 뒤의 느낌을 계획과 비교하는 것이오."),
    ]),
    "wolha": ("어떤 만남을 바라고 있소?", [
        _scene("new", "새로운 사람을 만나고 싶습니다", "meet", "어떤 자리에서 편히 자기 이야기를 할 수 있는지 떠올려 보시오. 만남의 수와 관계의 깊이는 다른 것이오."),
        _scene("closer", "지금 인연과 가까워지고 싶습니다", "talk", "상대에게 바라지만 아직 말하지 않은 것을 하나 골라, 부탁할 수 있는 문장으로 바꿔 보시오."),
        _scene("daily", "편안한 일상을 나누고 싶습니다", "home", "함께 보내고 싶은 평범한 하루를 구체적으로 떠올려 보시오. 그 안에 자신의 시간이 남는지도 보시오."),
    ]),
    "hongmae": ("함께 사는 일에서 무엇이 걸리오?", [
        _scene("life", "생활 방식이 다릅니다", "home", "잠드는 때, 집안일, 혼자 보내는 시간처럼 실제 생활의 약속을 한 가지씩 맞춰 보시오."),
        _scene("money", "돈 이야기를 맞추고 싶습니다", "debt", "함께 쓸 돈과 각자 관리할 돈의 범위를 말로 확인해 보시오. 추측으로 약속을 대신하지 마시오."),
        _scene("distance", "거리와 일 때문에 고민입니다", "distance", "만나는 일정과 이동의 부담이 어느 한쪽에 몰리는지 함께 살펴보시오."),
    ]),
    "yeondam": ("지난 관계에서 무엇이 남았소?", [
        _scene("silence", "연락이 끊긴 상태입니다", "silence", "연락이 없다는 사실과 그 까닭에 대한 추측을 구분하시오. 상대의 답을 강요하지 않으며 자신의 하루를 지킬 방법부터 보시오."),
        _scene("distance", "멀어졌지만 마음이 남았습니다", "distance", "그리운 사람과 그때의 생활 중 무엇이 더 그리운지 적어 보시오. 다시 만날지 여부는 여기서 정하지 않소."),
        _scene("part", "이제 정리하고 싶습니다", "part", "정리하고 싶은 이유를 남에게 설명할 말보다 자신이 읽을 말로 적어 보시오. 추억을 지우는 것과 경계를 세우는 것은 다르오."),
    ]),
    "hwagyeong": ("다툼은 어느 장면에서 커지오?", [
        _scene("talk", "대화하면 말이 엇갈립니다", "talk", "사실, 느낀 감정, 원하는 부탁을 한 문장씩 나눠 보시오. 상대의 의도까지 대신 판정하지는 마시오."),
        _scene("silence", "서로 말을 안 하게 됩니다", "silence", "대화를 멈출 때 다시 말할 수 있는 때를 합의했는지 돌아보시오. 침묵만으로 뜻이 전달되지는 않소."),
        _scene("boundary", "거리를 정하고 싶습니다", "part", "허용할 수 있는 행동과 어려운 행동을 구체적으로 나눠 보시오. 자신의 경계를 말하는 데서 시작하오."),
    ]),
    "haengsu": ("돈은 지금 어느 자리에 걸렸소?", [
        _scene("income", "벌이를 바꾸고 싶습니다", "job", "지금의 고정 수입과 바꾸려는 수입의 조건을 따로 적으시오. 기대하는 금액과 확인된 금액을 구분하시오."),
        _scene("biz", "제 장사를 키우고 싶습니다", "biz", "팔리는 것과 손에 남는 것을 함께 보시오. 손님 수만으로 일이 잘되는지 판단하지 마시오."),
        _scene("debt", "지출과 빚을 정리하려 합니다", "debt", "내야 할 날짜와 금액을 한곳에 모아 보시오. 사주 해석으로 매수나 매도 시점을 정하는 자리는 아니오."),
    ]),
    "hunjang": ("공부는 어디에서 막히오?", [
        _scene("start", "무엇부터 할지 모르겠습니다", "exam", "범위를 전부 잡기 전에 오늘 확인할 작은 단원을 고르시오. 공부한 시간과 이해한 내용을 따로 보시오."),
        _scene("tired", "앉아도 집중이 어렵습니다", "tired", "집중이 끊기는 때와 주변 조건을 적어 보시오. 자신을 꾸짖기 전에 방해되는 조건 하나부터 조정해 보시오."),
        _scene("plan", "계획을 꾸준히 지키고 싶습니다", "analyze", "지키지 못한 계획에서 분량과 시간을 따로 살펴보시오. 다음 계획은 실제로 해낸 양에서 시작하시오."),
    ]),
    "ilgwan": ("무슨 일을 위한 날이오?", [
        _scene("move", "이사 날짜를 생각합니다", "move", "계약과 이동이 가능한 날짜 범위를 먼저 정하시오. 날짜 해석은 실제 일정의 제약과 함께 보아야 하오."),
        _scene("open", "개업 날짜를 생각합니다", "biz", "준비가 끝나는 날과 손님을 맞을 수 있는 날을 확인하시오. 날짜만으로 장사의 결과를 정하지 않소."),
        _scene("meet", "모임 날짜를 생각합니다", "meet", "참석하는 사람이 실제로 가능한 날을 먼저 모아 보시오. 좋은 모임의 조건을 날짜 하나에 맡기지 마시오."),
    ]),
    "nopa": ("갈림길에서 어느 쪽을 생각하오?", [
        _scene("stay", "지금 자리에 남고 싶습니다", "home", "남는다면 달라져야 할 조건 하나를 정해 보시오. 익숙함과 만족이 같은지는 따로 살펴보시오."),
        _scene("leave", "다른 길로 가고 싶습니다", "road", "떠나고 싶은 이유와 가고 싶은 곳의 이유를 나눠 보시오. 다음 자리의 현실 조건도 같이 보시오."),
        _scene("pause", "잠시 쉬며 생각하고 싶습니다", "heal", "쉰 뒤 다시 살펴볼 질문 하나를 남겨 두시오. 모든 결정을 오늘 마칠 필요는 없소."),
    ]),
    "dongja": ("오늘은 어떤 한 잔이면 좋겠소?", [
        _scene("rest", "조용히 쉬고 싶습니다", "heal", "오늘 더하지 않아도 될 일 하나를 골라 보시오. 잠깐 쉬어 가는 자리로 두어도 되오."),
        _scene("talk", "누군가와 이야기하고 싶습니다", "care", "지금 마음을 한 문장으로 적어 보시오. 편히 이야기할 사람에게 그 문장부터 건네 보시오."),
        _scene("start", "작게 시작하고 싶습니다", "start", "끝까지 해낼 큰일보다 지금 손을 댈 수 있는 작은 일을 골라 보시오."),
    ]),
}


def _public(o):
    return {k: v for k, v in o.items() if k != "reading"}


def choices(lens_id=None):
    scene = SCENES.get(lens_id)
    return {
        "face": [_public(x) for x in FACE],
        "face_features": [dict(id=k, label=label, options=[
            dict(id=id, label=t, detail=detail, image=f"/choices/{k}-{id}.svg")
            for id, t, detail, _ in options]) for k, (label, options) in FEATURES.items()],
        "body_regions": [dict(id=k, label=v) for k, v in BODY_REGIONS],
        "body_states": [_public(x) for x in BODY_STATES],
        "body_duration": [dict(id=k, label=v) for k, v in DURATIONS],
        "body_impact": [dict(id=k, label=v) for k, v in IMPACTS],
        "scene": dict(title=scene[0], options=[_public(x) for x in scene[1]]) if scene else None,
    }


def _mapping(value):
    if not isinstance(value, dict):
        raise VisualInputError("고른 항목의 형식을 확인해 주시오.")
    return value


def _one(options, id):
    if not isinstance(id, str):
        raise VisualInputError("목록에서 하나를 골라 주시오.")
    found = next((x for x in options if x["id"] == id), None)
    if not found:
        raise VisualInputError("목록에 있는 항목으로 다시 골라 주시오.")
    return found


def _cut(id, title, source, html, sid):
    return dict(id=id, title=title, source=source,
                html=guard.enforce(html, {"cut": id}), min_level=0, statement_id=sid)


def face_cut(f, payload):
    p = _mapping(payload)
    shape = _one(FACE, p.get("shape")) if p.get("shape") != "unknown" else None
    features = _mapping(p.get("features", {}))
    if set(features) - set(FEATURES):
        raise VisualInputError("얼굴 부위를 다시 확인해 주시오.")
    rows, ids, labels = [], [], []
    if shape:
        labels.append(shape["label"])
        rows.append(f'<p><b>{shape["label"]}</b> · {shape["reading"]}</p>')
    for key, (label, options) in FEATURES.items():
        selected = features.get(key)
        if selected in (None, "unknown"):
            continue
        opt = next((x for x in options if x[0] == selected), None)
        if opt is None:
            raise VisualInputError("얼굴 특징을 목록에서 다시 골라 주시오.")
        id, text, _, symbol = opt
        labels.append(text)
        ids.append(f"{key}={id}")
        rows.append(f'<p><b>{label} · {text}</b>은 이 도감에서 <b>{symbol}</b>의 상징으로 읽소. '
                    f'요즘 {symbol}이 도움이 된 순간과 부담이 된 순간을 하나씩 떠올려 보시오.</p>')
    if not labels:
        raise VisualInputError("얼굴형이나 부위 특징 중 하나는 골라 주시오.")
    html = ('<p class="sm">고른 그림을 바탕으로 만든 성신당의 창작 관상 풀이요. '
            '얼굴로 실제 성격·건강·미래를 판정하지 않소.</p>' + "".join(rows) +
            '<p>여러 상징 중 지금의 경험과 닿는 것 하나를 골라 보시오. '
            '맞지 않는 설명은 내려놓아도 되오. 아래 사주 해석은 생년월일로 계산한 별도의 자리요.</p>')
    return _cut("face", "그림으로 고른 관상", "직접 고른 특징 · " + " · ".join(labels),
                html, "face:" + (shape["id"] if shape else "unknown") + ":" + ",".join(ids))


def body_cut(f, payload):
    p = _mapping(payload)
    regions = p.get("regions")
    allowed = dict(BODY_REGIONS)
    if (not isinstance(regions, list) or not 1 <= len(regions) <= 3 or
            any(not isinstance(x, str) or x not in allowed for x in regions) or
            len(set(regions)) != len(regions) or ("whole" in regions and len(regions) > 1)):
        raise VisualInputError("부위는 세 곳까지, 전반적인 컨디션은 단독으로 골라 주시오.")
    state = _one(BODY_STATES, p.get("state"))
    duration = dict(DURATIONS).get(p.get("duration")) if isinstance(p.get("duration"), str) else None
    impact = dict(IMPACTS).get(p.get("impact")) if isinstance(p.get("impact"), str) else None
    if not duration or not impact:
        raise VisualInputError("시작한 때와 일상에 미치는 영향을 골라 주시오.")
    labels = " · ".join(allowed[r] for r in regions)
    html = (f'<p>고른 위치는 <b>{labels}</b>, 상태는 <b>{state["label"]}</b>라 하셨소. '
            f'시작한 때는 {duration}, 일상은 “{impact}”로 적으셨소.</p>'
            '<p class="sm">직접 알려주신 내용을 정리한 것이오. 이 그림과 사주로 불편의 원인을 알 수는 없소.</p>')
    if p["impact"] == "severe":
        html += '<p><b>심하거나 갑자기 시작한 불편은 의료진의 확인을 먼저 받으시오.</b> 위급하면 119에 도움을 요청하시오.</p>'
    else:
        html += f'<p>{state["reading"]}</p><p>불편이 계속되거나 일상에 지장이 있다면 의료진과 상의하시오.</p>'
    # No element-to-organ relationship, medication, exercise prescription or score.
    return _cut("body", "몸의 상태를 함께 정리하오", "직접 알려주신 상태 · " + labels,
                html, "body:" + ",".join(sorted(regions)) + f':{p["state"]}:{p["duration"]}:{p["impact"]}')


def scene_cut(lens_id, payload):
    if not payload:
        return None
    p = _mapping(payload)
    scene = SCENES.get(lens_id)
    if not scene or p.get("lens_id") != lens_id:
        raise VisualInputError("이 캐릭터의 장면으로 다시 골라 주시오.")
    picked = _one(scene[1], p.get("pick"))
    return _cut("scene", "고른 장면에서 이어지는 말", "직접 고른 상황 · " + picked["label"],
                f'<p><b>{escape(picked["label"])}</b>라는 장면을 고르셨소.</p>'
                f'<p>{picked["reading"]}</p><p class="sm">알려주신 상황에 관한 질문이오. 그림으로 속마음을 알아낸 것은 아니오.</p>',
                f'scene:{lens_id}:{picked["id"]}')
