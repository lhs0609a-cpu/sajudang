"""The first conversation uses the same grounded story as the full reading."""
from html import escape
from . import interpretation, reading_storyline, guard, voice
from .reading_narrator import story


def project(segments,f,concern,axis4,you,misses):
    plan=interpretation.build_plan(f,concern)
    claim=next(iter(plan['selected']),None)
    if claim and misses<3:
        title,scene,meaning,cost,recognition,action=story(claim)
        spine=reading_storyline.build(plan,f)
        context=reading_storyline.domain_lines(spine,concern)
        bodies=[(scene,meaning),(cost,recognition),tuple(context[:2]),
            ('스스로 보는 모습과 이 장면이 닮았는지 보오.', '상황에 따라 다르다면 다른 점부터 말해도 되오.'),
            (recognition,action)]
    else:
        bodies=[('이번에는 그대를 한 가지 모습으로 정하지 않겠소.','최근 이 고민에서 마음에 걸린 일 하나가 있었소?'),
            ('그때 실제로 있었던 말과 내가 붙인 생각을 나누어 보오.','아직 확인하지 못한 것은 무엇이오?'),
            ('이미 해본 일이 있다면 같은 숙제를 더 얹지는 않겠소.','바꿔 보아도 남아 있던 조건이 있소?'),
            ('스스로 바꿀 수 있는 것과 다른 사람의 도움이 필요한 것을 나누어 보오.','혼자 책임지기 어려운 부분이 있소?'),
            ('맞지 않는 설명을 받아들이지 않아도 되오.','실제로 겪은 장면과 다른 점을 한 줄 남기는 것으로 시작하시오.')]
    for index,segment in enumerate(segments):
        old=segment['html']
        html=''.join('<p>'+escape(voice.address(line,you))+'</p>' for line in bodies[min(index,4)])
        segment['html']=guard.enforce(html+'<details class="reading-evidence"><summary>사주 근거와 전통 풀이</summary>'+old+'</details>')
        segment['yes']=voice.address('닮은 경험이 있다고 답했소. 그 상황의 차이도 함께 보겠소.',you)
        segment['no']=voice.address('맞지 않는 해석은 받아들이지 않아도 되오. 실제 경험이 먼저요.',you)
        segment['question']=voice.address('실제 경험과 닮은 부분이 있소?',you)
        segment['statement_id']=segment['statement_id'].replace(':copy2',':copy3')
    return segments
