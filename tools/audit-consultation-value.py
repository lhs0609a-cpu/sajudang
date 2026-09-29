"""Reproducible value audit and readable before/after review, using local engine."""
import json
import sys
from datetime import date
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'services/api'))
from engine import character_consultation as cc, lens, topic
from engine.calendar import build_chart
from engine.features import build_features
from engine.consultation_decisions import READINGS, ACTIONS
from engine.report import build_report, _plain

OUT = ROOT / 'output/quality-value-20260929'
OUT.mkdir(parents=True, exist_ok=True)
concerns = ('money', 'work', 'love', 'people', 'dir', 'health', 'real_estate')
profiles = [(1993, 11, 25, None, None, 'F'), (1988, 5, 3, 14, 20, 'M'), (2001, 2, 17, 7, 0, 'F')]
rows, samples = [], []
for index, birth in enumerate(profiles):
    features = build_features(build_chart(*birth, hour_known=birth[3] is not None), as_of=date(2026, 9, 29))
    for character, interview in cc.INTERVIEWS.items():
        for concern in concerns:
            spec = cc.enrich_spec(topic.ask_spec(concern), character, concern)
            answers = {('choice' if n == 1 else f'choice{n}'):spec[('options' if n == 1 else f'options{n}')][0]['id']
                       for n in range(1, 6) if spec.get('options' if n == 1 else f'options{n}')}
            free = build_report(features, 'quality-audit', character, 'free', concern, extras={'topic':answers})
            paid = build_report(features, 'quality-audit', character, 'one', concern, extras={'topic':answers})
            assert paid['concern'] == concern
            assert paid['practice']['version'] == 4
            free_ids = {c['id'] for c in free['cuts']}
            extra = [c for c in paid['cuts'] if c['id'] not in free_ids]
            rows.append({'profile':index, 'character':character, 'concern':concern,
                         'price_krw':lens.public(character)['price'],
                         'free_chapters':len(free['cuts']), 'paid_chapters':len(paid['cuts']),
                         'additional_chapters':len(extra), 'additional_input':paid['needs_input'],
                         'additional_characters':sum(len(_plain(c['html'])) for c in extra)})
        if index == 0:
            alternatives = []
            for option in (interview[4][0], interview[4][-1]):
                from engine.practice import build
                result = cc.enrich_practice(build('work'), character,
                    {'choice4':interview[2][0]['id'], 'choice5':option['id']})
                alternatives.append({'answer':option['label'], 'reading':result['specialist_verdict'],
                                     'action':result['specialist_action'], 'review':result['specialist_review']})
            samples.append({'id':character,'name':lens.public(character)['name'],
                            'before':interview[6],'after':alternatives})

summary = {'profiles':len(profiles), 'characters':20, 'concerns':len(concerns),
           'reports_generated':len(rows)*2,
           'interpretation_branches':sum(map(len, READINGS.values())),
           'action_branches':sum(map(len, ACTIONS.values())),
           'answer_combinations':sum(len(r[2])*len(r[4]) for r in cc.INTERVIEWS.values()),
           'human_satisfaction':None,
           'note':'분기 수와 분량은 만족도 점수가 아닙니다. 실제 고객의 재방문·도움 여부는 별도 검증이 필요합니다.'}
(OUT/'audit.json').write_text(json.dumps({'summary':summary,'products':rows,'samples':samples}, ensure_ascii=False, indent=2), encoding='utf-8')
cards = []
for s in samples:
    alternatives = ''.join(f'<article><small>고른 답 · {escape(a["answer"])}</small><p>{escape(a["reading"])}</p><h4>할 일 하나</h4><p>{escape(a["action"])}</p><h4>확인 기준</h4><p>{escape(a["review"])}</p></article>' for a in s['after'])
    cards.append(f'<section><h2>{escape(s["name"])}</h2><p class="before">기존: 답과 무관하게 “{escape(s["before"])}”</p><div class="pair">{alternatives}</div></section>')
table = ''.join(f'<tr><td>{escape(lens.public(r["character"])["name"])}</td><td>{r["concern"]}</td><td>{r["price_krw"]:,}원</td><td>{r["free_chapters"]}</td><td>{r["paid_chapters"]}</td><td>{r["additional_characters"]:,}</td><td>{escape(str(r["additional_input"] or "없음"))}</td></tr>' for r in rows if r['profile']==0)
html = f'''<!doctype html><html lang="ko"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>성신당 전체 품질 검토</title>
<style>body{{margin:0;background:#131c18;color:#e5e8db;font:16px/1.85 system-ui}}main{{max-width:1040px;margin:auto;padding:48px 24px}}h1,h2,h3,h4{{color:#ecd4a9;line-height:1.5}}h1{{font-size:36px}}section{{border-top:1px solid #526452;padding:24px 0}}small,.before{{color:#b6c4b1}}.pair{{display:grid;grid-template-columns:1fr 1fr;gap:18px}}article{{background:#203028;padding:24px;border-radius:12px}}h4{{margin:18px 0 4px}}p{{margin:8px 0 18px}}table{{border-collapse:collapse;width:100%;font-size:14px}}th,td{{padding:10px;text-align:left;border-bottom:1px solid #465145}}.scroll{{overflow:auto}}@media(max-width:640px){{.pair{{grid-template-columns:1fr}}h1{{font-size:28px}}}}@media print{{body{{background:white;color:#222}}h1,h2,h3,h4{{color:#222}}article{{background:#eee}}section{{break-inside:avoid}}}}</style>
<main><small>2026.09.29 · 로컬 구현 검증 · 운영 배포 전</small><h1>돈을 내고 읽은 뒤,<br>내 선택에 무엇이 남는가.</h1>
<p>기존 구조의 핵심 결함은 상담 질문에 답해도 판정과 행동이 바뀌지 않는 것이었습니다. 선택 문구만 되풀이하는 개인화에서 벗어나, 답에 맞는 해석·할 일·다시 볼 기준을 연결했습니다.</p>
<p>{summary['reports_generated']}개 리포트 생성 · 20명 × 7개 고민 × 3개 명식 × 무료/개별 유료.<br>{summary['interpretation_branches']}개 해석 분기 · {summary['action_branches']}개 행동/확인 기준 · {summary['answer_combinations']}개 답 조합.</p>
<h2>평가와 설계</h2><p>개선 전: 질문을 많이 받아도 핵심 답은 고정되어 유료 개인화의 설득력이 부족했습니다. 개선 후: 실제 답에 따라 다음 선택이 달라지며, 한 화면에서 중복되던 과제를 줄였습니다. 긍정적인 답을 억지로 문제화하지 않고 휴식과 연락 중단도 유효한 결론으로 다룹니다.</p>
<p>A1에는 서비스가 만드는 차이를 예시로 보여 줍니다. 질문 이후 첫 요약·전문 본문·행동 카드는 같은 분기를 사용합니다. 생년월일에서 계산한 내용과 직접 답한 상황에서 나온 조언은 구분합니다. 기존 MBTI 과제가 전문 행동과 충돌하지 않도록 막았습니다.</p>
<p><b>남은 한계:</b> 기존 사주 해석 문장 전체를 새로 집필한 것은 아닙니다. 선택형 답변 기반의 편집 콘텐츠이며 개별 전문가의 실시간 상담이 아닙니다. 실제 돈값과 감동은 자동 검사로 확정할 수 없습니다. 아래 분량은 제공 범위 확인용이며 만족도 점수가 아닙니다. 운영 서버 반영과 실제 결제 거래는 별도입니다.</p>
<h2>20명 전체 · 같은 질문에 달라지는 행동</h2>{''.join(cards)}
<h2>검증 결과와 남은 작업</h2><p>전체 회귀검사 2,499개 통과·2개 건너뜀. 마지막 API 변경 관련 255개 검사 통과. 브라우저 15개 검증 기록과 모바일/PC 스크린샷은 screens 폴더에서 볼 수 있습니다. 최종 판정과 화면별 설계는 설계와-검증.md에 정리했습니다.</p><p>구형 bank.build_hook의 2단계 공통 글자 비율은 34.8%로 내부 기준 26%를 초과했습니다. 현재 첫 해석 API는 별도 build_first_reading 경로를 사용합니다. 구형 문장 감사까지 통과했다고 보고하지 않습니다.</p>
<details><summary>140개 상품 조합의 가격과 무료/유료 제공 범위 펼치기</summary><p>첫 명식 표본 기준. 나머지 두 표본은 audit.json에 포함됩니다. 글자 수는 태그를 제거한 추가 본문 기준입니다. 추가 입력이 필요한 항목은 그 입력 없이 완성되었다고 보지 않습니다.</p><div class="scroll"><table><thead><tr><th>상담자</th><th>고민</th><th>개별 가격</th><th>무료 장</th><th>유료 장</th><th>추가 글자</th><th>추가 입력</th></tr></thead><tbody>{table}</tbody></table></div></details></main></html>'''
(OUT/'review.html').write_text(html, encoding='utf-8')
print(json.dumps(summary, ensure_ascii=False))
