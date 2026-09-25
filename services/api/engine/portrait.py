# -*- coding: utf-8 -*-
"""
어떤 사람인가 — **사람을 그리는 자리.**

왜 만들었나
    손님이 짚었습니다 — 「지금 사주가 추상적인데, 되게 구체적이고 너는
    이런 사람이야 이런 식으로 디테일하게 설명해 주는 걸로 전부 바꿀 수
    없어? 모든 캐릭터가?」

    재 보니 맞는 말이었습니다. 한 장 스물세 컷을 펴 놓고 세었더니
    **거의 모든 문장의 주어가 명리 용어**였습니다 —

        「재성이 하나요」 「상관이 가장 세오」 「일지가 戌이오」

    그대가 주어인 문장은 드물고, 있어도 조건문이었습니다(「…면 …하오」).
    그리고 「그대는 이런 사람이오」 라고 **끝까지 말해 주는 컷이 한 개도
    없었습니다.** 가장 가까운 것이 마감 컷의 한 문장이었는데, 그건 스물세
    컷을 다 읽은 **맨 끝**에 한 줄로 나왔습니다.

    ★ 말투는 이미 있었습니다. `engine/real.py` 가 그것이오 —
        「회의에서 옳은 말을 하고, 집에 와서 그 말을 후회하오」
      이 집은 구체적으로 쓸 줄 알면서 그걸 **곁말로만** 쓰고 있었습니다.
      표를 늘리기 전에 어느 컷에 걸렸는지부터 세라던 그 자리요.

무엇을 하나
    열 가지 면(面)을 여덟 글자에서 뽑아 **단정문**으로 폅니다.
    조건문을 안 씁니다. 주어는 그대요.

        처음 보는 사람 눈에 · 말할 때 · 일이 들어오면 · 돈을 쓸 때 ·
        가까운 사람 앞에서 · 욱할 때 · 지칠 때 · 남들이 잘못 아는 것 ·
        혼자 있을 때 · 요새

    ★ 면마다 **눈에 보이는 물건**을 댑니다 — 카드값 · 단톡 · 회의 ·
      견적 · 잠. 「자리」 「마음」 같은 이 집의 뜬 낱말을 머리말로 쓰면
      그 표 전체가 흐릿해지오.

스무 명이 어떻게 다른가
    ★ 여덟 글자는 같소. **사람은 한 사람**이오 — 캐릭터가 바뀐다고
      그대가 다른 사람이 되지 않소. 그러면 그건 점이 아니라 소설이오.
      갈리는 것은 **어느 면을 몇 번째로 보는가**요 (`VIEW`). 여는 줄은
      그 사람의 축에서 나오고(`editorial.ROLES`), 말투는 `voice` 가
      갈아 끼우오.

안 하는 것
    사건 단정 · 시점 확정 · 병 이름 · 적중률. `guard` 가 잡소.
    단정문이되 **틀릴 수 있는 단정**이오 — 끝에 아닌 대목을 빼라고
    적습니다. 다 맞는 글은 아무것도 안 맞는 글이오.
"""
from hashlib import sha256
from html import escape
from typing import Optional

from . import guard, terms, voice
from . import why as _why

VERSION = 'portrait-v1'

TITLE = '어떤 사람인가'

# 면의 머리말 — 말이 아니라 **표지판**이오. 어느 말투에도 안 걸리는 꼴로.
HEAD = {
    'first': '처음 보는 사람 눈에',
    'talk': '말할 때',
    'work': '일이 들어오면',
    'money': '돈을 쓸 때',
    'close': '가까운 사람 앞에서',
    'anger': '욱할 때',
    'tired': '지칠 때',
    'misread': '남들이 잘못 아는 것',
    'alone': '혼자 있을 때',
    'age': '요새',
}

# 면마다 **무엇으로 가르는가**. 근거 줄에 이 이름으로 답니다.
AXIS_OF = {
    'first': 'day_gan', 'talk': 'top_ten_god', 'work': 'flow',
    'money': 'gwan_jae', 'close': 'ilji_state', 'anger': 'sinsal_mark',
    'tired': 'weak_el', 'misread': 'strong_el', 'alone': 'top_ten_god',
    'age': 'daeun_phase',
}


# ══════════════════════════════════════════════════════════
# 처음 보는 사람 눈에 — 일간 열 자
# ══════════════════════════════════════════════════════════
#
# ★ 일간은 여덟 글자 가운데 **그대 자신**을 뜻하는 글자요. 사람을
#   그리는 자리라면 여기서 시작하는 것이 맞소.
FIRST = {
    '甲': '곧고 좀 미련해 보이오. 모임에서 먼저 말을 꺼내지는 않는데 한번 맡으면 끝을 보아서, 사람들이 궂은 일을 그대에게 먼저 가져오오.',
    '乙': '부드럽고 무르게 보이오. 정작 안 꺾이는 쪽은 그대라, 같이 야근을 해 본 사람만 그대가 얼마나 안 물러서는지 아오.',
    '丙': '밝고 시원해 보이오. 문을 열고 들어서는 순간 그대가 온 걸 사람들이 아오. 그래서 가라앉은 날에도 「무슨 일 있어?」를 먼저 듣소.',
    '丁': '조용해 보이오. 열 명이 앉은 회식 자리에서는 눈에 잘 안 띄는데, 단둘이 마주 앉아 본 사람은 그대를 아주 다르게 기억하오.',
    '戊': '듬직하고 느려 보이오. 급한 자리에서 표정이 안 바뀌어서, 사람들이 곤란한 얘기를 그대에게 들고 오오.',
    '己': '무던해 보이오. 남 얘기를 잘 받아 줘서 모임에서 다들 편해하는데, 정작 그대 얘기를 꺼낼 차례는 끝까지 안 오오.',
    '庚': '딱딱하고 차가워 보이오. 말을 돌려 하는 법이 없어서 그렇소. 친해지면 단톡방에서 「생각보다 사람 좋네」를 듣는데, 그 말을 듣기까지가 남들보다 오래 걸리오.',
    '辛': '깔끔하고 까다로워 보이오. 비뚤어진 액자나 오타 하나를 그냥 못 넘겨서, 아주 사소한 데서 먼저 표가 나오.',
    '壬': '속을 모르겠다 하오. 회의에서 어디까지 생각하고 왔는지가 안 보여서, 사람들이 그대를 한 수 위로 보거나 어렵게 여기오.',
    '癸': '조심스럽고 섬세해 보이오. 방에 들어서면서 공기부터 읽어서, 입을 떼기 전에 그 자리 분위기를 이미 파악하고 있소.',
}

# ══════════════════════════════════════════════════════════
# 말할 때 — 십신 열 가지
# ══════════════════════════════════════════════════════════
TALK = {
    '비견': '「나도 그랬어」가 먼저 나오오. 편들어 주려고 꺼낸 말인데, 듣는 쪽은 제 얘기를 가로챘다고 느낄 때가 있소.',
    '겁재': '지고 싶지 않은 마음이 먼저 서오. 술자리 농담으로 시작한 얘기가 어느새 누가 맞느냐로 가 있소.',
    '식신': '말이 술술 나오고 듣는 사람이 편하오. 다만 좋은 얘기만 하다가 정작 부탁할 말은 끝까지 못 꺼내오.',
    '상관': '아무도 안 짚는 것을 그대가 짚소. 맞는 말인데, 회의실을 나오면서 「그 말은 안 했어야 했나」를 한 번 더 생각하오.',
    '편재': '말이 크고 시원하오. 자리에서 「그건 내가 해 줄게」가 쉽게 나가고, 집에 와서 달력을 세어 보오.',
    '정재': '숫자와 날짜를 먼저 확인하오. 정확한 대신 결론이 늦어서, 성격 급한 사람은 그대와 얘기할 때 답답해하오.',
    '편관': '할 말을 줄여서 하오. 그래서 회의에서 던진 짧은 한마디가 세게 박히고, 그럴 뜻이 아니었는데 상대가 굳는 일이 생기오.',
    '정관': '앞뒤를 맞춰서 말하오. 틀린 말을 안 하려다 결론이 늦고, 답장을 기다리던 쪽은 그대가 발을 뺀다고 여기오.',
    '편인': '말수는 적은데 남이 안 보는 각도를 내놓소. 그 각도가 좋은데 설명을 반만 해서, 회의에 앉은 사람들이 못 따라오오.',
    '정인': '아는 것을 잘 풀어 주오. 그래서 설명이 길어지고, 상대가 원한 건 결론 한 줄인데 그대는 아직 자료의 배경을 말하고 있소.',
}

# ══════════════════════════════════════════════════════════
# 일이 들어오면 — 힘이 흐르는 쪽
# ══════════════════════════════════════════════════════════
WORK = {
    '비겁': '같이 할 사람부터 찾소. 그런데 마지막에 손보는 것은 늘 그대고, 그 몫은 어느 문서에도 안 적히오.',
    '식상': '먼저 만들어 보오. 만드는 동안이 제일 재미있고, 값을 적어 넣을 견적서 앞에서 힘이 빠지오.',
    '재성': '얼마가 되는지부터 셈하오. 셈이 빨라 기회를 잘 잡는 대신, 안 될 일을 붙들고 달력을 넘긴 날도 그만큼 많았소.',
    '관성': '누가 책임지는지부터 보오. 맡으면 끝까지 하는데, 이미 넘겨도 될 일의 단톡방을 아직 못 나가고 있소.',
    '인성': '먼저 알아보오. 자료가 쌓이는 동안 시작이 미뤄지고, 다 알고 났을 때는 이미 남이 해 놓았소.',
}

# ══════════════════════════════════════════════════════════
# 돈을 쓸 때 — 쥐는 글자의 갈래
# ══════════════════════════════════════════════════════════
MONEY = {
    '정재': '쓰는 쪽보다 안 쓰는 쪽이오. 장바구니에 담아 두고 며칠을 더 들여다보다가, 정작 써야 할 자리에서도 손이 안 나가오.',
    '편재': '크게 들어오고 크게 나가오. 밥값을 먼저 내고, 그달 말에 카드값을 보며 놀라오.',
    '둘다': '두 얼굴이 있소. 평소에는 배달비 삼천 원을 아끼다가, 한 번에 큰 것을 지르고 그걸로 균형을 맞췄다 여기오.',
    '없음': '돈 얘기를 앞에서 못 꺼내오. 값을 부를 때 먼저 깎아 말하고, 받을 것을 못 받고 넘어간 적이 있소.',
}

# ══════════════════════════════════════════════════════════
# 가까운 사람 앞에서 — 발밑 글자가 놓인 모양
# ══════════════════════════════════════════════════════════
CLOSE = {
    '충': '참지 않소. 밖에서는 웃고 넘기는 말을 집에서는 그냥 못 넘겨서, 크게 붙었다 크게 푸오.',
    '형': '말이 날카로워지오. 밖에서는 예의가 서는데, 집 현관을 들어서면 같은 말이 다르게 나가오.',
    '합': '가까워지는 것은 빠르고 떼는 것은 더디오. 연락처를 지운 뒤에도 그 사람 소식이 들리면 하루가 흔들리오.',
    '조용': '다툼이 드무오. 대신 먼저 연락하는 쪽도 그대가 아니라서, 그 사이가 몇 해째 같은 자리에 있소.',
}

# ══════════════════════════════════════════════════════════
# 욱할 때
# ══════════════════════════════════════════════════════════
ANGER = {
    '양인': '눈에 보이오. 참을 줄 몰라서가 아니라 한번 세우면 끝을 봐야 하기 때문이오. 그러고 나면 그 단톡방이 도로 조용해지기까지 오래 걸리오.',
    '상관': '말로 이기오. 그 자리에서는 이기고, 돌아오는 길 지하철에서 이겨서 남은 것이 무엇인지를 세어 보오.',
    '편관': '말을 끊고 자리를 뜨오. 터뜨리는 대신 닫아서, 답장이 끊긴 상대는 무슨 일인지도 모른 채 남겨지오.',
    '삼킴': '속으로 삼키오. 그날은 넘어가는데 잠이 안 오고, 며칠 뒤 엉뚱한 일에서 터지오.',
    '보통': '티를 덜 내오. 대신 그 사람에게 가던 연락이 하나둘 줄어드는 것으로 나타나오.',
}

# ══════════════════════════════════════════════════════════
# 지칠 때 — 모자란 기운
# ══════════════════════════════════════════════════════════
TIRED = {
    '목': '새로 시작할 힘부터 사라지오. 하던 일은 굴러가는데 새 일은 첫 줄을 못 쓰오.',
    '화': '사람 만나는 자리가 먼저 무겁소. 약속을 미루고, 미룬 것이 쌓여서 더 못 나가오.',
    '토': '정리가 안 되오. 책상도 단톡도 일정도 흩어진 채로 두고, 그걸 보며 또 지치오.',
    '금': '끊지를 못하오. 그만둘 일을 못 그만두고 달력을 세 번 넘기다가 한 번에 무너지오.',
    '수': '배운 것이 안 쌓이오. 같은 실수를 두 번 하고, 두 번째인 걸 알아서 더 화가 나오.',
}

# ══════════════════════════════════════════════════════════
# 남들이 잘못 아는 것 — 넘치는 기운
# ══════════════════════════════════════════════════════════
MISREAD = {
    '목': '벌이기만 하는 사람으로 아오. 실은 못 끝낸 일 목록을 들여다보며 제일 괴로워하는 쪽이 그대 자신이오.',
    '화': '늘 밝은 사람으로 아오. 그래서 힘든 날에도 단톡방에 먼저 웃는 낯을 올리게 되오.',
    '토': '사람 좋은 쪽으로 아오. 그래서 부탁이 그대에게 모이고, 한 번 거절하면 그날 저녁 연락이 뜸해지오.',
    '금': '차갑다 하오. 정이 없는 것이 아니라 회의에서 안 되는 걸 안 된다고 말한 것뿐이오.',
    '수': '느리다 하오. 답장이 늦고 첫 삽이 늦을 뿐이고, 한번 붙들면 남보다 멀리 가오.',
}

# ══════════════════════════════════════════════════════════
# 혼자 있을 때 — 받쳐 주는 글자
# ══════════════════════════════════════════════════════════
ALONE = {
    '편인': '그때가 진짜 쉬는 때요. 모임에서 돌아온 날은 그만큼을 혼자 되감아야 하루가 끝나오.',
    '정인': '뭔가를 배우고 있소. 쉬는 날에도 강의를 틀어 두는 쪽이라, 정작 아무것도 안 하는 시간이 제일 불편하오.',
    '없음': '오래 못 견디오. 조용해지면 일을 만들거나 연락할 사람을 찾소.',
}

# ══════════════════════════════════════════════════════════
# 요새 — 지금 지나는 십 년의 국면
# ══════════════════════════════════════════════════════════
AGE = {
    '들기전': '하는 일마다 반 박자씩 안 맞소. 그대가 못해서가 아니라 아직 그대 철이 안 온 것이라, 달력을 앞당긴다고 되는 일이 아니오.',
    '막들어옴': '전에 통하던 것이 안 통하오. 방법이 낡은 것이 아니라 판이 바뀐 것이오.',
    '한가운데': '가장 불편한 그 일이 지금 그대가 사는 십 년의 얼굴이오. 피하면 같은 모양으로 다시 오오.',
    '바뀔때': '마음이 붕 떠 있소. 이 십 년이 저물고 있기 때문이오. 다음에 하겠다 하면 또 십 년이오.',
}

TABLES = {
    'first': FIRST, 'talk': TALK, 'work': WORK, 'money': MONEY,
    'close': CLOSE, 'anger': ANGER, 'tired': TIRED, 'misread': MISREAD,
    'alone': ALONE, 'age': AGE,
}


# ══════════════════════════════════════════════════════════
# 스무 명 — **어느 면을 몇 번째로 보는가**
# ══════════════════════════════════════════════════════════
#
# ★ 사람은 한 사람이오. 캐릭터가 바뀐다고 그대가 다른 사람이 되면
#   그건 점이 아니라 소설이오. 갈리는 것은 **차례**요.
# ★ 맨 앞은 그 사람의 축에서 옵니다 (`editorial.ROLES`). 버티는 힘을
#   보는 이는 일부터 보고, 가까운 사이를 보는 이는 곁부터 보오.
# ★ 스무 줄이 **서로 달라야** 하오. 같은 줄이 둘이면 그 둘은 같은
#   사람이오 — `tests/test_portrait.py` 가 셉니다.
VIEW = {
    'pungun':    ['work', 'tired', 'anger', 'first', 'age'],
    'baegun':    ['tired', 'anger', 'misread', 'talk', 'work'],
    'cheongam':  ['alone', 'work', 'talk', 'misread', 'close'],
    'sigye':     ['age', 'work', 'first', 'close', 'money'],
    'eunbyeol':  ['misread', 'anger', 'talk', 'close', 'alone'],
    'jeokhyeol': ['work', 'close', 'money', 'tired', 'first'],
    'monghwa':   ['first', 'alone', 'age', 'misread', 'work'],
    'seoyeok':   ['misread', 'talk', 'alone', 'money', 'work'],
    'paeseon':   ['tired', 'work', 'money', 'anger', 'alone'],
    'myeonsang': ['close', 'anger', 'first', 'talk', 'misread'],
    'wolha':     ['close', 'talk', 'misread', 'alone', 'anger'],
    'hongmae':   ['money', 'close', 'work', 'talk', 'tired'],
    'yeondam':   ['close', 'alone', 'anger', 'talk', 'first'],
    'hwagyeong': ['talk', 'anger', 'close', 'work', 'misread'],
    'haengsu':   ['money', 'work', 'talk', 'tired', 'first'],
    'hunjang':   ['alone', 'work', 'talk', 'first', 'misread'],
    'yakcho':    ['tired', 'alone', 'close', 'work', 'anger'],
    'ilgwan':    ['first', 'work', 'misread', 'money', 'close'],
    'nopa':      ['age', 'work', 'close', 'misread', 'tired'],
    'dongja':    ['first', 'tired', 'close', 'alone', 'money'],
}

# 캐릭터를 안 고르고 들어온 자리(훅 첫머리)에서 쓰는 차례.
DEFAULT_ORDER = ['first', 'talk', 'work', 'close', 'tired', 'age']

CLOSING = ('여기까지가 여덟 글자로 읽은 그대의 모습이오. 아닌 대목이 있거든 '
           '그 줄을 빼고 읽으시오 — <b>다 맞는 글은 아무것도 안 맞는 글</b>이오.')


# ══════════════════════════════════════════════════════════
# 여덟 글자에서 면의 열쇠를 뽑는다
# ══════════════════════════════════════════════════════════
def _money_key(f) -> str:
    jeong, pyeon = int(f.ten_gods.get('정재', 0)), int(f.ten_gods.get('편재', 0))
    if jeong and pyeon:
        return '둘다'
    if pyeon:
        return '편재'
    if jeong:
        return '정재'
    return '없음'


def _close_key(f) -> str:
    # ★ 차례가 뜻이오 — 부딪힘이 가장 세고, 그다음이 다툼의 짝이오.
    if f.ilji_chung:
        return '충'
    from . import pattern as _pattern
    if any(p['key'] == 'ilji_hyeong' for p in _pattern.read(f, None, limit=99)):
        return '형'
    if f.ilji_hap:
        return '합'
    return '조용'


def _anger_key(f) -> str:
    from .pattern import all_patterns
    for p in all_patterns():
        if p['key'] == 'yangin':
            try:
                if p['test'](f):
                    return '양인'
            except Exception:
                pass
            break
    g = f.ten_gods
    if int(g.get('상관', 0)) >= 2:
        return '상관'
    if int(g.get('편관', 0)) >= 1:
        return '편관'
    if f.strength == '신약':
        return '삼킴'
    return '보통'


def _alone_key(f) -> str:
    g = f.ten_gods
    if int(g.get('편인', 0)) >= 1 and int(g.get('편인', 0)) >= int(g.get('정인', 0)):
        return '편인'
    if int(g.get('정인', 0)) >= 1:
        return '정인'
    return '없음'


def _age_key(f) -> str:
    """대운 국면. `real.PHASE` 가 쓰는 낱말 그대로요 — 이름을 새로 지으면
    표에 없어 한 줄도 안 붙습니다."""
    if not f.daeun_started:
        return '들기전'
    rows = list(f.daeun or [])
    i = int(f.daeun_now)
    start = int((rows[i] or {}).get('start_age') or 0) if 0 <= i < len(rows) else 0
    gone = int(f.age) - start
    if gone <= 2:
        return '막들어옴'
    if gone >= 8:
        return '바뀔때'
    return '한가운데'


def _key(f, facet: str) -> Optional[str]:
    if facet == 'first':
        return f.day_gan
    if facet == 'talk':
        return f.top_ten_god
    if facet == 'work':
        return f.flow
    if facet == 'money':
        return _money_key(f)
    if facet == 'close':
        return _close_key(f)
    if facet == 'anger':
        return _anger_key(f)
    if facet == 'tired':
        return f.weak_el
    if facet == 'misread':
        return f.strong_el
    if facet == 'alone':
        return _alone_key(f)
    if facet == 'age':
        return _age_key(f)
    return None


# 근거 줄에 댈 **센 값**. 면마다 하나씩.
def _ground(f, facet: str, key: str) -> str:
    g = f.ten_gods
    if facet == 'first':
        return '일간 %s' % f.day_gan
    if facet == 'talk':
        return '가장 센 십신 %s %d자' % (key, int(g.get(key, 0)))
    if facet == 'work':
        from .bank import GROUP_TOTAL
        return '힘이 흐르는 쪽 %s %d자' % (key, int(getattr(f, GROUP_TOTAL[key], 0)))
    if facet == 'money':
        return '정재 %d자 · 편재 %d자' % (int(g.get('정재', 0)), int(g.get('편재', 0)))
    if facet == 'close':
        return '일지 %s · %s' % (f.day_ji, key)
    if facet == 'anger':
        # ★ **가른 값을** 댑니다. 무엇으로 갈랐든 같은 줄을 대면 그건
        #   근거가 아니라 장식이오 — 손님이 대 볼 수가 없소.
        return {'양인': '양인 · 일간 %s · 일지 %s' % (f.day_gan, f.day_ji),
                '상관': '상관 %d자' % int(g.get('상관', 0)),
                '편관': '편관 %d자' % int(g.get('편관', 0)),
                '삼킴': _why.strength_seen(f),
                '보통': '겁재 %d자 · 신강약 %s' % (int(g.get('겁재', 0)), f.strength),
                }.get(key, '신강약 %s' % f.strength)
    if facet == 'tired':
        return '가장 모자란 기운 %s' % key
    if facet == 'misread':
        return '가장 넘치는 기운 %s' % key
    if facet == 'alone':
        return '정인 %d자 · 편인 %d자' % (int(g.get('정인', 0)), int(g.get('편인', 0)))
    if facet == 'age':
        return '지금 %d살 · 대운 %s' % (int(f.age), f.daeun_ten_god)
    return ''


def _lead(lens_id: Optional[str]) -> str:
    """여는 줄 — 그 사람이 사람을 볼 때 **어디부터 보는가**."""
    if not lens_id:
        return '여덟 글자를 사람으로 옮기면 이렇소.'
    try:
        from .editorial import ROLES
        label = ROLES[lens_id][1]
    except Exception:
        return '여덟 글자를 사람으로 옮기면 이렇소.'
    return '나는 사람을 볼 때 <b>%s</b>부터 보오. 그 눈으로 그대를 그려 보겠소.' % escape(label)


def facets_for(lens_id: Optional[str], n: int) -> list:
    order = VIEW.get(lens_id or '') or DEFAULT_ORDER
    return list(order)[:max(1, n)]


def rows(f, lens_id: Optional[str] = None, n: int = 5) -> list:
    """
    편 면들. `[{"facet","head","say","ground"}]` — 표에 없으면 **건너뜁니다.**

    ★ 없는 칸을 지어내지 않소. 빈 목록이 나오는 것이 정상이오.
    """
    out = []
    for facet in facets_for(lens_id, n):
        key = _key(f, facet)
        say = (TABLES.get(facet) or {}).get(key or '')
        if not say:
            continue
        out.append({'facet': facet, 'head': HEAD[facet], 'key': key,
                    'say': say, 'ground': _ground(f, facet, key)})
    return out


def build(f, lens_id: Optional[str] = None, n: int = 5,
          you: str = '그대', seen=None, lead: bool = True) -> Optional[dict]:
    """한 컷. `{"id","title","html","source","statement_id"}`"""
    got = rows(f, lens_id, n)
    if not got:
        return None
    parts = []
    if lead:
        parts.append('<p class="pt-lead">%s</p>' % _lead(lens_id))
    for r in got:
        parts.append('<p class="pt-face"><b>%s</b> — %s</p>'
                     % (escape(r['head']), r['say']))
    # ★ 센 값을 **본문에** 세웁니다 (2026-09-24).
    #
    #   근거 줄에만 두었더니 팩폭 자가 80 을 냈습니다. 이 집이 한 번
    #   겪은 자리요 — 세는 값이 접힌 줄에만 있으면 손님은 그림만 읽고
    #   「그래서 어디서 나온 말이오」 를 못 봅니다.
    #   자리는 **그림 아래**요. 위에 두면 첫 문단이 강의가 되오.
    parts.append('<p class="pt-count">이 그림이 나온 자리 — <b>%s</b></p>'
                 % escape(' · '.join(r['ground'] for r in got)))
    parts.append('<p class="pt-close">%s</p>' % CLOSING)
    body = ''.join(parts)
    # ★ 여기서 풀이를 달지 않습니다 (2026-09-24).
    #
    #   리포트가 컷마다 `terms.gloss` 를 한 번 더 겁니다(engine/report 끝).
    #   그래서 같은 괄호가 **잇달아 두 번** 찍혀 나갔습니다 —
    #   「식상(말·글·솜씨처럼 내가 밖으로 내놓는 것)(말·글·솜씨처럼
    #   내가 밖으로 내놓는 것) 4자」. 1만 명 전원이 이 줄을 봤습니다.
    #   풀이는 **한 장에 한 곳에서** 답니다. 부르는 쪽이 `seen` 을 들고
    #   있으니 여기서 달면 그 셈이 두 벌이 되오.
    if seen is not None:
        body = terms.gloss(body, seen, None, f.sex)
    body = voice.address(body, escape(you))
    pillars = '네 기둥' if f.hour_known else '세 기둥 · 태어난 시각 제외'
    source = _why.axis_line(
        escape('%s · %s' % (pillars, ' · '.join(r['ground'] for r in got))),
        AXIS_OF.get(got[0]['facet'], 'day_gan'))
    sid = '%s:%s:%s' % (VERSION, lens_id or '-',
                        sha256(''.join(r['facet'] + ':' + str(r['key'])
                                       for r in got).encode()).hexdigest()[:16])
    return {'id': 'portrait', 'title': TITLE,
            'html': guard.enforce(body, {'statement_id': sid}),
            'source': guard.enforce(source, {'statement_id': sid}),
            'statement_id': sid, 'facets': [r['facet'] for r in got]}
