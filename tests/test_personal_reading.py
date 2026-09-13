from datetime import date
from engine.calendar import build_chart
from engine.features import build_features
from engine import interpretation as ip, personal_reading as personal, guard


def sample(hour=15, minute=30, known=True):
    return build_features(build_chart(1993, 11, 25, hour if known else None,
        minute if known else None, 'M', hour_known=known, city='서울'), as_of=date(2026, 9, 13))


def test_sample_is_not_misread_as_preparation_or_leadership():
    f = sample()
    plan = ip.build_plan(f, 'dir')
    assert plan['personal']['groups'] == {'비겁': 1, '식상': 4, '재성': 0, '관성': 0, '인성': 2}
    claims = {c['id']: c for c in plan['selected']}
    assert '리더십보다 설명과 수정' in claims['initiative_expression']['thesis']
    assert '결과를 낸 뒤에도 수정을 멈추지' in claims['learning_output']['thesis']
    text = personal.portrait_html(f, plan)
    assert '상관이 천간에 3번' in text
    assert '월지 亥의 본기는 식신' in text
    assert '일지 戌의 본기는 편인' in text
    assert '경계에서 약 2분' in text


def test_hidden_resources_are_not_described_as_absent_and_domains_are_distinct():
    plan = ip.build_plan(sample(), 'money')
    money = personal.domain_reading(plan, 'money')
    assert '재성 0' in money and '甲(편재)' in money and '乙(정재)' in money
    assert '가격' in money and '수정 횟수' in money
    love = personal.domain_reading(plan, 'love')
    assert '공감을 대신' in love and '일지' in love
    work = personal.domain_reading(plan, 'work')
    assert '관성 0' in work and '丁(정관)' in work
    assert len({personal.domain_reading(plan, d) for d in ip.content()['domains']}) == 6


def test_pair_directions_change_the_mechanism_for_every_rule():
    # Swap the same two nonzero counts: coexistence is unchanged, interpretation must change.
    for rule in ip.content()['rules']:
        a, b = rule['groups']
        facts = {'group:' + g: {'value': 1} for g in ip.GROUPS}
        facts['group:' + a]['value'] = 4
        left = personal.specialize(rule, facts)
        facts['group:' + a]['value'] = 1
        facts['group:' + b]['value'] = 4
        right = personal.specialize(rule, facts)
        assert left['title'] != right['title'], rule['id']
        assert left['action'] != right['action'], rule['id']


def test_nearby_birth_hour_changes_visible_structure_and_money_basis():
    a, b = (ip.build_plan(f, 'money') for f in (sample(), sample(16, 30)))
    assert a['personal'] != b['personal']
    assert personal.domain_reading(a, 'money') != personal.domain_reading(b, 'money')
    unknown = ip.build_plan(sample(known=False), 'money')
    assert '시주' not in personal.domain_reading(unknown, 'money')


def test_rejection_does_not_resurface_as_personality():
    f = sample()
    first = ip.build_plan(f, 'dir')['selected'][0]
    plan = ip.build_plan(f, 'dir', {'consultation': {'concern': 'dir', 'answers': {ip._answer_key(first['id'], 'dir'): 'no'}}})
    assert '전통 해석에서의 중심' not in personal.portrait_html(f, plan)
    for domain in ip.content()['domains']:
        assert '성향 확장은 보류' in personal.domain_reading(plan, domain)
    assert not guard.scan(ip.render(plan, f, 'all', comprehensive=True))


def test_transit_explains_natal_interaction_not_only_calendar_labels():
    f = sample()
    year = personal.transit_reading(f, '丙', '午')
    assert '원국 관성 0자리' in year
    assert '승인 가능한 형식' in year
    assert year != personal.transit_reading(f, '癸', '亥')
