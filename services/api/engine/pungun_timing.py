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


def build(f, concern):
    """Return a self-contained, chart-specific free timing analysis."""
    parts = []

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
