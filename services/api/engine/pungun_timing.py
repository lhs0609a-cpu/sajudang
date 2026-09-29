"""Pungun's timing reading, assembled only from calculated Features.

The analysis describes traditional symbolic relationships, not event predictions.
No personality questionnaire or invented monthly timing enters this reading.
"""
from html import escape

from .constants import CHUNG, HAP, ELEMENT_OF_GAN, TEN_GOD_GROUP

THEMES = {
    '비견': ('자기 기준과 독립', '함께하더라도 결정권과 각자의 몫을 분명히 하는 문제'),
    '겁재': ('경쟁과 자원 배분', '같은 시간·돈·기회를 여러 사람이 나누는 문제'),
    '식신': ('꾸준한 생산과 생활', '반복해서 유지할 수 있는 속도와 결과를 만드는 문제'),
    '상관': ('표현과 기존 방식의 수정', '생각을 밖으로 드러내고 맞지 않는 규칙을 바꾸는 문제'),
    '편재': ('외부 기회와 넓은 교류', '선택지가 늘어날 때 자원을 어디에 배분할지 정하는 문제'),
    '정재': ('지속할 수 있는 관리', '수입·시간·약속을 예측 가능한 범위로 정리하는 문제'),
    '편관': ('요구와 대응력', '외부의 요구에 대응하면서 감당할 수 있는 한도를 정하는 문제'),
    '정관': ('역할과 공식 기준', '책임·절차·평가 기준을 명확히 하는 문제'),
    '편인': ('관점 전환과 재검토', '익숙한 해석에서 벗어나 필요한 지식과 방법을 다시 고르는 문제'),
    '정인': ('학습과 지원 기반', '배우고 도움받으며 판단의 근거를 쌓는 문제'),
}
CONCERNS = {
    'people': '사람을 좋은 인연과 나쁜 인연으로 나누기보다, 관계에서 요구되는 역할이 지금의 역량과 맞는지를 읽겠소.',
    'work': '이직 여부를 단정하기보다, 맡는 역할과 성과를 내는 방식 중 어느 쪽의 조정이 필요한지를 읽겠소.',
    'money': '수익이 생길 날짜를 예언하기보다, 기회를 넓히는 힘과 자원을 관리하는 힘의 관계를 읽겠소.',
    'love': '상대의 마음이나 만날 날짜를 단정하기보다, 관계를 유지하는 방식과 현재의 요구가 어떻게 맞물리는지 읽겠소.',
    'dir': '정해진 직업 하나를 찍기보다, 새로 시도할 때와 기반을 다질 때의 기준을 읽겠소.',
    'health': '몸의 증상은 이 계산으로 판단하지 않소. 여기서는 활동과 회복에 배분하는 힘의 균형만 읽겠소.',
    'real_estate': '매수·매도의 시점을 정답처럼 제시하지 않소. 확장과 유지의 기준을 실제 자금·계약 조건과 구분해서 읽겠소.',
}


def _calculation(f, concern):
    """Return a self-contained, chart-specific free timing analysis."""
    parts = [f'<p class="timing-summary">그대의 {f.year_num}년을 읽는 중심은 '
             f'{escape(THEMES[f.year_ten_god][0])}이오. '
             '타고난 구조 위에 지금 어떤 조건이 더해졌는지, 계산된 글자를 하나씩 맞대 보겠소.</p>']

    def section(title, text):
        parts.append(f'<h3>{escape(title)}</h3><p>{escape(text)}</p>')

    pillars = ' · '.join(p['label'] + ' ' + p['gz'] for p in f.pillars)
    month = next(p for p in f.pillars if p['label'] == '월주')
    roots = ('월지에서 나를 돕는 계절 조건이 잡히오.' if f.deuk_ryeong else
             '월지에서는 나를 돕는 계절 조건이 잡히지 않소.')
    footing = ('일지에도 나를 돕는 조건이 있소.' if f.deuk_ji else
               '일지 역시 나를 돕는 조건으로 집계되지는 않소.')
    strength = {
        '신강': '이 계산에서는 나를 지지하는 쪽의 힘이 상대적으로 크오. 들어오는 운을 볼 때 힘이 더해지는지만큼, 그 힘을 표현·성과·책임으로 옮길 통로가 있는지를 보오.',
        '신약': '이 계산에서는 나를 지지하는 쪽의 힘이 상대적으로 작소. 표현·성과·책임이 늘어나는 운이라면 그것을 받쳐 줄 학습·지원·회복 조건을 함께 보오.',
        '중화': '이 계산에서는 한쪽으로 크게 기울지 않은 상태요. 들어오는 운이 무엇을 더하는지에 따라 균형을 읽는 방향도 달라지므로 신강·신약 어느 한쪽의 설명에 고정하지 않소.',
    }[f.strength]
    section('명식의 출발점 · 버틸 힘은 어디에서 오는가',
            f'{pillars}. 나를 뜻하는 일간은 {f.day_gan}({ELEMENT_OF_GAN[f.day_gan]})이고, 태어난 달은 {month["gz"]}요. '
            f'{roots} {footing} 득령·득지와 오행 가중치를 합한 판정은 {f.strength}요. {strength}')

    top = [tg for tg, count in f.ten_gods.items() if count == max(f.ten_gods.values())]
    weights = ' · '.join(f'{el} {value:g}' for el, value in f.elements.items())
    section('원래 두드러진 힘과 부족한 통로',
            f'천간과 지지 본기를 기준으로 센 십신에서는 {"·".join(top)}이 각각 {f.ten_gods[top[0]]}회로 '
            + ('공동 최다요. 하나만 그대의 성격으로 단정하지 않소. ' if len(top) > 1 else '가장 많이 잡히오. ')
            + f'지장간을 포함한 오행 가중치는 {weights}요. 이는 글자 개수가 아니라 본기·중기·여기의 가중합이오. '
            + f'현재 억부법 계산의 보완 후보는 {f.yongsin}요. 적게 나온 오행이 곧 없는 능력을 뜻하지는 않으며, 이 후보 하나로 길흉을 정하지 않소.')

    year_title, year_meaning = THEMES[f.year_ten_god]
    annual_group = TEN_GOD_GROUP[f.year_ten_god]
    if f.daeun_started and f.daeun:
        current = f.daeun[f.daeun_now]
        start = f.birth_year + int(current['start_age'])
        dtg = f.daeun_ten_god
        dtitle, dmeaning = THEMES[dtg]
        section('지금의 대운 · 오래 이어지는 배경',
                f'현재 대운은 {current["gz"]}, 천간의 십신은 {dtg}요. 앱의 연 나이 기준으로 {start}년부터 들어오는 구간이오. '
                f'명리에서는 {dtg}을 {dtitle}의 주제로 읽소. 이 기간의 배경을 {dmeaning}로 보는 것이오. '
                '대운이 바뀌는 해를 사건의 발생일로 해석하지 않소. 이 연도 표기는 정밀한 전환 일시를 뜻하지 않소.')
        dgroup = TEN_GOD_GROUP[dtg]
        if dgroup == annual_group:
            overlap = f'대운의 {dtg}과 올해의 {f.year_ten_god}은 같은 {annual_group} 계열이오. 장기 배경과 올해의 주제가 겹치므로, 새 문제가 갑자기 생겼다고 보기보다 원래 다루던 주제가 더 선명해지는 구조로 읽소.'
        else:
            overlap = f'대운의 {dtg}은 {dtitle}, 올해의 {f.year_ten_god}은 {year_title}을 가리키오. 장기적으로는 {dmeaning} 위에 올해는 {year_meaning}가 포개지는 구조요. 두 기준이 서로 맞는지, 한쪽을 좇느라 다른 쪽을 놓치는지 구분해서 보오.'
    else:
        section('지금의 대운 · 아직 진입 전',
                '계산상 첫 대운에 아직 들어가지 않았소. 목록의 첫 대운을 현재 운처럼 붙이지 않겠소. 지금의 해석은 원국과 올해 세운의 관계에 한정하오.')
        overlap = f'현재 대운을 전제하지 않고, 원국 위에 올해의 {year_title} 주제가 더해지는 관계만 읽겠소.'

    section(f'{f.year_num}년 세운 · 왜 하필 지금인가',
            f'입춘으로 구분한 {f.year_num}년은 {f.year_gz}년이오. 그 천간을 {f.day_gan}일간과 비교하면 {f.year_ten_god}이오. '
            f'올해의 상징적 주제는 {year_meaning}요. {overlap}')

    year_ji = f.year_gz[-1]
    contacts = []
    for p in f.pillars:
        ji = p['ji']
        if CHUNG.get(year_ji) == ji:
            contacts.append(f'{p["label"]} {ji}와 올해 {year_ji}는 충 관계요. 기존 방식과 새 요구의 마찰을 살피는 표시로 읽되, 이별·사고 같은 사건으로 바꾸어 말하지 않소.')
        elif HAP.get(year_ji) == ji:
            contacts.append(f'{p["label"]} {ji}와 올해 {year_ji}는 육합 관계요. 연결과 조율의 주제로 읽되, 좋은 관계의 성립이나 합화가 자동으로 확정되는 것은 아니오.')
        elif year_ji == ji:
            contacts.append(f'{p["label"]}의 {ji}가 올해 지지와 같소. 같은 지지가 다시 등장한다는 사실이며, 이것만으로 복음이나 길흉을 확정하지 않소.')
    section('올해 글자가 원국에 닿는 자리', ' '.join(contacts) if contacts else
            f'올해 지지 {year_ji}와 확인된 원국 지지 사이에서는 육합·충·같은 글자의 반복이 잡히지 않소. 이 세 관계가 없다는 사실을 변화가 없거나 평온하다는 예측으로 바꾸지는 않소.')
    support_group = annual_group in ('비겁', '인성')
    direction = ('나를 지지하는 계열' if support_group else '표현·성과·책임으로 힘을 쓰는 계열')
    focus = {
        ('신강', True): '이미 지지하는 힘이 큰 원국에 같은 방향이 더해지는 셈이오. 기반을 더 쌓는 것과 쌓인 힘을 실제 결과로 내보내는 것의 균형이 해석의 핵심이오.',
        ('신강', False): '원국에서 지지받는 힘을 밖으로 사용하는 방향이 들어온 셈이오. 힘을 쓸 통로로 읽을 수 있지만, 성과나 보상이 자동으로 따라온다는 뜻은 아니오.',
        ('신약', True): '원국에서 상대적으로 작게 잡힌 지지 기반과 같은 방향이 들어온 셈이오. 기반을 보완하는 주제로 읽되, 세운 천간 하나가 원국 전체의 강약을 뒤집는다고 보지는 않소.',
        ('신약', False): '지지 기반보다 힘을 쓰는 방향이 더해지는 셈이오. 새 요구의 크기와 실제로 받을 수 있는 지원을 함께 살피는 것이 이 조합의 핵심이오.',
        ('중화', True): '기존 균형 위에 기반을 다지는 방향이 더해지는 셈이오. 준비가 깊어지는 것과 실행이 늦어지는 것을 구분해 읽소.',
        ('중화', False): '기존 균형 위에 힘을 밖으로 쓰는 방향이 더해지는 셈이오. 표현·성과·책임 중 올해의 십신이 가리키는 주제에 무게를 두되, 균형이 무너졌다고 미리 단정하지 않소.',
    }[(f.strength, support_group)]
    section('이 구조를 물으신 일에 대입하면',
            f'원국의 {f.strength} 판정에 올해는 {direction}인 {annual_group}이 들어오오. {focus} '
            + CONCERNS.get(concern, CONCERNS['dir']))
    scope = ('출생시가 없어 시주는 제외했소. 시주가 들어오면 강약과 보완 후보, 시지와의 관계가 달라질 수 있소. ' if not f.hour_known else '')
    section('이 해석의 범위', scope + '위 글은 계산된 원국·대운·세운을 전통 명리의 관계로 해석한 것이오. MBTI나 선택형 성격 답변으로 계산을 바꾸지 않았소. 월운·일운과 실제 사건의 발생 여부는 이 분석에 포함하지 않소.')
    return '<div class="pungun-timing">' + ''.join(parts) + '</div>'


# The first reading is written for someone who has never studied saju.
# Technical names and all counted evidence remain in the expandable calculation.
EASY = {
    '비견': ('내가 원하는 것을 분명히 하는 일', '남에게 맞추기 전에 내 뜻을 정하는 시기', '같이할 일과 혼자 정할 일을 나누어 보시오.'),
    '겁재': ('시간과 돈을 누구와 나눌지 정하는 일', '사람들과 함께하면서 내 몫도 챙기는 시기', '함께 시작한다면 비용과 책임을 먼저 나누시오.'),
    '식신': ('꾸준히 해 온 일을 결과로 만드는 일', '한 가지를 오래 익혀 내 것으로 만드는 시기', '일을 늘리기 전에 지금 하던 일을 끝내는 순서를 정하시오.'),
    '상관': ('내 생각을 말하고 일하는 방식을 바꾸는 일', '익숙한 방법을 고쳐 보는 시기', '불편하다는 말에 바꾸고 싶은 방법 하나를 덧붙이시오.'),
    '편재': ('새 기회를 고르고 돈을 쓸 곳을 정하는 일', '새로운 사람과 기회를 넓게 살피는 시기', '좋아 보이는 제안도 쓸 돈과 시간을 먼저 계산하시오.'),
    '정재': ('들어오고 나가는 돈을 꾸준히 챙기는 일', '돈과 약속을 안정적으로 관리하는 시기', '매번 새 계획을 세우기보다 지킬 수 있는 기준 하나를 정하시오.'),
    '편관': ('늘어난 요구를 어디까지 받아들일지 정하는 일', '어려운 요구에 대처할 방법을 익히는 시기', '급한 일일수록 마감과 맡을 범위를 먼저 확인하시오.'),
    '정관': ('내 역할과 책임을 분명히 하는 일', '일의 기준과 책임을 정리하는 시기', '무엇을 잘해야 하는지 평가 기준부터 맞춰 보시오.'),
    '편인': ('배우던 방법과 생각을 다시 살펴보는 일', '혼자 배우고 생각을 정리하는 시기', '자료를 더 모으기 전에 지금 아는 것으로 작은 결과 하나를 만들어 보시오.'),
    '정인': ('필요한 도움을 받고 기초를 다지는 일', '배우고 도움받으며 준비하는 시기', '혼자 해결하기 어려운 부분은 무엇을 도와주면 되는지 말하시오.'),
}
EXAMPLES = {
    'work': '회사라면 “지금 방식에서 시간이 가장 오래 걸리는 부분은 여기입니다”처럼 말할 수 있소.',
    'money': '돈 문제라면 수입만 보지 말고, 그 일을 위해 드는 비용과 시간도 함께 적어 보시오.',
    'people': '사람 문제라면 “내가 맡을 수 있는 건 여기까지야”처럼 서로 맡을 일을 분명히 할 수 있소.',
    'love': '연인 사이라면 “알아서 해줬으면 좋겠어”보다 원하는 연락이나 만남을 하나만 말해 보시오.',
    'dir': '진로라면 직업 이름부터 고르기보다, 일주일 동안 직접 해볼 일 하나로 좁혀 보시오.',
    'health': '생활을 돌아볼 때는 잠·일·휴식 시간을 함께 보시오. 몸의 증상은 사주로 판단하지 않소.',
    'real_estate': '집 문제라면 원하는 조건과 매달 감당할 비용을 따로 적어 보시오. 계약 판단은 실제 자료를 확인해야 하오.',
}


def build(f, concern):
    topic, _, action = EASY[f.year_ten_god]
    parts = []
    def section(title, body):
        parts.append(f'<h3>{escape(title)}</h3><p>{escape(body)}</p>')

    section(f'{f.year_num}년, 먼저 볼 것은 이것이오',
            f'그대의 올해 사주는 “{topic}”에 초점을 두고 읽소. '
            '같은 일을 더 오래 붙잡는 것보다, 지금 어떤 방법이 필요한지 살펴보겠소.')
    strongest = [k for k, v in f.ten_gods.items() if v == max(f.ten_gods.values())]
    if len(strongest) > 2:
        section('그대가 자주 신경 쓰는 일',
                '여러 특징의 글자 수가 같게 나왔소. 한 가지 성격으로 묶기보다 다음 특징을 함께 살피겠소.')
        parts.append('<ul>'+''.join('<li>'+escape(EASY[t][0])+'</li>' for t in strongest)+'</ul>')
        parts.append('<p>이 중 실제로 중요하게 여기는 일이 무엇인지 경험과 맞춰 보시오.</p>')
    else:
        descriptions = ' · '.join(EASY[t][0] for t in strongest)
        section('그대가 자주 신경 쓰는 일',
                f'태어난 사주에서는 “{descriptions}”에 해당하는 글자가 가장 많이 보이오. '
                + ('여러 특징이 함께 보여 한 가지 성격으로 묶지는 않겠소. ' if len(strongest)>1 else '')
                + '이 일을 중요하게 여기는 편으로 읽을 수 있소. 실제 경험과 맞는지 함께 보시오.')
    if f.daeun_started and f.daeun:
        current = f.daeun[f.daeun_now]
        start = f.birth_year + int(current['start_age'])
        background = EASY[f.daeun_ten_god][1]
        same = TEN_GOD_GROUP[f.daeun_ten_god] == TEN_GOD_GROUP[f.year_ten_god]
        section('왜 지금 이 이야기를 하는가',
                f'계산상 {start}년부터 이어지는 긴 기간은 “{background}”로 읽소. '
                f'그 안에서 {f.year_num}년에는 “{topic}”이 더해지오. '
                + ('몇 년 동안 다뤄 온 주제를 올해 다시 살피는 셈이오.' if same else
                   '몇 년 동안 중요했던 일과 올해 새로 신경 쓸 일이 다른 셈이오. 둘 중 무엇을 먼저 할지 순서를 정하는 것이 중요하오.'))
    else:
        section('왜 지금 이 이야기를 하는가',
                '아직 첫 10년 운에 들어가기 전이오. 긴 기간의 운을 억지로 붙이지 않고, 태어난 사주와 올해만 비교했소.')
    practical = {
        '신강': '계획을 계속 더하기보다, 이미 준비한 것을 밖으로 보여줄 방법을 살펴보시오.',
        '신약': '해야 할 일이 늘어난다면, 혼자 해낼 수 있는 양과 도움받을 일을 먼저 나누시오.',
        '중화': '무조건 혼자 밀어붙이거나 전부 남에게 맡길 필요는 없소. 지금 맡은 일의 양과 도움받을 수 있는 조건을 함께 보시오.',
    }[f.strength]
    section('내 상황에서는 이렇게 읽으면 되오', practical + ' ' + action)
    section('생활 속에서 써본다면', EXAMPLES.get(concern, EXAMPLES['dir']))
    scope = '사주를 이렇게 읽을 수 있다는 설명이오. 어떤 일이 생길 날짜를 정한 것은 아니오.'
    if not f.hour_known:
        scope += ' 태어난 시간을 몰라 그 부분은 빼고 읽었소. 시간을 알게 되면 해석이 달라질 수 있소.'
    parts.append(f'<p class="reading-scope">{escape(scope)}</p>')
    parts.append('<details class="reading-calculation"><summary>왜 이렇게 읽었는지 · 계산 근거 보기</summary>'
                 + _calculation(f, concern) + '</details>')
    return '<div class="pungun-timing easy-reading">' + ''.join(parts) + '</div>'
