"""Research-informed editorial checklist, NOT predicted user satisfaction.

Weights/thresholds are internal design choices. They are frozen for before/after
comparisons and must not be tuned to make a release pass. Human scores stay null.
"""
from hashlib import sha256
from pathlib import Path
import json
import re
from .reading_quality import visible_text

ROOT = Path(__file__).resolve().parents[3]
RUBRIC_VERSION = 1
NOTE = '내부 체크리스트 충족 점수입니다. 사용자 만족도 예측이나 명리 정확도가 아니며, 실제 사용자 점수는 응답 전까지 미측정입니다.'
SOURCES = {
    'clarity':'https://www.nngroup.com/articles/mobile-content/',
    'control':'https://selfdeterminationtheory.org/topics/application-technology/',
    'disclosure':'https://www.nngroup.com/articles/progressive-disclosure/',
    'trust':'https://www.nngroup.com/articles/trustworthy-design/',
    'action':'https://cancercontrol.cancer.gov/brp/research/constructs/implementation-intentions',
    'human':'https://www.nngroup.com/articles/testing-content-websites/',
}


def check(key, name, weight, level, evidence, fix, source):
    return dict(key=key, name=name, weight=weight, level=level, evidence=evidence,
        fix=fix if level < 2 else None, source=SOURCES[source])


def total(checks):
    return round(sum(c['weight']*c['level']/2 for c in checks)*100/sum(c['weight'] for c in checks))


def score_reading(reading, result_id='', concern='', lens_id='', tier='all'):
    rows = reading['summary'] + reading['sections']
    texts = [visible_text(row['html']) for row in rows]
    practice = reading.get('practice') or {}
    body = ' '.join(texts+[practice.get(k,'') for k in ('trigger','action','observe')])
    sentences = [s.strip() for s in re.split(r'[.!?]', body) if s.strip()]
    long_count = sum(len(s) > 85 for s in sentences)
    jargon = re.findall(r'[\u4e00-\u9fff]|십신|식상|비겁|관성|재성|인성|지장간|천간',body)
    explained = sum('<details' in r['html'] for r in reading['summary'])
    actions = re.findall(r'<p[^>]*class="reading-action"[^>]*>(.*?)</p>', ''.join(r['html'] for r in rows), re.S)
    unique_actions = {visible_text(a) for a in actions}
    questions = sum('?' in t for t in texts)
    revised = any(r['id']=='revised' for r in rows)
    checks = [
        check('clarity','쉬운 본문',15,0 if jargon else (1 if long_count else 2),
            f'노출 전문 표현 {len(jargon)}개 · 85자 초과 문장 {long_count}개', '긴 문장을 나누고 전문 근거는 펼침 영역으로 옮기기','clarity'),
        check('grounding','결론의 근거 접근',15,2 if (explained == len(reading['summary']) and explained) or (not reading['summary'] and reading.get('empty_reason')) else 0,
            f'핵심 결론 {len(reading["summary"])}개 중 접힌 근거 {explained}개', '각 결론의 계산 근거와 적용 예외 연결하기','trust'),
        check('agency','해석 수정과 거절',15,2 if reading.get('consultation',{}).get('questions') else 0,
            '답변으로 해석을 조정하는 질문 제공' if reading.get('consultation',{}).get('questions') else '수정 질문 없음', '경험과 다른 해석을 제외할 수 있게 하기','control'),
        check('specificity','경험 확인 장면',15,2 if questions >= 2 or revised or (not reading['summary'] and reading.get('empty_reason')) else (1 if questions else 0),
            f'생활 장면을 묻는 본문 {questions}개 · 거절 반영 {revised}', '인물의 과거를 지어내지 않고 실제 장면을 질문하기','human'),
        check('action','행동의 실행 조건',20,2 if all(practice.get(k) for k in ('trigger','action','observe','fallback')) else (1 if actions else 0),
            f'서로 다른 행동 {len(unique_actions)}개 · 언제/확인/대안 {bool(practice)}', '언제 할지, 무엇을 확인할지, 어려울 때 대안을 붙이기','action'),
        check('closure','완결과 가져갈 것',10,2 if practice and any(r['id']=='review' for r in rows) else (1 if actions else 0),
            '실행 카드와 마무리 함께 제공' if practice else '본문 조언만 제공', '한 가지 실행을 선택하고 보관할 수 있게 하기','control'),
        check('structure','읽을 순서',10,2 if reading.get('journey') and len(rows)>1 else 1,
            f'이야기 순서 {bool(reading.get("journey"))} · 본문 {len(rows)}개', '핵심부터 읽고 세부로 이동할 목차 제공','disclosure'),
    ]
    sections=[]
    for row, text in zip(rows,texts):
        n_long=sum(len(s.strip())>85 for s in re.split(r'[.!?]',text))
        terms=len(re.findall(r'[\u4e00-\u9fff]|십신|지장간',text))
        # Section roles differ; a method paragraph does not need to cause emotion.
        role='evidence' if row['id']=='method' else 'story'
        sections.append(dict(id=row['id'],title=row['title'],role=role,
            score=max(0,100-min(60,n_long*15)-min(40,terms*10)) if text else 0,
            metric='문장 길이·전문 표현만 검사; 내용의 타당성/감동 점수 아님',
            chars=len(text),long_sentences=n_long,technical_terms=terms))
    return dict(id=result_id,concern=concern,lens_id=lens_id,tier=tier,version=reading['version'],
        score=total(checks),checks=checks,sections=sections,human_score=None,
        blockers=[c['fix'] for c in checks if c['level']==0],
        review_required=['개인적 공감과 위로는 독자 평가 필요','명리 해석의 타당성은 전문가 검수 필요'])


def page_inventory():
    from . import screenscan
    web=ROOT/'apps/web'
    shell=(web/'components/Shell.tsx').read_text('utf-8')
    screens=screenscan._screens()
    route_files=sorted((web/'app').rglob('page.tsx'))
    page_rows=[]
    for file in route_files:
        src=file.read_text('utf-8')
        for imported in re.findall(r'from [\"\'](\.[^\"\']+)[\"\']',src):
            candidate=file.parent/(imported+'.tsx')
            if candidate.exists():
                src+='\n'+candidate.read_text('utf-8')
        route='/' + str(file.parent.relative_to(web/'app')).replace('\\','/').replace('.','').strip('/')
        ids=re.findall(r'<Shell\s[^>]*screen="([^"]+)"',src)
        # Route rows cover every physical page; state rows cover every declared screen.
        entries=[('route:'+route,route,None)]+[(sid,screenscan.KO.get(sid,sid),screens.get(sid,('',))[0]) for sid in dict.fromkeys(ids)]
        for sid,title,copy in entries:
            public=route!='/admin'
            read=route in ('/omnibus','/report/[id]','/summary','/daily','/s/[token]')
            commerce=route in ('/pay','/me')
            checks=[
                check('purpose','이 화면의 목적',20,2 if re.search(r'<h[12]|title=',src) else 0,
                    f'{file.relative_to(ROOT).as_posix()}의 제목 선언', '제목에 사용자 과업을 명확하게 적기','clarity'),
                check('navigation','다음 행동과 돌아가기',20,2 if re.search(r'<button|<Link|href=',src) and 'onBack' in shell else 0,
                    '소스의 버튼/링크 및 공통 뒤로 이동 검사', '누르면 어디로 갈지 알 수 있는 버튼 제공','trust'),
                check('recovery','실패·입력 수정',15,2 if re.search(r'retry|Retry|다시|수정|setErr',src) else 1,
                    '재시도/수정 문구 소스 검사; 모든 오류 상태의 실측은 별도', '오류 때 입력을 보존하고 다시 시도할 경로 제공','control'),
                check('pace','읽는 속도의 선택',15,2 if 'ReadingControls' in shell else 1,
                    '공통 읽기 모드 버튼' if 'ReadingControls' in shell else '손짓/스크롤로 연출 해제, 명시적 모드 버튼 없음', '바로 읽기와 연출 읽기를 직접 선택하게 하기','control'),
                check('feedback','실제 평가 수집',10,2 if 'PageFeedback' in shell and public else (2 if not public else 0),
                    '관리 화면은 사용자 평점 대상 제외' if not public else '공통 페이지 평가 부품 연결 여부', '기본 선택 없이 과업 성공과 쉬운 정도를 묻기','human'),
            ]
            if read:
                checks.append(check('reuse','읽은 뒤 다시 사용',20,2 if 'ReadingAnalysis' in src and (web/'components/ReadingPractice.tsx').exists() else (1 if re.search(r'print|공유|share|save',src) else 0),
                    '저장/공유/실행 카드 코드 확인', '필요한 한 문장과 행동을 다시 찾을 수 있게 하기','action'))
            elif commerce:
                checks.append(check('terms','가격·해지·범위',20,2 if all(x in src for x in ('환불','구독')) and re.search('price|amount',src) else 1,
                    '가격과 환불/구독 문구 검사; 법률 적합성 판정 아님', '총액·주기·포함 범위·해지 경로를 결제 전 함께 제시','trust'))
            else:
                checks.append(check('burden','불필요한 부담',20,2 if '개인정보' in src or '선택' in src or not public else 1,
                    '선택/입력 안내 소스 검사', '필요한 정보의 이유와 생략 가능한 입력을 설명하기','trust'))
            page_rows.append(dict(id=sid,title=title,route=route,source=file.relative_to(ROOT).as_posix(),
                audience='customer' if public else 'operator',score=total(checks),checks=checks,
                human_score=None,method='정적 소스 체크리스트 · 브라우저 상태별 과업 점수 아님',
                scope='route' if sid.startswith('route:') else 'screen'))
    return page_rows


def score_auxiliary(payload,kind,result_id,case,concern):
    from . import guard
    if kind=='hook':
        texts=[visible_text(r['html']) for r in payload]
        evidence=all(r.get('source') for r in payload)
        completion=len(payload)==5 and all(r.get('yes') and r.get('no') for r in payload)
    else:
        texts=payload.get('plain') or payload.get('lines',[])
        evidence=bool(payload.get('source'))
        completion=bool(payload.get('practice'))
    text=' '.join(texts)
    long_count=sum(len(s.strip())>85 for s in re.split(r'[.!?]',text))
    jargon=len(re.findall(r'[\u4e00-\u9fff]|십신|식상|비겁|관성|재성|인성|지장간|천간',text))
    checks=[check('clarity','쉬운 주 본문',50,0 if jargon else 1 if long_count else 2,
        f'전문 표현 {jargon}개 · 85자 초과 {long_count}개','주 본문을 짧고 쉬운 문장으로 고치기','clarity'),
        check('source','근거 제공',20,2 if evidence else 0,'출처/계산 근거 필드 확인','근거를 펼쳐 볼 수 있게 하기','trust'),
        check('completion','이 결과의 역할 완결',20,2 if completion else 0,
            '5단 응답 흐름' if kind=='hook' else '하루의 실행 카드','다음으로 할 수 있는 행동 제공','action'),
        check('guard','단정 표현 검사',10,0 if guard.scan(payload) else 2,'기존 출력 가드 검사','금지된 단정 표현 제거','trust')]
    return dict(id=result_id,case=case,concern=concern,kind=kind,score=total(checks),checks=checks,
        human_score=None,rubric='auxiliary-output-v1',note='대화·일진의 역할에 맞춘 별도 점검표. 종합 풀이 점수와 직접 비교하지 않습니다.')


def source_fingerprint():
    paths=[]
    for base in ('apps/web','services/api/engine','services/api/routers','packages/shared-types'):
        paths += [p for p in (ROOT/base).rglob('*') if p.suffix in ('.py','.tsx','.ts','.css') and not any(x in p.parts for x in ('node_modules','.next','__pycache__'))]
    paths += [ROOT/'seed/lens_view.json',ROOT/'seed/lens_cuts.json']
    digest=sha256()
    for path in sorted(paths):
        digest.update(path.relative_to(ROOT).as_posix().encode())
        digest.update(path.read_bytes().replace(b'\r\n',b'\n'))
    return digest.hexdigest()[:16]


def snapshot():
    path=ROOT/'seed/value_audit.json'
    if not path.exists():
        return {'available':False,'note':NOTE}
    report=json.loads(path.read_text('utf-8'))
    report['available']=True
    report['stale']=report.get('source_fingerprint') != source_fingerprint() if (ROOT/'apps/web').exists() else None
    report['note']=NOTE
    return report
