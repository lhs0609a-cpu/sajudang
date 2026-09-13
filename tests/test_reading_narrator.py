from html.parser import HTMLParser
import re
from datetime import date
from engine import interpretation as ip, reading_narrator as narrator, lens, guard
from engine.calendar import build_chart
from engine.features import build_features


class Visible(HTMLParser):
    def __init__(self):
        super().__init__()
        self.depth = 0
        self.parts = []

    def handle_starttag(self, tag, attrs):
        if tag == 'details':
            self.depth += 1

    def handle_endtag(self, tag):
        if tag == 'details':
            self.depth -= 1

    def handle_data(self, text):
        if not self.depth:
            self.parts.append(text)


def visible(html):
    parser = Visible()
    parser.feed(html)
    return ' '.join(parser.parts)


def fixture():
    return build_features(build_chart(1993, 11, 25, 15, 30, 'M', city='서울'), as_of=date(2026, 9, 13))


def test_every_character_and_domain_gets_easy_spoken_prose():
    f = fixture()
    first_lines = set()
    for concern in ip.content()['domains']:
        plan = ip.build_plan(f, concern)
        for character in lens.released():
            reading = ip.render(plan, f, 'all', lens_id=character['id'])
            assert reading['narrator']['id'] == character['id']
            for row in reading['summary'] + reading['sections']:
                body = visible(row['html'])
                assert not re.search(r'[\u4e00-\u9fff]|십신|비겁|식상|재성|관성|인성|천간|지장간|비대칭|집계', body), body
                for sentence in re.split(r'[.!?]', body):
                    assert len(sentence.strip()) <= 95, sentence
            assert not guard.scan(reading)
            if concern == 'dir':
                first_lines.add(visible(reading['summary'][0]['html']).split('.')[0])
    assert len(first_lines) == len(lens.released())


def test_same_claim_has_different_voices_including_headlines():
    f = fixture()
    plan = ip.build_plan(f, 'dir')
    readings = {lid: ip.render(plan, f, 'all', lens_id=lid) for lid in ('pungun', 'hongmae', 'dongja', 'hunjang', 'yeondam')}
    bodies = {lid: visible(r['summary'][0]['html']) for lid, r in readings.items()}
    assert '없소.' in bodies['pungun']
    assert '없어.' in bodies['hongmae']
    assert '없어요.' in bodies['dongja']
    assert '없네.' in bodies['hunjang']
    assert '없습니다.' in bodies['yeondam']
    assert len({r['headline'] for r in readings.values()}) >= 4
    assert len({r['basis'] for r in readings.values()}) == 1


def test_metaphor_keeps_direction_and_rejection():
    f = fixture()
    plan = ip.build_plan(f, 'dir')
    claim = next(c for c in plan['selected'] if c['id'] == 'learning_output')
    assert '편지' in narrator.story(claim)[1]
    inverse = dict(claim, composition='인성 4 · 식상 1')
    assert '지도' in narrator.story(inverse)[1]
    changed = ip.build_plan(f, 'dir', {'consultation': {'concern':'dir', 'answers': {ip._answer_key(claim['id'], 'dir'):'no'}}})
    result = ip.render(changed, f, 'all', comprehensive=True)
    assert '편지' not in ' '.join(visible(r['html']) for r in result['summary'] + result['sections'])


def test_evidence_and_paid_gates_survive_easy_rendering():
    f = fixture()
    plan = ip.build_plan(f, 'dir')
    free = ip.render(plan, f, 'free')
    assert [s['id'] for s in free['sections']] == ['method']
    assert '癸' in free['summary'][0]['html']
    assert '癸' not in visible(free['summary'][0]['html'])
    paid = ip.render(plan, f, 'all', comprehensive=True)
    assert '2026년 입춘부터' in next(s['html'] for s in paid['sections'] if s['id'] == 'timing')
    assert len([s for s in paid['sections'] if s['id'].startswith('domain_')]) == 5
