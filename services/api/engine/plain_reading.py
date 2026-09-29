"""A reading edition for every character; calculation originals remain available.

Only text nodes change. Tables, technical details, attributes, numbers and user
quotes remain intact. The dictionary uses the same final-consonant class as the
original term so Korean particles also work across inline markup boundaries.
"""
import re
from html import escape
from html.parser import HTMLParser

from .terms import used_here

VERSION = 'plain-reading-v2'
WORDS = {
    '비견': '독립심', '겁재': '경쟁과 나눌 몫',
    '식신': '꾸준히 만드는 재능', '상관': '표현과 변화 성향',
    '편재': '큰 거래', '정재': '꾸준한 돈 관리',
    '편관': '외부의 압박', '정관': '규칙과 책임',
    '편인': '혼자 깊이 배우는 성향', '정인': '배움과 지원',
    '비겁': '독립심과 경쟁심', '식상': '표현과 실력',
    '재성': '돈과 살림', '관성': '규칙과 책임', '인성': '배움과 지원',
    '십신': '사주 속 역할', '일간': '나를 나타내는 기준',
    '일지': '태어난 날의 아래 글자', '월지': '태어난 달의 아래 글자',
    '년주': '태어난 해의 글자', '월주': '태어난 달의 글자',
    '일주': '태어난 날의 글자', '시주': '태어난 시간의 글자',
    '천간': '사주의 윗줄', '지지': '사주의 아랫줄 글자',
    '지장간': '아래 글자에 담긴 성분',
    '신강': '스스로 버티는 쪽', '신약': '도움이 필요한 쪽',
    '중화': '균형 상태', '용신': '보완할 부분', '희신': '보완을 돕는 부분',
    '기신': '균형을 깨는 부분', '대운': '10년 운', '세운': '올해 운',
    '일진': '오늘 운', '명식': '사주 구성', '원국': '태어난 사주 구성',
    '통근': '버팀목', '득령': '계절의 도움', '득지': '생활의 버팀목',
    '억부법': '강약을 맞추는 계산법', '가중합': '비중을 반영한 합',
    '대운수': '10년 운의 시작 나이', '조후': '춥고 더운 정도',
    '절기': '계절을 나누는 날짜', '절입': '계절이 바뀌는 시점',
    '진태양시': '출생지에 맞춘 시간 표시',
    '순행': '순서대로 도는 진행', '역행': '거꾸로 도는 진행',
    '상생': '서로 돕는 작용', '상극': '서로 누르는 작용',
    '공망': '비어 있다고 해석하는 부분', '격': '사주를 읽는 기준',
    '도화': '눈길을 끄는 표시', '역마': '이동과 변화의 표시',
    '화개': '혼자 몰입하는 표시', '괴강': '강한 고집의 상징',
    '양인': '강한 추진력의 상징', '원진': '엇갈림의 상징',
    '귀문': '예민함의 상징', '백호': '강한 긴장의 표시',
    '길신': '좋게 해석하는 상징', '신살': '글자 조합에 붙인 별칭',
    '식상생재': '표현과 실력을 수입으로 잇는 배치',
    '관인상생': '책임과 배움이 서로 이어지는 구성',
    '재다신약': '돈을 다룰 일에 비해 뒷받침이 적은 쪽',
    '비겁쟁재': '함께 나눌 몫을 살피는 배치',
    '상관견관': '내 표현과 정해진 규칙이 맞서는 구성',
    '식신제살': '꾸준한 실력으로 압박에 대응하는 틀',
    '신강약': '사주에서 나를 돕는 힘의 비중',
    '관살': '역할과 외부 요구의 상징', '신왕': '나를 돕는 힘이 큰 쪽',
    '월령': '태어난 달의 계절 조건', '본기': '아래 글자의 중심 성분 표시',
    '투출': '숨은 성분이 윗줄에도 드러남', '궁위': '사주에서 살피는 생활 자리',
    '격국': '사주를 읽는 전체 틀', '십성': '사주 속 역할의 구분',
    '재고': '재물을 모으는 것으로 읽는 표시',
}
PHRASES = {
    '선택이 갈리는 기준': '무엇을 보고 결정할까',
    '원인이 갈리는 자리': '왜 이런 일이 반복될까',
    '이 캐릭터가 보는 기준': '여기서 중요하게 보는 것',
    '계산으로 확인한 수': '사주에서 확인한 내용',
    '이 반응이면 — 먼저 조율할 일': '이럴 때는 함께 맞춰 보시오',
    '이 반응이면 — 기준을 바꿀 일': '이럴 때는 다른 방법이 필요하오',
    '상대에게 전할 말은 이만큼 구체적으로': '이렇게 말해 보시오',
    '원인·분기·행동': '이유·선택 기준·할 일',
    '명확히': '분명히', '관점 전환': '다르게 보기',
    '자원 배분': '시간과 돈 나누기', '의사결정': '결정',
    '우선적으로': '먼저', '상대적으로': '비교하면',
    '감당 가능한': '감당할 수 있는', '확인 가능한': '확인할 수 있는',
    '분리하': '따로 나누',
    '체력이 남는가 모자라는가': '사주에서 나를 돕는 글자가 얼마나 있는가',
    '도와주는 옛 이름표가 몇인가': '도움을 뜻하는 글자 조합이 있는가',
    '날카로운 판정': '답에서 먼저 살필 점',
    '전문 관점': '이 상담자가 살피는 것',
    '판정 기준': '판단할 기준', '분기점': '선택이 달라지는 지점',
    '검증하': '확인하', '관찰하': '살펴보',
}
_WORDS = re.compile('|'.join(map(re.escape, sorted(WORDS, key=len, reverse=True))))
_GLOSS = re.compile(r'<i\b[^>]*class=["\']gl["\'][^>]*>.*?</i>', re.S)


def text(value, concern=None, sex=None, name=None):
    if name and name in value:
        return name.join(text(part, concern, sex) for part in value.split(name))
    words = WORDS
    if concern == 'love':
        override = ({'재성':'관계와 살림', '정재':'꾸준한 관계', '편재':'새로운 끌림의 표시'} if sex == 'M' else
                    {'관성':'관계의 책임', '정관':'안정된 관계의 상징', '편관':'강한 끌림의 상징'} if sex == 'F' else {})
        words = {**WORDS, **override}
    for before, after in PHRASES.items():
        value = value.replace(before, after)

    def substitute(match):
        word = match.group()
        # "받아들일지" contains 日支 as letters, but is an ordinary verb ending.
        # The old glossary's word-boundary list covers only some terms.
        if match.start() and '가' <= value[match.start()-1] <= '힣':
            return word
        tail = value[match.end():]
        # Ordinary negation and stock/reconsideration must keep their meaning.
        if word == '지지' and re.match(r'\s*(?:않|못|말|마|않으)', tail):
            return word
        if word == '재고' and re.match(r'\s*(?:하|해|를\s*(?:확인|세|줄|정리)|가\s*(?:남|없|많))', tail):
            return word
        if not used_here(value, word, match.start(), match.end()):
            return word
        # Counts describe chart symbols, not an amount of someone's ability.
        counted = re.match(r'\s*\d+(?:\.\d+)?\s*(?:개|회|자|글자)', tail)
        return words[word] + ('에 해당하는 글자' if counted else '')

    return _WORDS.sub(substitute, value)


class _Reader(HTMLParser):
    def __init__(self, concern=None, sex=None, name=None):
        super().__init__(convert_charrefs=False)
        self.out = []
        self.stack = []
        self.concern, self.sex = concern, sex
        self.name = name
        self.paragraph_chars = 0

    def handle_starttag(self, tag, attrs):
        self.out.append(self.get_starttag_text())
        if tag in {'p', 'li', 'h3', 'h4'}:
            self.paragraph_chars = 0
        if tag not in {'br', 'hr', 'img', 'input', 'source', 'wbr'}:
            protected = tag in {'table', 'code', 'pre', 'q', 'script', 'style'} or any(
                key == 'class' and 'reading-calculation' in (value or '') for key, value in attrs)
            self.stack.append((tag, protected))

    def handle_endtag(self, tag):
        self.out.append(f'</{tag}>')
        for i in range(len(self.stack)-1, -1, -1):
            if self.stack[i][0] == tag:
                del self.stack[i:]
                break

    def handle_startendtag(self, tag, attrs):
        self.out.append(self.get_starttag_text())

    def handle_data(self, data):
        if any(p for _, p in self.stack):
            self.out.append(data)
            return
        value = text(data, self.concern, self.sex, self.name)
        if any(tag in {'p','li'} for tag, _ in self.stack):
            # Break only at an authored sentence ending, including within bold
            # or marked text. Keep the inline tags balanced and numbers intact.
            chunks = re.split(r'(?<=[.!?])(\s+)', value)
            for chunk in chunks:
                if chunk.isspace() and self.paragraph_chars >= 80:
                    self.out.append('<br class="reader-break">')
                    self.paragraph_chars = 0
                else:
                    self.out.append(chunk)
                    self.paragraph_chars += len(chunk)
        else:
            self.out.append(value)

    def handle_entityref(self, name):
        self.out.append('&'+name+';')

    def handle_charref(self, name):
        self.out.append('&#'+name+';')

    def handle_comment(self, data):
        self.out.append('<!--'+data+'-->')


def html(value, concern=None, sex=None, name=None):
    if not value:
        return value
    # Dense evidence stays available without interrupting the explanation.
    # Match complete paragraphs only; never remove the evidence or alter values.
    value = re.sub(r'(<p\b[^>]*>이 그림이 나온 자리.*?</p>)',
                   r'<details class="reading-calculation"><summary>이 설명의 계산 근거</summary>\1</details>', value, flags=re.S)
    reader = _Reader(concern, sex, name)
    reader.feed(_GLOSS.sub('', value))
    reader.close()
    result = ''.join(reader.out)
    # Keep authored sentences, but stop long paragraphs becoming a wall of text.
    def paragraph(match):
        body = match.group(2)
        if len(re.sub('<[^>]+>', '', body)) < 160 or '<' in body:
            return match.group()
        sentences = re.split(r'(?<=[.!?])\s+', body)
        return ''.join(match.group(1) + ' '.join(sentences[i:i+2]) + '</p>'
                       for i in range(0, len(sentences), 2))
    return re.sub(r'(<p\b[^>]*>)([^<]+)</p>', paragraph, result)
