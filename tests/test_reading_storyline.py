from datetime import date
from engine import interpretation as ip, reading_context as context, reading_storyline as story, guard
from engine.calendar import build_chart
from engine.features import build_features


def features(hour=15, minute=30):
    return build_features(build_chart(1993,11,25,hour,minute,'M',city='서울'),as_of=date(2026,9,13))


def answered(f, concern, rule, reason, response='yes'):
    return ip.build_plan(f, concern, {'consultation': {'concern': concern, 'answers': {
        ip._answer_key(rule, concern): response, context.key(concern,rule): reason}}})


def test_reason_is_asked_after_behavior_and_is_optional():
    f = features()
    initial = ip.build_plan(f, 'dir')
    claim = initial['selected'][0]
    assert not any(q['id'].startswith('reason:') for q in ip.questions(initial)['questions'])
    confirmed = ip.build_plan(f, 'dir', {'consultation': {'concern':'dir', 'answers': {ip._answer_key(claim['id'],'dir'):'yes'}}})
    q = ip.questions(confirmed)['questions'][0]
    assert q['id'] == context.key('dir',claim['id'])
    assert q['options'][-1]['id'] == 'unknown'
    assert context.selected(confirmed) is None


def test_same_chart_and_behavior_get_three_different_actions_and_recognition():
    f = features()
    rule = 'learning_output'
    plans = [answered(f,'dir',rule,cause) for cause in ('chosen','worried','required')]
    assert len({str(p['facts']) for p in plans}) == 1
    assert len({p['basis'] for p in plans}) == 1
    assert len({ip.next_action(p) for p in plans}) == 3
    assert len({tuple(story.closing_lines(story.build(p,f))) for p in plans}) == 3
    for p in plans:
        reading = ip.render(p,f,'all',comprehensive=True)
        assert reading['journey']['source'] == 'self_report'
        assert not guard.scan(reading)
        row = next(r for r in reading['summary'] if r['id'].startswith(rule+'@'))
        assert context.selected(p)[2][1] in row['html']


def test_external_requirement_does_not_return_as_personality_blame():
    f = features()
    plan = answered(f,'dir','learning_output','required')
    reading = ip.render(plan,f,'all')
    row = next(r for r in reading['summary'] if r['id'].startswith('learning_output@'))
    visible_part = row['html'].split('<details')[0]
    assert '상대가 계속 더 요구' in visible_part
    assert '편지는 못 보내고 밤만 깊어지오' not in visible_part
    assert '성향 설명은 여기서 멈추겠소' in visible_part


def test_reason_cannot_be_guessed_or_carried_across_rejection():
    f = features()
    bad = ip.build_plan(f,'dir',{'consultation':{'concern':'dir','answers':{context.key('dir','learning_output'):'worried'}}})
    assert bad['input_error'] and not bad['answers']
    rejected = answered(f,'dir','learning_output','worried',response='no')
    assert context.key('dir','learning_output') not in rejected['answers']
    assert context.selected(rejected) is None
    assert '걱정돼서 다시 손봤다고' not in str(ip.render(rejected,f,'all',comprehensive=True))


def test_domain_scenes_are_distinct_for_all_ten_gods():
    assert len(story.SCENES) == 10
    scenes = []
    for god, rows in story.SCENES.items():
        assert len(rows) == 6
        assert len(set(row[2] for row in rows)) == 6
        scenes.extend(row[0] for row in rows)
    assert len(set(scenes)) == 60


def test_real_chart_change_changes_story_but_equivalent_input_does_not():
    f, nearby, equivalent = features(),features(16,30),features(15,29)
    a,b,c = [story.build(ip.build_plan(x,'dir'),x) for x in (f,nearby,equivalent)]
    assert a['visibility'] != b['visibility']
    assert story.domain_lines(a,'money') != story.domain_lines(b,'money')
    assert story.domain_lines(a,'money') == story.domain_lines(c,'money')


def test_every_reason_branch_has_an_action_and_complete_recognition():
    for rule, reasons in context.REASONS.items():
        assert set(reasons) == {'chosen','worried','required'}
        assert len({row[2] for row in reasons.values()}) == 3
        assert len({row[3] for row in reasons.values()}) == 3
        assert not guard.scan(reasons)


def test_free_story_is_complete_and_does_not_withhold_reassurance():
    f = features()
    plan = answered(f,'dir','learning_output','worried')
    free = ip.render(plan,f,'free')
    assert len(free['summary']) == 1
    assert 'reading-recognition' in free['summary'][0]['html']
    assert 'reading-action' in free['summary'][0]['html']
    assert [s['id'] for s in free['sections']] == ['method']
