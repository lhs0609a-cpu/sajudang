"""Turn a grounded interpretation into one optional, observable experiment."""
from . import reading_context

# Trigger and observable result depend on the selected relationship, not random copy.
CUES = {
 'output_value':('다음 일을 맡기 전에','약속한 범위 밖의 일을 따로 말했는지 확인하시오.'),
 'autonomy_standards':('새 일을 나눠 맡을 때','직접 정할 수 있는 일 하나가 분명해졌는지 확인하시오.'),
 'pressure_learning':('같은 급한 일이 다시 생길 때','내가 맡을 것과 도움받을 것이 나뉘었는지 확인하시오.'),
 'shared_reward':('다른 사람과 일을 시작하기 전에','서로 적은 역할과 몫이 같은지 확인하시오.'),
 'expression_rules':('바꿀 점을 말하고 싶을 때','상대가 답할 자리와 정할 사람이 분명했는지 확인하시오.'),
 'learning_output':('끝낸 일을 다시 고치고 싶을 때','미리 정한 선에서 한 번 마쳤는지 확인하시오.'),
 'resources_support':('새 일정을 넣으려 할 때','쉬거나 준비할 자리가 함께 남았는지 확인하시오.'),
 'reward_responsibility':('새 제안을 받았을 때','받는 것과 계속 해야 할 일을 함께 적었는지 확인하시오.'),
 'independent_support':('혼자 해내야 한다는 생각이 들 때','도움받을 부분 하나를 구체적으로 말했는지 확인하시오.'),
 'initiative_expression':('내 설명이 길어지고 있음을 느낄 때','말을 멈추고 상대의 답을 끝까지 들었는지 확인하시오.'),
}
FALLBACK = {
 'work':'바로 협의하기 어렵다면 바뀐 요구 하나만 적어 두시오.',
 'money':'당장 값을 말하기 어렵다면 실제로 쓴 시간부터 한 줄 적으시오.',
 'love':'당장 대화하기 어렵다면 듣고 싶은 말과 하고 싶은 말을 하나씩 나누시오.',
 'people':'여럿 앞에서 어렵다면 믿을 만한 한 사람과 먼저 이야기하시오.',
 'dir':'큰 선택이 어렵다면 되돌릴 수 있는 작은 시험 하나만 고르시오.',
 'health':'당장 일정을 바꾸기 어렵다면 오늘 덜 맡을 일 하나만 정하시오.',
}


def build(plan, shown):
    from .reading_narrator import story
    context=reading_context.selected(plan)
    claim=context[0] if context else (shown[0] if shown else None)
    if claim:
        trigger,observe=CUES[claim['id']]
        action=context[2][2] if context else story(claim)[5]
        remember=context[2][3] if context else story(claim)[4]
    else:
        trigger='최근에 마음에 걸린 일을 떠올릴 때'
        action='실제로 있었던 일과 그 일에 붙인 내 생각을 한 줄씩 나누시오.'
        observe='확인한 일과 아직 모르는 일이 나뉘었는지 보시오.'
        remember='근거가 부족한 설명까지 그대의 모습으로 받아들일 필요는 없소.'
    if plan['answers'].get('stage')=='tried':
        trigger='이미 바꿔 보았는데 같은 문제가 남았을 때'
        action='더 애쓰기 전에 달라지지 않은 조건 하나와 필요한 도움을 적으시오.'
        observe='내가 바꿀 수 있는 것과 다른 사람의 협조가 필요한 것이 나뉘었는지 보시오.'
    return {'trigger':trigger,'action':action,'observe':observe,
        'fallback':FALLBACK[plan['concern']], 'remember':remember,
        'source':'self_report' if context else 'reflection' if not claim else 'traditional_hypothesis'}
