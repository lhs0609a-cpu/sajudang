"""Authored summaries grounded in chart counts and explicitly selected answers.

No invented biography, inferred interview answer, or prediction confidence.
Original, calculated evidence is retained beside the reading edition.
"""
from html import escape
from .pungun_timing import EASY
from .constants import TEN_GOD_GROUP
from .easy_specialists import INTRO
from .character_consultation import INTERVIEWS
from .consultation_decisions import decide

VERSION = 'personal-reading-v3'
TITLES = {
 'chart':'입력한 생년월일로 계산한 사주', 'portrait':'사주에서 읽은 나의 특징',
 'spine':'이 풀이의 핵심', 'concern':'물어본 고민에서 먼저 볼 것',
 'lack':'적게 보이는 글자는 어떻게 읽을까', 'rarity':'다른 사주와 비교한 계산 특징',
 'place':'가까운 관계에서 살필 점', 'daeun_now':'지금 이어지는 10년의 주제',
 'yongsin':'균형을 위해 보완할 점', 'daeun_map':'시기마다 달라지는 주제',
 'sinsal':'글자 조합에 붙은 상징', 'helper':'도움이 되는 조건을 찾는 법',
 'ancestor':'태어난 해의 글자로 읽는 배경', 'concern_scale':'이 고민에서 계산한 내용',
 'concern_pattern':'여러 특징이 함께 나타날 때', 'concern_turn':'이 고민을 시기와 함께 읽으면',
 'concern_face':'내가 고른 성격 유형과 비교하면', 'hindsight':'지나온 경험과 맞춰 볼 점',
 'counter':'내 경험과 다르다면', 'why':'이런 설명이 나온 이유',
 'solace':'내 잘못으로만 생각하지 않아도 될 일', 'hope':'이미 활용할 수 있는 점',
 'week':'이번 주에 해볼 한 가지', 'closing_cut':'끝으로 기억할 것',
}
# Useful condition, possible cost, observable way to tell the two apart.
TRAITS = {
 '비견': ('스스로 순서를 정하고 끝까지 맡을 수 있을 때', '도움받을 수 있는 일까지 혼자 맡을 때', '혼자 해야 빨라지는 일인지, 함께하면 시간을 줄일 수 있는 일인지 보시오.'),
 '겁재': ('다른 사람과 역할을 나눠 함께 움직일 때', '사람에게 맞추다가 내 시간과 돈의 한도를 넘을 때', '함께하기로 한 약속에 각자의 몫이 적혀 있는지 보시오.'),
 '식신': ('익숙한 일을 꾸준히 해서 결과를 쌓을 때', '완성도를 높이느라 끝내거나 보여줄 때를 놓칠 때', '더 고치면 무엇이 좋아지는지 한 가지를 말할 수 있는지 보시오.'),
 '상관': ('문제를 발견하고 더 나은 방법을 제안할 때', '고쳐야 할 점을 한꺼번에 말해 중요한 제안이 묻힐 때', '불편한 점 다음에 상대가 할 수 있는 요청 하나가 붙어 있는지 보시오.'),
 '편재': ('새로운 사람이나 일을 만나 기회를 넓힐 때', '여러 제안을 받아들여 쓸 돈과 시간이 흩어질 때', '새 일을 시작한 뒤에도 이미 한 약속을 지킬 여유가 남는지 보시오.'),
 '정재': ('돈과 일정을 정해 둔 기준에 맞춰 꾸준히 관리할 때', '계획이 바뀔까 봐 필요한 조정까지 미룰 때', '지키려는 기준이 지금도 도움이 되는지, 습관만 남은 것인지 보시오.'),
 '편관': ('어려운 요구 앞에서 우선순위를 세우고 대응할 때', '급하다는 이유만으로 내 몫이 아닌 일까지 받아들일 때', '마감과 맡을 범위를 함께 정했는지, 급하다는 말만 들었는지 보시오.'),
 '정관': ('서로 지킬 기준과 맡을 역할이 분명할 때', '기준을 지키려다 내 사정이나 필요한 도움을 말하지 못할 때', '문제가 생겼을 때 약속을 다시 조정할 수 있는지 보시오.'),
 '편인': ('혼자 깊이 살피며 익숙한 설명을 다시 검토할 때', '생각과 자료가 늘어나는데 실제로 해본 일은 없을 때', '새로 알아본 정보가 다음 행동을 바꾸었는지 보시오.'),
 '정인': ('배우고 도움받으며 기초를 충분히 다질 때', '준비가 끝났다는 허락을 기다리느라 시작이 늦어질 때', '지금 아는 것만으로 안전하게 해볼 작은 일이 있는지 보시오.'),
}

# The same calculated group has different practical meanings by concern.
EXAMPLES = {
 'work': {
  '비겁':'업무를 나눌 때 “누가 무엇을 언제까지 끝낼지”를 적어 보시오.',
  '식상':'의견을 낼 때 바꾸고 싶은 작업 하나와 그 이유를 함께 말해 보시오.',
  '재성':'새 업무를 맡기 전에 늘어날 시간과 받을 보상을 함께 확인하시오.',
  '관성':'마감이 겹치면 “어느 일을 뒤로 미뤄도 되는지”를 먼저 물어보시오.',
  '인성':'자료를 더 찾기 전에 지금 아는 내용으로 짧은 초안을 만들어 보시오.'},
 'money': {
  '비겁':'함께 쓰는 돈이라면 각자가 낼 금액과 더 내지 않을 한도를 먼저 정하시오.',
  '식상':'돈을 벌 계획이라면 누가 어떤 결과에 값을 지불하는지부터 확인하시오.',
  '재성':'들어온 돈에서 고정 지출을 빼고 실제 남는 금액을 비교해 보시오.',
  '관성':'도와줘야 한다는 부담이 들어도 이미 약속한 지출부터 확인하시오.',
  '인성':'모르는 비용이나 조건을 적고, 그 답을 확인한 뒤 결정하시오.'},
 'love': {
  '비겁':'서로 혼자 보내고 싶은 시간과 함께할 시간을 말로 맞춰 보시오.',
  '식상':'서운함을 한꺼번에 설명하기보다 바라는 연락 방식 하나를 말해 보시오.',
  '재성':'마음의 크기와 실제로 지킬 수 있는 시간·돈의 약속을 따로 보시오.',
  '관성':'연인 사이에서도 거절하거나 약속을 조정할 수 있는지 보시오.',
  '인성':'상대의 뜻을 혼자 추측하기보다 실제로 한 말과 다음 행동을 함께 보시오.'},
 'people': {
  '비겁':'부탁을 받으면 함께 맡을 사람과 내 몫을 먼저 정하시오.',
  '식상':'말이 길어질 때는 상대에게 바라는 행동 하나로 줄여 보시오.',
  '재성':'도울 마음이 있어도 가능한 금액과 시간을 먼저 말하시오.',
  '관성':'거절했을 때 상대가 조건을 조정하는지, 죄책감을 주는지 살펴보시오.',
  '인성':'상대를 이해한 것과 그 부탁을 받아들이는 것을 같은 뜻으로 두지 마시오.'},
 'dir': {
  '비겁':'남의 기대를 빼고도 내가 고르고 싶은 이유가 남는지 적어 보시오.',
  '식상':'관심 있는 일을 작게 만들어 보여주고 실제 반응을 받아 보시오.',
  '재성':'좋아 보이는 기회라도 배우는 비용과 생활비를 함께 계산하시오.',
  '관성':'이름이 좋은 직업인지보다 실제 맡을 업무와 책임을 알아보시오.',
  '인성':'정보 하나를 더 알면 선택이 바뀌는지부터 확인하시오.'},
 'health': {
  '비겁':'쉴 시간을 만들기 위해 다른 사람과 나눌 일을 찾아보시오.',
  '식상':'하던 일을 어디서 끝낼지 정하고 남은 일은 따로 적어 두시오.',
  '재성':'일정과 비용 때문에 휴식을 미루는지 생활 조건을 살펴보시오.',
  '관성':'모든 부탁을 받아들여 쉬는 시간이 사라지지는 않는지 보시오.',
  '인성':'휴식법을 더 찾기 전에 잠과 일의 시간을 기록해 보시오.'},
 'real_estate': {
  '비겁':'공동으로 부담한다면 각자 낼 돈과 책임을 문서로 확인하시오.',
  '식상':'원하는 집의 조건을 모두 늘어놓기보다 꼭 필요한 조건부터 고르시오.',
  '재성':'매매가뿐 아니라 이자·세금·수리비까지 넣어 감당할 비용을 계산하시오.',
  '관성':'계약을 서두르라는 말보다 서류와 실제 부담 조건을 확인하시오.',
  '인성':'모르는 계약 조건은 뜻을 확인하고 필요한 전문가에게 물어보시오.'},
}


def _section(title, body):
    return f'<h3>{escape(title)}</h3><p>{escape(body)}</p>'


def leaders(f):
    highest=max(f.ten_gods.values())
    return [key for key,value in f.ten_gods.items() if value==highest]


def build_depth(f, lens_id, concern):
    from .chart_synthesis import core
    return core(f,lens_id,concern)


def selected(lens_id, topic):
    row=INTERVIEWS[lens_id]
    choices=[]
    for key,options in [('choice4',row[2]),('choice5',row[4])]:
        option=next((o for o in options if o['id']==(topic or {}).get(key)),None)
        if not option: return None
        choices.append(option['label'])
    return choices,decide(lens_id,topic['choice4'],topic['choice5'])


def build_scene(f, lens_id, concern, topic=None):
    from .chart_synthesis import analyze, timing_text, contact_text, section, PRIORITY, year_fit
    synthesis=analyze(f)
    answer=selected(lens_id,topic)
    parts=[_section('지금 함께 볼 이야기',INTRO[lens_id])]
    if answer:
        labels,decision=answer
        parts.extend([_section('직접 고른 상황',f'“{labels[0]}”, “{labels[1]}”이라고 답했소. 이 부분은 생년월일로 짐작한 것이 아니라 직접 고른 답이오.'),
                      _section('그 답에서 먼저 살필 점',decision['reading'])])
    else:
        parts.append(_section('실제 상황과 맞춰볼 곳',EXAMPLES.get(concern,EXAMPLES['dir'])[TEN_GOD_GROUP[f.top_ten_god]]+
                              ' 아직 세부 상황을 듣지 못했으므로 실제로 겪었다고 단정하지 않겠소.'))
    parts.append(section('왜 하필 지금 이 이야기를 하는가',*timing_text(f,synthesis)))
    parts.append(year_fit(f,synthesis))
    parts.append(section('올해 글자가 닿는 생활 자리',*contact_text(synthesis['year_contacts'],'올해')))
    parts.append(_section('태어난 사주와 함께 정한 순서',PRIORITY[synthesis['priority']][1]))
    if answer:
        parts.extend([_section('지금 할 한 가지',answer[1]['action']),_section('그다음 확인할 것',answer[1]['review'])])
    else:
        parts.append(_section('생활에서 확인해 보려면',TRAITS[f.year_ten_god][2]))
    parts.append(_section('해석과 실제 경험을 구분하시오','글자의 관계를 전통적인 뜻으로 읽은 것이며 실제 사건을 확인한 것은 아니오.'+
                         (' 태어난 시간을 몰라 그 부분은 제외했소.' if not f.hour_known else '')))
    return '<div class="personal-reading">'+''.join(parts)+'</div>'


def evidence(original):
    return '<details class="reading-calculation"><summary>계산과 자세한 풀이 보기</summary>'+original+'</details>'


def build_paid(cut_id, f, concern):
    """Paid common chapters answer distinct questions, without invented events."""
    from . import chart_synthesis
    if cut_id=='why':
        return chart_synthesis.why(f,concern)
    if cut_id=='daeun_now':
        return chart_synthesis.period(f,concern)
    if cut_id=='yongsin':
        return chart_synthesis.balance(f,concern)
    group=TEN_GOD_GROUP[f.top_ten_god]
    example=EXAMPLES.get(concern,EXAMPLES['dir'])[group]
    if cut_id=='lack':
        from .reading_facts import visible_elements
        names={'목':'나무','화':'불','토':'흙','금':'금속','수':'물'}
        counts=visible_elements(f)
        lowest=min(counts.values())
        weak=[names[k] for k,v in counts.items() if v==lowest]
        phrase=' · '.join(weak)
        fact=(f'그대 사주에 겉으로 보이지 않는 것은 {phrase}에 해당하는 글자요.' if lowest==0 else
              f'그대 사주에서 겉으로 가장 적게 보이는 것은 {phrase}에 해당하는 글자요.')
        parts=[_section('계산에서 확인한 것',fact),
               _section('이 숫자를 어떻게 읽을까','글자가 적다는 사실을 재능이나 능력이 부족하다는 뜻으로 읽지는 않소. 아래 글자 속에 담긴 성분까지 세는 계산과도 구분해야 하오.'),
               _section('물어본 일에서 살펴볼 조건',example),
               _section('내 경험으로 확인할 기준','혼자 할 때 막혔던 일이 도움·시간·정보가 생긴 뒤 달라졌는지 보시오. 조건을 바꿔도 같다면 글자의 많고 적음만으로 이유를 정하지 마시오.')]
        hidden=[names[k] for k,v in counts.items() if v==0 and f.elements[k]>0]
        parts.insert(2,_section('겉의 글자와 속의 성분을 함께 보면',
            ('겉에서는 보이지 않아도 아래 글자 속에 '+ ' · '.join(hidden)+' 성분이 들어 있소. 전혀 없다고 읽으면 이 차이를 놓치오.' if hidden else
             '겉의 글자 수와 아래 글자 속 성분의 비중은 서로 다른 계산이오. 적은 글자만 채우면 된다는 결론으로 넘어가지 않소.')))
        synthesis=chart_synthesis.analyze(f)
        parts.insert(3,chart_synthesis.section('전체 균형에서는 이렇게 읽소',*chart_synthesis.support_text(f,synthesis)))
        parts.append(_section('이번에 먼저 조정할 것',chart_synthesis.PRIORITY[synthesis['priority']][1]))
    elif cut_id=='rarity':
        from .rarity import look
        row=look(f)
        parts=[_section('비교 표본에서 나온 결과',f'비교 표본 {row["sample"]:,}건 중 그대 사주와 같은 계산 특징을 가진 묶음은 {row["count"]:,}건이오.'),
               _section('무엇이 같다는 뜻인가','글자 구성과 강약, 도움을 뜻하는 조합, 가까운 자리의 충돌을 묶어 비교한 수요. 성격이나 살아온 일이 같은 사람을 센 것은 아니오.'),
               _section('이 결과를 사용할 때','드물다고 더 좋거나, 흔하다고 덜 특별한 것은 아니오. 나와 다른 사람이 같은 설명을 받아도 실제 선택은 각자의 시간·돈·관계 조건에 맞춰야 하오.')]
    else:
        return None
    return '<div class="personal-reading">'+''.join(parts)+'</div>'


def paid_evidence(cut_id, f):
    from .reading_facts import visible_elements
    if cut_id=='lack':
        detail='겉으로 보이는 글자 수: '+ ' · '.join(f'{k} {v}' for k,v in visible_elements(f).items())
    elif cut_id=='rarity':
        from .rarity import look
        row=look(f)
        detail=f'비교 표본 {row["sample"]}건 · 같은 분류 {row["count"]}건. 전체 인구의 비율이나 적중률을 뜻하지 않습니다.'
    elif cut_id=='yongsin':
        detail=f'강약 계산 {f.strength} · 억부법 보완 후보 {f.yongsin}. '+ ' · '.join(f'{k} {v}' for k,v in f.elements.items())
    elif cut_id=='daeun_now':
        current=f.daeun[f.daeun_now] if f.daeun_started and f.daeun else None
        detail=(f'현재 대운 {current["gz"]} · 시작 연 나이 {current["start_age"]} · {f.daeun_ten_god}. ' if current else '첫 대운 진입 전. ')
        detail+=f'세운 {f.year_num}년 {f.year_gz} · {f.year_ten_god}.'
    else:
        detail='십신 글자 수: '+' · '.join(f'{k} {v}' for k,v in f.ten_gods.items())
        detail+=f'. 강약 계산 {f.strength}. 행동이나 체력을 측정한 값은 아닙니다.'
    return evidence('<p>'+escape(detail)+'</p>')


def basis(f,lens_id,concern,topic):
    answer=selected(lens_id,topic)
    return {'version':VERSION,'title':'이번 풀이에 반영한 정보',
            'birth':'태어난 연·월·일·시간' if f.hour_known else '태어난 연·월·일 · 시간은 제외',
            'timing':f'{f.year_num}년과 현재 10년 운' if f.daeun_started else f'{f.year_num}년 · 첫 10년 운 이전',
            'answers':answer[0] if answer else [],
            'scope':'사주에서 읽은 특징과 직접 고른 답을 구분해 설명합니다. 실제 경험과 다르면 경험을 먼저 봅니다.'}
