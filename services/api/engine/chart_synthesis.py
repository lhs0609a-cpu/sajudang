"""Explain combinations of calculated facts, not a biography or a prediction.

No random wording or identity hash creates artificial uniqueness. The same
evidence yields the same reasoning. Rules return their inputs for inspection.
"""
from html import escape
from itertools import combinations

from .constants import CHUNG, HAP, HIDDEN, ELEMENT_OF_GAN, TEN_GOD_GROUP, ten_god

VERSION = 'chart-synthesis-v1'
GROUPS = ('비겁', '식상', '재성', '관성', '인성')
LABEL = {'비겁':'내 선택과 함께 나눌 몫', '식상':'표현과 결과물', '재성':'돈과 현실적인 조건',
         '관성':'책임과 지켜야 할 기준', '인성':'배움과 도움받을 기반'}
POSITION = {'년주':'태어난 해', '월주':'태어난 달', '일주':'태어난 날', '시주':'태어난 시간'}
AREA = {'년주':'주변의 기대', '월주':'사회에서 맡는 역할', '일주':'가까운 관계와 생활 방식', '시주':'앞으로 이어갈 계획'}
SEASON = dict(zip('寅卯辰巳午未申酉戌亥子丑',
                  ('봄이 시작되는 때','봄의 한가운데','봄에서 여름으로 넘어가는 때',
                   '여름이 시작되는 때','여름의 한가운데','여름에서 가을로 넘어가는 때',
                   '가을이 시작되는 때','가을의 한가운데','가을에서 겨울로 넘어가는 때',
                   '겨울이 시작되는 때','겨울의 한가운데','겨울에서 봄으로 넘어가는 때')))
PAIR = {
 frozenset(('비겁','식상')): ('내 뜻을 세우는 힘과 밖으로 보여주는 힘을 함께 읽소.', '혼자 정한 기준이 다른 사람도 이해할 수 있는 결과로 이어지는지'),
 frozenset(('비겁','재성')): ('스스로 정하고 싶은 마음과 돈·시간의 조건을 함께 읽소.', '원하는 선택을 하더라도 함께 쓸 돈과 시간을 남겨 두는지'),
 frozenset(('비겁','관성')): ('내 방식과 외부에서 요구하는 기준을 함께 읽소.', '내가 바꿀 수 있는 부분과 반드시 지켜야 할 약속을 나눴는지'),
 frozenset(('비겁','인성')): ('스스로 판단하는 힘과 배우며 도움받는 힘을 함께 읽소.', '내가 결정할 일까지 남의 확인을 기다리거나, 필요한 도움까지 거절하는지'),
 frozenset(('식상','재성')): ('만들고 표현하는 힘과 현실적인 보상을 함께 읽소.', '시간을 들인 결과가 실제로 필요한 사람에게 닿고 정당한 대가로 이어지는지'),
 frozenset(('식상','관성')): ('바꾸고 표현하려는 힘과 정해진 기준을 함께 읽소.', '제안의 내용은 타당한데 전달 방법이나 승인 절차 때문에 막히는지'),
 frozenset(('식상','인성')): ('충분히 이해하려는 힘과 직접 해보는 힘을 함께 읽소.', '더 배워야 하는 부분과 지금 아는 것으로 시도할 수 있는 부분을 나눴는지'),
 frozenset(('재성','관성')): ('현실적인 성과와 그에 따르는 책임을 함께 읽소.', '얻는 보상보다 맡아야 할 책임이 더 빨리 늘어나는지'),
 frozenset(('재성','인성')): ('당장 쓸 수 있는 결과와 배우는 데 필요한 여유를 함께 읽소.', '지금의 보상을 위해 앞으로 필요한 배움과 휴식을 계속 미루는지'),
 frozenset(('관성','인성')): ('외부의 요구와 그 요구를 감당할 준비를 함께 읽소.', '책임을 받기 전에 필요한 정보·권한·도움을 함께 받았는지'),
}
PRIORITY = {
 'support': ('받을 도움과 맡을 범위를 먼저 정하는 쪽', '해야 할 일을 늘리기 전에 함께할 사람·쓸 수 있는 시간·필요한 정보를 먼저 확인하시오.'),
 'deliver': ('준비한 것을 작게 실행해 보는 쪽', '준비를 하나 더 보태기보다 이미 아는 것으로 끝낼 수 있는 결과 하나를 정하시오.'),
 'bound': ('힘을 쓸 곳과 끝낼 기준을 정하는 쪽', '여러 일을 한꺼번에 맡기보다 이번에 끝낼 일과 다음으로 미룰 일을 나누시오.'),
 'trial': ('작게 해본 뒤 조건을 다시 맞추는 쪽', '큰 약속 전에 작은 시도를 하고, 들인 시간과 돌아온 결과를 비교하시오.'),
}

def relation(a, b):
    """Direction is from a to b in the five-role cycle, never an event forecast."""
    delta = (GROUPS.index(b)-GROUPS.index(a)) % 5
    return ('same','produces','controls','controlled_by','supported_by')[delta]

def contacts(pillars, branch):
    result = []
    for p in pillars:
        kind = 'clash' if CHUNG.get(branch)==p['ji'] else 'join' if HAP.get(branch)==p['ji'] else 'repeat' if branch==p['ji'] else None
        if kind:
            result.append({'position':p['label'], 'natal':p['ji'], 'incoming':branch, 'kind':kind})
    return result

def analyze(f):
    month = next(p for p in f.pillars if p['label']=='월주')
    day = next(p for p in f.pillars if p['label']=='일주')
    month_role = ten_god(month['gan'], f.day_gan)
    season_role = ten_god(HIDDEN[month['ji']][0][0], f.day_gan)
    private_role = ten_god(HIDDEN[day['ji']][0][0], f.day_gan)
    counts = {g:sum(v for k,v in f.ten_gods.items() if TEN_GOD_GROUP[k]==g) for g in GROUPS}
    # Stable presentation order; ties are disclosed, never treated as a ranking of people.
    ordered = sorted((g for g in GROUPS if counts[g]), key=lambda g:(-counts[g], -int(g==TEN_GOD_GROUP[season_role]), GROUPS.index(g)))
    roots = [p['label'] for p in f.pillars if any(ELEMENT_OF_GAN[g]==ELEMENT_OF_GAN[f.day_gan] for g,_ in HIDDEN[p['ji']])]
    pairs = []
    for left,right in combinations(f.pillars,2):
        kind = 'clash' if CHUNG.get(left['ji'])==right['ji'] else 'join' if HAP.get(left['ji'])==right['ji'] else None
        if kind:
            pairs.append({'left':left['label'],'right':right['label'],'kind':kind,'letters':[left['ji'],right['ji']]})
    annual = TEN_GOD_GROUP[f.year_ten_god]
    support = annual in ('비겁','인성')
    priority = 'support' if f.strength=='신약' else 'deliver' if f.strength=='신강' and support else 'bound' if not support else 'trial'
    current = f.daeun[f.daeun_now] if f.daeun_started and f.daeun else None
    period = TEN_GOD_GROUP[f.daeun_ten_god] if current else None
    return {'version':VERSION,'strength':f.strength,'season':SEASON[month['ji']],
            'season_support':f.deuk_ryeong,'day_support':f.deuk_ji,'root_positions':roots,
            'month_role':month_role,'season_role':season_role,'private_role':private_role,
            'groups':counts,'ordered_groups':ordered,'natal_contacts':pairs,
            'year_group':annual,'year_contacts':contacts(f.pillars,f.year_gz[-1]),
            'period_group':period,'period_contacts':contacts(f.pillars,current['ji']) if current else [],
            'period_year_relation':relation(period,annual) if period else None,
            'priority':priority,
            'rule_inputs':{'priority':['strength','year_ten_god'],
                           'pair':['ten_gods','month_branch'],
                           'positions':['day_gan','month_stem','day_branch'],
                           'timing':['daeun','year_gz','pillars']}}

def section(title, *paragraphs):
    return '<h3>'+escape(title)+'</h3>'+''.join('<p>'+escape(p)+'</p>' for p in paragraphs if p)

def support_text(f, s):
    season = ('태어난 계절은 나를 돕는 쪽으로 계산됐소.' if s['season_support'] else '태어난 계절 자체는 나를 돕는 쪽으로 계산되지 않았소.')
    footing = ('태어난 날의 아래 글자에는 나를 돕는 조건이 있소.' if s['day_support'] else '태어난 날의 아래 글자에서도 나를 돕는 조건은 잡히지 않았소.')
    total = {'신강':'다른 글자까지 합하면 나를 돕는 비중이 큰 편이오. 같은 요구가 와도 무엇을 실행할지에 무게를 두오.',
             '신약':'다른 글자까지 합하면 나를 돕는 비중이 작은 편이오. 같은 요구가 와도 무엇이 받쳐 주는지부터 살피오.',
             '중화':'다른 글자까지 합하면 한쪽으로 크게 기울지 않소. 계절 한 가지보다 실제로 늘어나는 일과 지원을 함께 보오.'}[f.strength]
    return [f'계절 기준으로는 {s["season"]}의 사주요. '+season, footing+' '+total]

def position_text(s):
    from .pungun_timing import EASY
    a,b = s['month_role'],s['private_role']
    return [f'사회에서 맡는 역할을 살피는 달의 윗글자는 “{EASY[a][0]}”으로 읽소.',
            f'가까운 관계와 생활을 살피는 날의 아랫글자는 “{EASY[b][0]}”으로 읽소.',
            ('두 자리의 주제가 같소. 다만 밖에서 잘 통하는 방식도 가까운 사람에게 같은 방식으로 필요한지 확인하시오.' if a==b else
             '두 자리의 주제가 다르오. 밖에서 맡는 역할과 가까운 관계에서 중요하게 보는 조건을 따로 확인하시오. 어느 쪽이 진짜 성격이라고 정하지 않소.')]

def pair_text(s):
    groups = s['ordered_groups']
    if len(groups)<2:
        return ['확인한 글자가 한 종류의 역할에 모여 있소. 다른 능력이 없다는 뜻은 아니오.',
                '익숙한 방식 하나로 서로 다른 문제를 모두 해결하려 하는지 확인하시오.']
    first,second = groups[:2]
    text, question = PAIR[frozenset((first,second))]
    leaders = [LABEL[g] for g in groups if s['groups'][g]==s['groups'][first]]
    tie = (' 가장 많은 묶음도 동률이어서 한 가지 성격으로 정하지 않소.' if len(leaders)>1 else '')
    return [text+tie, '실제 장면에서는 '+question+' 보시오.']

def contact_text(items, when):
    if not items:
        return [f'{when} 글자와 태어난 글자 사이에서 이번에 확인한 맞섬·결합·같은 글자의 반복은 없소. 변화가 없다는 뜻은 아니오.']
    lines = []
    for item in items:
        place=POSITION[item['position']]; area=AREA[item['position']]
        suffix={'clash':f'{area}에서 예전 방식과 새 요구를 함께 지킬 수 있는지 확인하시오.',
                'join':f'{area}에서 함께 맞출 조건을 살피되, 동의하지 않은 약속까지 생긴 것으로 보지 마시오.',
                'repeat':f'{area}의 같은 주제를 다시 살피는 표시요. 같은 사건이 반복된다는 뜻은 아니오.'}[item['kind']]
        fact={'clash':'서로 맞서는 짝','join':'서로 묶이는 짝','repeat':'같은 글자'}[item['kind']]
        lines.append(f'{when}의 아래 글자는 {place}의 아래 글자와 {fact}이오. '+suffix)
    return lines

def timing_text(f,s):
    from .pungun_timing import EASY
    annual=f'{f.year_num}년에는 “{EASY[f.year_ten_god][0]}”을 더해 읽소.'
    if not s['period_group']:
        return ['아직 첫 10년 운에 들어가기 전이므로, 태어난 사주와 올해만 비교하오.',annual]
    current=f.daeun[f.daeun_now]
    start=f.birth_year+int(current['start_age'])
    period=f'계산상 {start}년부터 이어지는 기간은 “{EASY[f.daeun_ten_god][1]}”요.'
    a,b=LABEL[s['period_group']],LABEL[s['year_group']]
    link={
        'same':f'긴 기간과 올해 모두 {a}에 초점이 맞춰져 있소. 새 목표를 더하기보다 이미 다루던 문제에서 아직 정하지 못한 조건을 확인하시오.',
        'produces':f'긴 기간의 {a}에서 올해의 {b}로 이어지는 관계요. 쌓아 둔 것을 다음 단계에 어떻게 사용할지 순서를 정하시오.',
        'supported_by':f'올해의 {b}가 긴 기간의 {a}를 받치는 관계요. 새로 얻는 도움이나 준비가 기존 목표에 실제로 필요한지 확인하시오.',
        'controls':f'긴 기간의 {a}가 올해의 {b}를 제한하는 관계로 읽소. 원래 지키던 기준 때문에 새로운 시도를 어디까지 허용할지 살피시오.',
        'controlled_by':f'올해의 {b}가 긴 기간의 {a}를 조정하는 관계로 읽소. 새 요구를 받아들이기 전에 기존 약속 중 무엇을 바꿔야 하는지 확인하시오.',
    }[s['period_year_relation']]
    return [period,annual,link]

def year_fit(f,s):
    """Read the incoming role against existing emphasis and support, not alone."""
    from .pungun_timing import EASY
    top=[k for k,v in f.ten_gods.items() if v==max(f.ten_gods.values())]
    body=section('태어난 사주에서 먼저 보인 주제',
        '올해 이야기와 비교할 출발점이오. 같은 수로 나온 주제는 함께 남겼소.' if len(top)>1 else
        '태어난 사주에서 가장 많이 잡힌 역할을 올해의 주제와 비교하오.')
    body+='<ul>'+''.join('<li>'+escape(EASY[k][0])+'</li>' for k in top)+'</ul>'
    match=(f'올해의 “{EASY[f.year_ten_god][0]}”은 원래 두드러진 주제와 같소. 익숙한 방식의 장점과 부담이 함께 커질 수 있는지 살피시오.' if f.year_ten_god in top else
           f'올해의 “{EASY[f.year_ten_god][0]}”은 원래 가장 두드러진 주제와 다르오. 잘해 오던 방식을 그대로 늘리기보다 새 요구에 맞춰 바꿀 부분을 확인하시오.')
    supported=s['year_group'] in ('비겁','인성')
    fit={
        ('신약',True):'태어난 사주에서 작게 잡힌 뒷받침과 같은 방향이 올해 더해지오. 더 맡을 기회로만 보기보다 실제로 쓸 수 있는 도움을 먼저 확보하시오.',
        ('신약',False):'태어난 사주에서 뒷받침은 작게 잡히는데, 올해는 밖으로 힘을 쓸 주제가 더해지오. 새 일을 받아들일 때 지원과 마감을 한 약속으로 맞추시오.',
        ('신강',True):'원래 나를 돕는 쪽이 큰데 올해도 같은 방향이 더해지오. 준비가 더 필요한지, 준비만 늘고 실행이 늦어지는지 구분하시오.',
        ('신강',False):'원래 나를 돕는 쪽이 크고 올해는 밖으로 힘을 쓸 주제가 더해지오. 쌓아 둔 것을 어디에 쓸지 좁히되 결과가 보장된다고 보지는 마시오.',
        ('중화',True):'전체 균형 위에 뒷받침하는 주제가 더해지오. 도움을 받았을 때 어떤 시도를 시작할 수 있는지 연결해 보시오.',
        ('중화',False):'전체 균형 위에 표현·돈·책임처럼 밖으로 힘을 쓸 주제가 더해지오. 새로 늘어나는 일만큼 줄이거나 나눌 일도 함께 정하시오.',
    }[(f.strength,supported)]
    return body+section('올해가 원래의 특징에 더하는 것',match,fit)

def core(f,lens_id,concern):
    from .personal_reading import EXAMPLES
    from .easy_specialists import INTRO
    s=analyze(f)
    title,action=PRIORITY[s['priority']]
    groups=s['ordered_groups']
    body=section('이 사주에서 먼저 읽은 결론',f'지금은 {title}에 무게를 두오. 글자 하나가 아니라 태어난 계절·전체 균형·올해 들어오는 주제를 함께 본 해석이오.')
    body+=section('같은 특징도 다르게 읽는 이유',*support_text(f,s))
    body+=section('두 가지 힘을 함께 보면',*pair_text(s))
    body+=section('밖에서 맡는 역할과 가까운 생활',*position_text(s))
    body+=section('물어본 일에 적용하면',EXAMPLES.get(concern,EXAMPLES['dir'])[groups[0]],action)
    if s['natal_contacts']:
        pair=next((p for p in s['natal_contacts'] if p['kind']=='clash'),s['natal_contacts'][0])
        body+=section('글자의 위치에서 더 확인할 것',
            f'{POSITION[pair["left"]]}와 {POSITION[pair["right"]]}의 아래 글자가 '+('서로 맞서는 짝이오.' if pair['kind']=='clash' else '서로 묶이는 짝이오.'),
            f'{AREA[pair["left"]]}와 {AREA[pair["right"]]}의 조건을 동시에 지킬 수 있는지 살피시오. 실제로 갈등이 있었다고 단정한 것은 아니오.')
    body+=section('이 상담자가 더 살피는 것',INTRO[lens_id])
    return '<div class="personal-reading chart-synthesis">'+body+'</div>'

def why(f,concern):
    from .personal_reading import TRAITS, EXAMPLES
    from .pungun_timing import EASY
    s=analyze(f)
    outside,inside=s['month_role'],s['private_role']
    helpful,_,check=TRAITS[outside]
    _,cost,private_check=TRAITS[inside]
    body=section('반복을 의심할 때 나누어 볼 두 조건',
        f'달의 윗글자에서 읽은 “{EASY[outside][0]}”과 날의 아랫글자에서 읽은 “{EASY[inside][0]}”을 한 장면에 놓고 비교하오.')
    body+=section('이 방식이 잘 통하는 조건',helpful+'는 도움이 될 수 있소. '+check)
    body+=section('같은 일을 하는데 부담이 생기는 조건',cost+'는 부담이 커질 수 있소. '+private_check)
    body+=section('먼저 바꿔 볼 조건 하나',
        ('전체 계산에서는 뒷받침을 먼저 살피는 쪽이므로, 의지를 더 내기 전에 도움과 맡을 양을 바꿔 보시오.' if s['priority']=='support' else
         '전체 계산에서는 준비를 실행으로 옮기는 쪽이므로, 더 확인받기 전에 작게 끝낼 범위를 정해 보시오.' if s['priority']=='deliver' else
         '올해 더해지는 요구까지 함께 보면, 방식 전체를 바꾸기보다 끝낼 범위와 다시 볼 때를 먼저 정하는 쪽이오.'),
        EXAMPLES.get(concern,EXAMPLES['dir'])[TEN_GOD_GROUP[outside]])
    body+=section('설명이 맞는지 확인하는 방법',
        '최근 일이 잘된 장면과 막힌 장면을 하나씩 고르시오. 맡은 일은 비슷한데 도움·시간·결정권이 달랐는지 비교하시오.',
        '조건이 달라도 결과가 같다면 이 설명만으로 원인을 정하지 마시오. 실제 반복의 원인은 사주 글자만으로 확인할 수 없소.')
    return '<div class="personal-reading chart-synthesis">'+body+'</div>'

def period(f,concern):
    from .personal_reading import EXAMPLES
    s=analyze(f)
    body=section('긴 흐름에서 실제로 조정할 것',
        '올해의 주제만 따라 결정을 바꾸기 전에, 길게 이어지는 흐름이 태어난 사주의 어느 자리에 닿는지 살피오.' if s['period_group'] else
        '아직 첫 10년 운에 들어가기 전이므로, 미래 구간을 현재의 일처럼 적용하지 않소.')
    if s['period_group']:
        body+=section('긴 흐름이 닿는 자리',*contact_text(s['period_contacts'],'현재 10년 운'))
    shared=sorted({x['position'] for x in s['period_contacts']} & {x['position'] for x in s['year_contacts']},key=lambda x:list(POSITION).index(x))
    body+=section('긴 흐름과 올해가 같은 자리에 닿는가',
        ('두 흐름 모두 '+ ' · '.join(POSITION[p] for p in shared)+'의 자리에 닿소. 한 흐름만 보고 결론을 내리기보다 같은 생활 영역에서 무엇을 유지하고 조정할지 함께 확인하시오.' if shared else
         '이번에 확인한 글자 관계에서는 두 흐름이 함께 닿는 자리가 없소. 긴 계획을 바꿀 문제와 올해만 조율할 문제를 나누어 보시오.'))
    if shared:
        body+=section('같은 자리라도 작용이 다를 수 있소',*contact_text([x for x in s['year_contacts'] if x['position'] in shared],'올해'))
    elif s['year_contacts']:
        body+=section('올해 따로 조율할 자리',*contact_text(s['year_contacts'],'올해'))
    body+=section('선택의 순서를 정하면',PRIORITY[s['priority']][1],EXAMPLES.get(concern,EXAMPLES['dir'])[s['year_group']])
    body+=section('시기의 뜻을 구분하시오','표시한 연도는 구간을 살피는 기준이며 정밀한 전환 날짜가 아니오. 계약·이직·관계의 결정은 실제 조건과 함께 판단하시오.')
    return '<div class="personal-reading chart-synthesis">'+body+'</div>'

def balance(f,concern):
    from .personal_reading import EXAMPLES
    s=analyze(f)
    body=section('무엇을 보완한다는 뜻일까',*support_text(f,s))
    root=(' · '.join(POSITION[p] for p in s['root_positions'])+'의 아래 글자에 나와 같은 성분이 들어 있소.' if s['root_positions'] else
          '확인한 아래 글자 속에서는 나와 같은 성분이 잡히지 않았소. 혼자 해낼 능력이 없다는 뜻은 아니오.')
    body+=section('숫자와 실제 도움을 구분하시오',root,
        '사주에서 보완할 성분을 실제 물건이나 색깔 하나로 바꾸지는 않소. 생활에서는 시간·정보·권한·사람 중 무엇을 더하면 선택이 달라지는지 보오.')
    body+=section('이번 고민에서 보완할 조건',PRIORITY[s['priority']][1],EXAMPLES.get(concern,EXAMPLES['dir'])[s['year_group']])
    return '<div class="personal-reading chart-synthesis">'+body+'</div>'
