"""Twenty editorial perspectives × six concerns, grounded in existing feature axes.

This layer separates computed observations from prompts for self-reflection.
It never turns a birth configuration into proof of a person's behaviour.
"""
from . import guard, lens_cuts, lens, voice
from .editorial_questions import question as concern_question


def _plan_voice(text, tone):
    """Normalize the reviewed modern plan endings before the existing voice pass.

    Integrated prose stays in plain Korean. Only character dialogue uses the
    bank's canonical 하오체 and the established per-character transformation.
    """
    text = text.replace('보세요.', '보시오.').replace('살펴봅니다.', '살펴보오.')
    if text.endswith('나요?'):
        text = text[:-3] + '소?'
    return voice.speak(text, tone)

VERSION=2
# axis, perspective, falsifiable question, small action
ROLES={
 'pungun':('deuk','버티는 힘과 빌려 쓰는 힘','내가 버텨낸 일에 도움을 준 사람이나 조건을 빼놓고 있지는 않소?','혼자 해낸 몫과 도움받은 몫을 나눠 적으시오.'),
 'baegun':('johu','속도를 높이기 전에 필요한 여유','급한 마음 때문에 원래 지키려던 기준까지 바꾼 적은 없소?','서둘러 답할 일 하나에 확인할 기준을 먼저 적으시오.'),
 'cheongam':('seupjo','생각을 오래 붙잡는 방식','신중하게 고르는 것과 결정을 피하는 것을 구분할 수 있겠소?','더 알아야 할 사실 하나와 이미 아는 사실 하나를 구분하시오.'),
 'sigye':('daeun_phase','지금의 단계와 다음 단계','일이 바뀌었는데 예전 방식으로만 힘을 쓰고 있지는 않소?','계속할 일 하나와 방식을 바꿀 일 하나를 나누시오.'),
 'eunbyeol':('gap_band','많이 쓰는 힘과 덜 쓰는 힘','익숙한 방법이 통하지 않을 때도 같은 방법을 더 세게 쓰지는 않소?','늘 쓰던 방법 외에 작게 시험할 방법 하나를 정하시오.'),
 'jeokhyeol':('score_band','맡은 몫과 감당할 수 있는 몫','괜찮다고 한 뒤에야 부담을 느낀 일이 있소?','다음 수락 전에 필요한 시간과 가능한 범위를 적으시오.'),
 'monghwa':('sinsal_mark','관심이 움직이는 자리','새로운 자극을 찾는 것과 지금의 답답함을 피하는 것을 구분해 보았소?','새로 원하는 것과 지금 피하고 싶은 것을 각각 적으시오.'),
 'seoyeok':('flow','내 방식과 다른 기준','남이 좋다고 한 선택을 내 기준처럼 쓰고 있지는 않소?','남의 추천에서 내 상황에 맞는 이유만 남기시오.'),
 'paeseon':('yongsin','많이 가진 것보다 필요한 조건','더하는 일에 익숙해 정작 줄일 일을 놓치지는 않소?','추가할 계획 하나를 고르기 전에 그만둘 일 하나를 찾으시오.'),
 'myeonsang':('palace','가까운 자리에서 달라지는 태도','밖에서 보이는 모습과 편한 사람 앞의 모습은 어디서 달라지오?','두 자리에서 달랐던 반응을 사실만 적어 비교하시오.'),
 'wolha':('ilji_state','가까워지고 싶은 마음과 지키고 싶은 거리','원하는 것을 말하지 않은 채 알아주기를 기다린 적은 없소?','상대가 알아주길 바랐던 것을 요청 한 문장으로 바꾸시오.'),
 'hongmae':('gwan_jae','기대받는 몫과 받고 싶은 대가','좋은 관계를 지키려고 조건을 흐릿하게 둔 적은 없소?','지킬 약속과 다시 합의할 조건을 하나씩 적으시오.'),
 'yeondam':('ilji_state','내가 선택할 수 있는 연락과 경계','상대의 마음을 추측하느라 내 기준을 미루고 있지는 않소?','상대의 답과 무관하게 지킬 연락 기준을 정하시오.'),
 'hwagyeong':('top_ten_god','드러내는 말과 실제로 하는 행동','설명은 길어졌는데 필요한 행동은 미뤄진 일이 있소?','설명 한 문장을 덜고 끝낼 수 있는 행동 하나를 정하시오.'),
 'haengsu':('flow','들어오는 것과 남는 것','수고한 크기만큼 남는 것도 확인하고 있소?','시간을 쓴 뒤 실제로 남은 결과 하나를 기록하시오.'),
 'hunjang':('top_ten_god','익힌 것과 직접 해본 것','준비가 부족해서 멈췄소, 아니면 평가받는 순간을 미루고 있소?','이미 아는 것으로 끝낼 수 있는 작은 결과물을 정하시오.'),
 'yakcho':('zero_band','활동과 쉬는 경계','쉬는 시간에도 끝내지 못한 일을 계속 세고 있지는 않소?','오늘 마칠 일과 내일로 미룰 일을 하나씩 구분하시오.'),
 'ilgwan':('season','주변 조건에 맞추는 방식','지금의 조건이 달라졌는데 계획은 그대로 두고 있지는 않소?','바뀐 조건 하나와 그 때문에 고칠 계획 하나를 적으시오.'),
 'nopa':('age_band','익숙해서 반복하는 선택','오래 해왔다는 이유만으로 계속하는 일이 있소?','지금도 필요한 이유와 습관으로 남은 이유를 구분하시오.'),
 'dongja':('hour_known','모르는 것을 비워 두는 용기','답을 더 얻으려다 이미 지친 마음을 놓치지는 않았소?','오늘은 해석을 더 사지 말고 기억할 문장 하나만 남기시오.'),
}
CONCERNS={
 'money':('돈','최근의 지출이나 돈에 관한 약속','금액·용도·선택 이유'),
 'work':('일','최근 맡거나 미룬 업무','담당 범위·시간·완료 기준'),
 'love':('사랑','상대와 말이 어긋났던 대화','실제로 들은 말·내 해석·원하는 요청'),
 'people':('관계','부탁을 받거나 경계를 정했던 장면','부탁 내용·가능한 범위·내 일정'),
 'dir':('방향','아직 고르지 못한 두 선택','지킬 것·포기할 것·되돌릴 수 있는 범위'),
 'health':('생활 리듬','하루를 마치는 시간의 습관','마칠 일·미룰 일·쉬기 시작할 시각'),
}

def build(f,lens_id,concern,plan=None):
    if lens_id not in ROLES or concern not in CONCERNS:return None
    axis,perspective,question,action=ROLES[lens_id]
    tone = (lens.view(lens_id) or {}).get('voice')
    question = voice.speak(concern_question(lens_id, concern), tone)
    action = voice.speak(action, tone)
    value=lens_cuts.axis_value(f,axis,concern)
    observation=lens_cuts._counted(f,[axis])
    label,scene,record=CONCERNS[concern]
    # The report passes its shared plan; standalone editorial clients retain v2.
    if plan is not None:
        from .interpretation import next_action
        selected = plan['selected']
        if selected:
            first = selected[0]
            question = _plan_voice(first['question'], tone)
            action = _plan_voice(next_action(plan), tone)
            perspective = first['title']
            observation = ' · '.join(plan['facts'][ref]['label'] for ref in first['evidence_ids'])
        else:
            question = _plan_voice('어떤 상황에서 이 고민이 가장 크게 느껴지는지 먼저 살펴보세요.', tone)
            action = _plan_voice(next_action(plan), tone)
        value = plan['fingerprint']
    return {'version':VERSION,'id':f'editorial:{VERSION}:{lens_id}:{concern}:{value}',
        'title':f'{label}, 이번 해석에서 확인할 것',
        'perspective':guard.enforce(perspective),
        'observation':guard.enforce(observation),
        'question':guard.enforce(question),
        'scene':guard.enforce(f'{scene} 하나를 떠올리시오. {record} — 이 셋을 나눠 보시오.'),
        'action':guard.enforce(action),
        'boundary':'전통 해석을 돌아보기 위한 질문이오. 맞는 경험이 없다면 내 이야기로 받아들이지 않아도 되오.',
        'source_kind':'traditional_interpretation_and_reflection'}
