"""Easy, character-spoken readings; calculated evidence stays behind a disclosure.

Canonical prose is authored in 하오체, then passed through the existing voice
and address engine. It never invents memories, motives, diagnoses or events.
"""
from html import escape
from . import guard, lens, voice


# One household image per story. The image explains the selected relationship.
# title, scene/question, meaning, cost, recognition, small action
STORIES = {
    'output_value': ('공들인 만큼 내 몫도 남겨야 하오', '밥상을 정성껏 차리고도 정작 내 밥그릇은 비워 둔 적이 있소?', '일을 잘해 주는 것과 내 몫을 챙기는 것은 함께 배워야 하오.', '더 해준 일이 모두 덤이 되면, 바쁜데도 손에 남는 것은 적소.', '내 몫을 말한다고 정성이 작아지는 것은 아니오.', '다음 일을 맡기 전에 어디까지 해주고 얼마를 받을지 먼저 적으시오.'),
    'autonomy_standards': ('맡은 일만큼 정할 수 있어야 하오', '부엌은 맡겼다면서 숟가락 놓을 자리까지 정해 주면 답답하지 않소?', '함께 지킬 약속과 내가 정할 방법을 나눠야 하오.', '하나하나 허락을 받다 보면, 일보다 허락을 기다리는 데 힘이 드오.', '내 방식이 필요하다는 말은 함께하기 싫다는 뜻이 아니오.', '다음 일에서는 내가 정해도 되는 것 하나를 먼저 확인하시오.'),
    'pressure_learning': ('버틴 만큼 내게 남는 것도 있어야 하오', '무거운 짐을 날랐는데 다음 날에도 똑같이 혼자 들어야 한다면 어떻겠소?', '애쓴 시간이 쌓이려면, 다음에는 덜 힘들게 할 방법도 남아야 하오.', '급한 일만 끝내다 보면 잘하는 사람에게 급한 일이 더 몰리오.', '도움이 필요하다는 말까지 혼자 삼킬 필요는 없소.', '반복해서 힘든 일 하나를 고르고, 누가 무엇을 도와야 할지 말하시오.'),
    'shared_reward': ('가까운 사이일수록 몫을 먼저 정하시오', '함께 차린 밥상에서 누가 얼마나 먹을지 나중에 다투면 밥맛도 사라지오.', '친한 마음이 있어도 각자가 들인 시간은 다르게 기억할 수 있소.', '처음에 미룬 돈 이야기가 나중에는 마음의 빚이 되오.', '분명히 정해 두는 것도 관계를 아끼는 방법이오.', '함께할 일 하나에서 맡을 일과 나눌 몫을 먼저 적으시오.'),
    'expression_rules': ('옳은 말도 들어갈 문이 필요하오', '좋은 물건도 닫힌 문 앞에 놓아두면 안으로 들어가지 못하오.', '바꿀 점을 말하기 전에, 누가 듣고 누가 정하는지 살펴야 하오.', '내용은 맞는데 말한 자리와 순서 때문에 대화가 막힐 수 있소.', '의견을 버릴 필요는 없소. 전할 자리를 고르면 되오.', '다음 의견은 여러 사람 앞에서 할 말인지, 둘이 있을 때 할 말인지 먼저 정하시오.'),
    'learning_output': ('다 알아야 첫발을 뗄 수 있는 것은 아니오', '길을 나서기 전에 지도를 다 외우려 하면 해가 먼저 지오.', '더 배울 것이 남아 있어도 지금 아는 것으로 해볼 일은 있소.', '준비할 것이 늘 때마다 시작할 날도 멀어질 수 있소.', '작게 해본 일이 다음에 배울 것을 알려주기도 하오.', '새 자료를 찾기 전에 지금 아는 것으로 한 장만 끝내 보시오.'),
    'resources_support': ('다음 날의 힘까지 오늘 쓰지는 마시오', '내일 먹을 쌀까지 오늘 밥솥에 넣으면 오늘은 넉넉해도 내일이 막막하오.', '당장 얻을 것과 다시 시작할 힘을 함께 남겨야 하오.', '일을 늘릴 때 쉬고 배우는 시간부터 줄이면 다음 일이 더 버거워지오.', '남겨 둔 여유도 일을 오래 이어 가게 하는 몫이오.', '새 일을 하나 넣을 때 무엇을 덜 할지도 함께 정하시오.'),
    'reward_responsibility': ('좋은 기회에 딸린 짐도 보시오', '예쁜 보따리를 받았는데 매일 들고 다녀야 한다면 무게도 봐야 하지 않겠소?', '새로 얻는 것에는 계속 지켜야 할 약속이 붙을 수 있소.', '처음 받은 것보다 나중에 해야 할 일이 커지면 마음이 무거워지오.', '조건을 묻는다고 좋은 기회를 걷어차는 것은 아니오.', '새 제안에서 받는 것과 매번 해야 할 일을 나란히 적으시오.'),
    'independent_support': ('도움을 받아도 내 길은 내가 정할 수 있소', '무거운 가방을 잠깐 맡긴다고 갈 곳까지 남이 정하는 것은 아니오.', '도움받을 일과 내가 결정할 일을 나누면 되오.', '설명하기 번거롭다고 모두 안고 가면 짐이 줄지 않소.', '혼자 해낸 것만 내 힘으로 셀 필요는 없소.', '다음에는 결정까지 맡기지 말고, 작업 하나만 구체적으로 부탁하시오.'),
    'initiative_expression': ('먼저 가기 전에 함께 갈 사람을 보시오', '내 걸음이 빠르다고 옆 사람의 신발까지 빨라지지는 않소.', '내가 정한 방향을 상대도 알고 있는지 먼저 살펴야 하오.', '좋은 뜻으로 앞장서도 설명이 빠지면 상대는 끌려가는 듯할 수 있소.', '잠깐 기다려 주는 것도 함께 가는 힘이오.', '다음 제안에서는 왜 가려는지 말한 뒤 상대의 생각부터 들으시오.'),
}

# Direction changes the image and practical takeaway, not merely a number.
VARIANTS = {
    ('learning_output', '식상'): ('잘 고치는 눈에도 쉬는 때가 필요하오', '다 쓴 편지를 보내기 전에 자꾸 다시 고쳐 본 적이 있소?', '이미 시작한 일에서도 더 나은 답을 찾는 쪽으로 읽히오.', '고치고 또 고치다 보면, 편지는 못 보내고 밤만 깊어지오.', '편지에 고칠 곳이 남아 있어도 그 안에 담은 정성까지 지울 필요는 없소.', '오늘 끝낼 일 하나는 고칠 점을 세 개까지만 정하고 마치시오.'),
    ('initiative_expression', '식상'): ('마음을 전할 자리도 남겨 두시오', '물을 가득 따른 잔에는 상대가 물을 더 보탤 수 없소.', '생각을 자세히 전하려는 힘이 상대가 답할 자리까지 채우는지 보오.', '설명을 더할수록 뜻은 또렷해져도 상대의 말은 줄어들 수 있소.', '덜 말해도 진심이 줄어드는 것은 아니오.', '다음에는 이유 하나만 말하고, 상대가 끝까지 답할 동안 기다리시오.'),
    ('output_value', '재성'): ('받은 일만큼 끝낼 시간도 있소?', '밥솥은 하나인데 밥 먹을 사람만 계속 부르면 곤란하오.', '일을 잡는 속도와 끝내는 속도를 함께 봐야 하오.', '좋은 제안을 다 받으면 먼저 한 약속을 지키기 어려워지오.', '한 번 거절하는 것이 이미 한 약속을 지키는 길일 수 있소.', '새 일을 받기 전에 지금 남은 일부터 시간으로 적으시오.'),
    ('autonomy_standards', '관성'): ('내 생각도 결정에 넣으시오', '운전대를 잡고도 길을 꺾을 때마다 허락을 기다리면 앞으로 가기 어렵소.', '맡은 책임에 비해 스스로 정할 일이 적은지 보오.', '남의 답만 기다리면 내 판단을 꺼낼 때가 늦어지오.', '틀릴 수 있어도 내 의견을 말할 자리는 있어야 하오.', '다음에 허락을 구할 때는 내가 고른 답과 이유도 함께 말하시오.'),
    ('pressure_learning', '인성'): ('배운 것을 손으로 써볼 때요', '요리책을 다 읽어도 불을 켜지 않으면 밥은 익지 않소.', '알게 된 것을 실제로 맡아 해보는 자리가 필요하오.', '설명은 늘어도 해본 일이 없으면 자신감이 따라오기 어렵소.', '처음 만든 것이 서툴러도 배운 것이 사라지는 것은 아니오.', '이번에 배운 것 하나를 오늘 할 수 있는 일로 바꾸시오.'),
    ('shared_reward', '재성'): ('부탁에 담긴 기대도 말하시오', '같이 밥을 먹자고 불러 놓고 설거지까지 기대했다면 미리 말해야 하오.', '함께하는 마음과 상대에게 바라는 일을 나눠 보오.', '말하지 않은 기대까지 상대가 알아주기는 어렵소.', '원하는 것을 말하는 편이 혼자 실망하는 것보다 서로에게 친절하오.', '다음 부탁에서는 어디까지 바라는지 먼저 말하시오.'),
    ('expression_rules', '관성'): ('틀리지 않으려다 말까지 삼키지는 마시오', '문을 두드려도 되는지 오래 고민하면 안에 있는 사람은 온 줄도 모르오.', '맞는 순서를 찾느라 필요한 의견을 늦추는지 보오.', '말하지 않은 불편은 고쳐지지 않고 남기 쉽소.', '다 맞는 답을 준비한 뒤에만 말할 수 있는 것은 아니오.', '다음 대화에서 바꾸고 싶은 점 하나만 짧게 꺼내 보시오.'),
    ('resources_support', '인성'): ('준비물을 늘리기 전에 하나를 써보시오', '연필을 더 산다고 빈 공책이 채워지지는 않소.', '배울 것과 도구를 모으는 일이 실제로 쓰는 일보다 앞서는지 보오.', '준비는 늘었는데 끝낸 것이 없으면 다시 부족한 마음이 들 수 있소.', '지금 가진 것으로 해낸 작은 일도 내 실력이오.', '새 것을 사기 전에 이미 가진 것으로 한 가지를 끝내시오.'),
    ('reward_responsibility', '관성'): ('짐을 더 받으면 내 몫도 다시 정하시오', '가방에 짐을 더 넣으면서 가볍게 들길 바랄 수는 없소.', '일을 잘해냈다는 이유로 추가 일을 같은 조건에 맡는지 보오.', '책임만 늘고 시간과 도움이 그대로면 잘하는 일이 버거워지오.', '조건을 다시 묻는 것은 책임을 피하는 일이 아니오.', '추가 일을 받을 때 필요한 시간이나 도움도 함께 말하시오.'),
    ('independent_support', '인성'): ('길을 물어도 걸을 곳은 내가 고르시오', '길을 아는 사람이 많아도 발은 한 번에 한쪽으로만 움직이오.', '조언을 듣고도 누구의 기준으로 고를지 정하지 못하는지 보오.', '답을 더 들을수록 내 선택이 더 어려워질 수 있소.', '남의 조언을 다 따르지 않아도 고마운 마음은 남길 수 있소.', '더 묻기 전에 내가 꼭 지킬 조건 두 가지를 적으시오.'),
}

ENTRANCES = {
    'pungun': '그대의 글자에서 먼저 눈에 들어오는 대목을 풀어 보겠소.',
    'baegun': '서두르지 말고 한 대목씩 보오. 오래 쓸 힘도 남겨야 하오.',
    'cheongam': '복잡한 이름은 잠시 내려놓고, 눈에 보이는 장면으로 말하겠소.',
    'sigye': '먼저 순서부터 보오. 언제 시작하고 어디서 멈추는지가 중요하오.',
    'eunbyeol': '이렇게 읽히지만 실제 경험과 다른 곳이 있는지 함께 보오.',
    'jeokhyeol': '돌려 말하지 않겠소. 마음에 걸리는 대목부터 보오.',
    'monghwa': '장면 하나를 떠올려 보오. 실제로 닮은 곳이 있는지 보오.',
    'seoyeok': '조금 떨어져 보오. 가까이 있을 때 놓친 길이 보일 수 있소.',
    'paeseon': '한 번에 다 고를 필요는 없소. 손에 남길 것부터 보오.',
    'myeonsang': '겉으로 드러난 행동부터 보오. 속마음을 미리 정하지는 않겠소.',
    'wolha': '마음이 오가는 자리를 보오. 한 사람의 뜻만으로 채울 수는 없소.',
    'hongmae': '듣기 좋은 말만 하지는 않겠소. 애쓴 마음도 빠뜨리지 않겠소.',
    'yeondam': '서둘러 답을 내리지 않겠소. 지금 할 수 있는 일부터 보오.',
    'hwagyeong': '누가 더 잘못했는지보다 실제로 어떤 말이 오갔는지 보오.',
    'haengsu': '공들인 만큼 무엇이 남는지 보오. 내 몫도 셈에 넣으시오.',
    'hunjang': '잘하는 것을 알아야 고칠 것도 고르오. 하나씩 짚겠소.',
    'yakcho': '오늘 쓴 힘부터 보오. 애쓴 만큼 쉬는 자리도 있어야 하오.',
    'ilgwan': '오늘 할 일 하나로 좁혀 보오. 모든 날을 한꺼번에 살 수는 없소.',
    'nopa': '다 떠안을 생각부터 내려놓으시오. 할 수 있는 데까지 보는 것이오.',
    'dongja': '어려운 말은 빼겠소. 작은 일 하나부터 같이 보오.',
}


def story(claim):
    values = claim.get('composition', '').split(' · ')
    counts = {part.split()[0]: int(part.split()[1]) for part in values if len(part.split()) == 2}
    lead = max(counts, key=counts.get) if counts and len(set(counts.values())) > 1 else None
    return VARIANTS.get((claim['id'], lead), STORIES[claim['id']])


def say(text, lid):
    view = lens.view(lid)
    heading = bool(text) and text[-1] not in '.?!'
    raw = escape(text + ('.' if heading else ''))
    spoken = voice.speak(voice.address(raw, lens.you_of(lid)), view.get('voice'))
    # In these authored invitations, 보오 is an invitation to look together.
    # The generic converter's declarative 보네요 obscures that intent.
    if view.get('voice') == voice.HAEYO:
        spoken = spoken.replace('보네요.', '봐요.')
    return guard.enforce(spoken[:-1] if heading and spoken.endswith('.') else spoken)


def para(text, lid, css=''):
    return '<p' + (' class="' + css + '"' if css else '') + '>' + say(text, lid) + '</p>'


def evidence(html):
    return '<details class="reading-evidence"><summary>왜 이렇게 읽었나요? · 사주 근거</summary>' + html + '</details>'


def question(claim, lid):
    scene = story(claim)[1]
    if not scene.endswith('?'):
        scene += ' 그대에게도 닮은 장면이 있소?'
    return say(scene, lid)


def claim_body(claim, plan, lid, first=False):
    title, scene, meaning, cost, recognition, action = story(claim)
    from . import reading_context
    contextual = reading_context.selected(plan)
    if contextual and contextual[0]['id'] == claim['id']:
        _, choice, reply = contextual
        scene, meaning = '직접 들려준 사정을 먼저 놓고 읽겠소.', reply[1]
        cost = ('이유를 듣기 전에 붙인 성향 설명은 여기서 멈추겠소.' if choice == 'required' else
                '같은 행동도 무엇을 지키려 했는지에 따라 바꿀 방법이 달라지오.')
        recognition, action = reply[3], reply[2]
    html = para(ENTRANCES.get(lid, ENTRANCES['pungun']), lid) if first else ''
    html += para(scene, lid, 'reading-thesis') + para(meaning, lid) + para(cost, lid)
    html += para(recognition, lid, 'reading-recognition')
    if plan['answers'].get('stage') == 'tried':
        action = '이미 해본 일이라면 같은 숙제를 더 얹지는 않겠소. 해봤는데도 달라지지 않은 조건 하나를 먼저 보오.'
    elif plan['answers'].get('stage') == 'constrained':
        action = '당장 크게 바꾸기 어렵다면 작은 한 번만 해보시오. ' + action
    html += para(action, lid, 'reading-action')
    if claim['answer'] == 'yes':
        html += para('비슷한 경험이 있다고 답한 대목이오. 어디에서 그랬는지 떠올려 보오.', lid)
    elif claim['answer'] == 'mixed':
        html += para('상황에 따라 다르다고 답했소. 모든 자리에 같은 이야기를 붙이지는 않겠소.', lid)
    facts = ''.join('<p>' + escape(plan['facts'][ref]['label'] + ' — ' + plan['facts'][ref]['text']) + '</p>' for ref in claim['evidence_ids'])
    facts += '<p>' + escape(claim['exception']) + '</p>'
    return html + evidence(facts)


DOMAIN = {
    'work': ('일할 때', '일을 다 마쳤는데도 자꾸 다시 손보는 날이 있소?', '끝낼 선을 정하지 않으면 잘하는 일이 계속 내 시간을 가져가오.', '오늘 할 일 하나에서 꼭 고칠 것과 다음으로 넘길 것을 나누시오.'),
    'money': ('돈을 벌고 쓸 때', '정성껏 만든 물건을 건네고도 값을 말하기 머뭇거린 적이 있소?', '잘해 주는 마음만큼 내 시간의 값도 챙겨야 하오.', '다음 일에서는 값과 어디까지 해줄지를 시작 전에 정하시오.'),
    'love': ('마음을 주고받을 때', '상대는 옆에 앉아 주길 바랐는데 나는 해결할 방법부터 찾은 적이 있소?', '도와주고 싶은 마음이 있어도 상대가 원하는 도움은 다를 수 있소.', '다음에는 들어주길 바라는지, 함께 답을 찾길 바라는지 먼저 물으시오.'),
    'people': ('사람들 사이에서', '남의 옷에 묻은 것을 발견했을 때, 모두 들으라고 말할 필요는 없소.', '고칠 점을 알려주는 말도 둘이 있을 때 건네면 덜 아플 수 있소.', '다음 조언은 상대가 듣고 싶어 하는지 먼저 물으시오.'),
    'dir': ('어느 길로 갈지 고민할 때', '갈림길에서 오래 서 있어도 두 길의 끝이 모두 보이지는 않소.', '되돌아올 수 있는 만큼 걸어 보면 머릿속에서만 고를 때보다 알게 되는 것이 있소.', '고민하는 두 가지를 작은 일 하나씩 해보고, 해본 뒤의 마음을 적으시오.'),
    'health': ('하루를 마치고 쉴 때', '몸은 집에 왔는데 마음은 아직 일하던 자리에 남아 있소?', '오늘 못 끝낸 일을 계속 생각하면 쉬는 시간에도 일을 놓기 어렵소.', '내일 할 일을 세 줄만 적고, 오늘은 다시 열어보지 않을 일을 정하시오.'),
}


GROUP_IMAGES = {
    '비겁': ('가방을 혼자 다 들 필요는 없소.', '내가 정할 것과 나눠 맡길 것을 하나씩 고르시오.'),
    '식상': ('보내지 못한 편지를 계속 고치는지 보오.', '한 번 마친 뒤에는 상대의 답을 받을 틈도 남기시오.'),
    '재성': ('바구니에 더 담기 전에 들고 갈 무게부터 보오.', '새로 얻을 것과 계속 들여야 할 시간과 돈을 함께 적으시오.'),
    '관성': ('약속이 하나 늘면 하루의 빈칸은 하나 줄어드오.', '새 일을 맡을 때는 지금 하는 일 중 무엇을 덜 할지도 정하시오.'),
    '인성': ('지도를 더 보기 전에 지금 선 자리부터 살피시오.', '더 알아볼 것 하나와 지금 해볼 것 하나를 나누시오.'),
}


def domain_body(plan, concern, lid):
    title, scene, meaning, action = DOMAIN[concern]
    if plan['rejected']:
        return para('앞에서 맞지 않다고 한 이야기를 여기서 다시 꺼내지는 않겠소. 이 자리에서 실제로 겪은 일을 듣고 이어가겠소.', lid)
    leaders = plan['personal']['leaders']
    if leaders == ['식상']:
        return para(scene, lid, 'reading-thesis') + para(meaning, lid) + para(action, lid, 'reading-action')
    # Other compositions keep their own selected relationship and image.
    # Caller supplies the actual domain plan, never fabricates a supporting pair.
    chosen = plan['selected']
    if chosen:
        row = story(chosen[0])
        return para(row[1], lid, 'reading-thesis') + para(row[2], lid) + para(row[5], lid, 'reading-action')
    return ''.join(para(GROUP_IMAGES[g][0], lid) + para(GROUP_IMAGES[g][1], lid, 'reading-action') for g in leaders)


def project(result, plan, f, lid='pungun'):
    from .interpretation import build_plan, GROUPS
    from . import reading_storyline, reading_context
    spine = reading_storyline.build(plan, f)
    shown = plan['selected'][:len(result['summary'])]
    for index, (row, claim) in enumerate(zip(result['summary'], shown)):
        row['title'] = say(story(claim)[0], lid)
        if spine['context'] and spine['context'][0]['id'] == claim['id']:
            row['title'] = say('그때의 사정을 듣고 다시 읽겠소', lid)
        row['html'] = claim_body(claim, plan, lid, first=index == 0)
    result['headline'] = result['summary'][0]['title'] if shown else say('그대의 이야기를 조금 더 듣고 싶소.', lid)
    result['boundary'] = '사주로 읽은 이야기입니다. 실제 경험과 다른 대목은 아래 답변에서 알려주세요.'
    result['narrator'] = {'id': lid, 'name': lens.public(lid)['name']}
    result['journey'] = {'version': 1, 'source': spine['source'], 'mode': spine['mode'],
        'steps': ['나에게 익숙한 모습', '잘하는 힘이 버거워질 때', '실제 경험과 다른 점', '오늘 남길 한 가지'],
        'context_label': spine['context'][2][0] if spine['context'] else None}
    result['empty_reason'] = say('이 자리에서는 하나로 묶어 말할 근거가 모자라오. 결론을 억지로 붙이지 않겠소.', lid) if not shown else None
    from . import reading_practice
    practice = reading_practice.build(plan, shown)
    result['practice'] = {key: say(value, lid) if key != 'source' else value for key, value in practice.items()}
    for section in result['sections']:
        old, key = section['html'], section['id']
        if key == 'portrait':
            section['title'] = '그대의 힘이 쓰이는 곳'
            body = ''.join(para(line, lid) for line in reading_storyline.opening_lines(spine))
            # Boundary conditions affect the reading; keep them visible.
            if not f.hour_known:
                body += para('태어난 시각을 몰라 세 기둥만 보았소. 시각을 알면 이야기가 달라질 수 있소.', lid)
            elif f.correction.get('after'):
                hour, minute = map(int, f.correction['after'].split(':'))
                phase = (hour * 60 + minute - 60) % 120
                if min(phase, 120-phase) <= 5:
                    body += para('태어난 시각이 사주 글자가 바뀌는 때와 아주 가깝소. 태어난 도시와 시각을 다시 확인해야 하오.', lid)
            section['html'] = body + evidence(old)
        elif key == 'focus' or key.startswith('domain_'):
            concern = plan['concern'] if key == 'focus' else key[7:]
            dp = plan if key == 'focus' else build_plan(f, concern)
            dp['rejected'] = plan['rejected']
            section['title'] = DOMAIN[concern][0]
            group = {'work':'관성','money':'재성','love':'인성','people':'비겁','dir':'식상','health':'인성'}[concern]
            fact = plan['facts']['group:' + group]
            body = ''.join(para(line, lid, 'reading-action' if line.startswith('이 일이') else '')
                           for line in reading_storyline.domain_lines(spine, concern))
            if spine['context'] and key == 'focus':
                body = para(spine['context'][2][1], lid, 'reading-origin') + para(spine['context'][2][2], lid, 'reading-action')
                body += para('다른 자리에서도 같은 이유였는지는 아직 묻지 않았소. 아래 이야기는 그 자리의 경험과 따로 맞춰 보시오.', lid)
            section['html'] = body + evidence('<p>' + escape(fact['label'] + ' — ' + fact['text']) + '</p>')
        elif key == 'decision':
            section['title'] = '지금 바꿔 볼 한 가지'
            body = para(story(shown[0])[5] if shown else '최근에 마음이 걸린 일 하나부터 떠올려 보시오.', lid, 'reading-action')
            if spine['context']:
                body = para(spine['context'][2][2], lid, 'reading-action')
            if plan['answers'].get('stage') == 'tried':
                body = para('이미 바꿔 보았다고 답했소. 같은 일을 더 하라고 하지는 않겠소. 달라지지 않은 조건부터 함께 보오.', lid)
            elif plan['answers'].get('stage') == 'constrained':
                body += para('당장 바꾸기 어렵다고 답했소. 오늘 가능한 작은 일까지만 해보시오.', lid)
            # Keep the explicit chosen real-world constraint visible and distinct.
            if plan['answers'].get('driver'):
                from .interpretation import content
                driver = next(d for d in content()['domains'][plan['concern']]['drivers'] if d['id'] == plan['answers']['driver'])
                body += '<p class="reading-origin">직접 고른 고민 · ' + escape(driver['label']) + '</p>'
                body += para(driver['action'].replace('보세요.', '보시오.'), lid, 'reading-action')
            section['html'] = body + evidence(old)
        elif key == 'timing':
            section['title'] = '지나온 때와 앞으로의 때'
            from .constants import TEN_GOD_GROUP, ten_god
            body = para('시간이 흐르면 맡는 일과 주변의 약속도 달라지오. 사주에서는 그 흐름을 나눠 보오. 무슨 일이 생긴다고 정해 놓은 달력은 아니오.', lid)
            if f.daeun_started and f.daeun and int(f.daeun[f.daeun_now]['start_age']) <= f.age < int(f.daeun[f.daeun_now]['start_age']) + 10:
                d = f.daeun[f.daeun_now]
                group = TEN_GOD_GROUP[ten_god(d['gan'], f.day_gan)]
                body += para(f"지금 계산에 쓰는 큰 구간은 연 나이 {d['start_age']}세부터 열 해요.", lid)
                body += para(GROUP_IMAGES[group][0], lid) + para(GROUP_IMAGES[group][1], lid)
            section['html'] = body + evidence(old)
        elif key == 'method':
            section['title'] = '사주 근거와 입력 확인'
            section['html'] = para('태어난 때를 어떻게 계산했는지 이 안에 적어 두었소. 어려운 이름을 외울 필요는 없소.', lid) + evidence(old)
        elif key == 'revised':
            section['html'] = para('맞지 않는다고 답한 이야기는 이번 풀이에서 뺐소. 그대의 경험을 먼저 듣겠소.', lid)
        elif key == 'review':
            section['title'] = '끝으로 건네는 말'
            section['html'] = para(practice['remember'], lid, 'reading-recognition')
            section['html'] += para('오늘 한 번 달라진 선택이 있었는지 보시오. 잘되지 않았다면 그 조건부터 다시 살피면 되오.', lid)
    questions = result['consultation']['questions']
    for q in questions:
        claim = next((c for c in plan['selected'] if q['id'].startswith('claim:') and q['id'].endswith(':' + c['id'])), None)
        if claim:
            q['question'] = question(claim, lid)
        elif q['id'].startswith('reason:'):
            q['question'] = say('비슷한 경험이 있었다고 했소. 그때 그렇게 한 이유는 어느 쪽에 가까웠소?', lid)
    return guard.enforce_deep(result)
