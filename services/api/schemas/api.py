"""
요청·응답 스키마 — packages/shared-types/chart.ts 와 짝을 맞춘다.

★ 응답에 문장 원문·뱅크 키·규칙 조건식을 넣지 않습니다.
  렌더된 HTML 과 statement_id 만 내려보냅니다. (docs/02 §7)
"""
from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field, model_validator

Sex = Literal["M", "F"]
Concern = Literal["money", "work", "love", "people", "dir", "health"]
Tier = Literal["free", "one", "all", "sub"]


class ChartRequest(BaseModel):
    year: int = Field(ge=1900, le=2100)
    month: int = Field(ge=1, le=12)
    day: int = Field(ge=1, le=31)
    hour: Optional[int] = Field(default=None, ge=0, le=23)
    minute: Optional[int] = Field(default=None, ge=0, le=59)
    hour_known: bool = True
    sex: Sex
    birth_city: str = "서울"

    @model_validator(mode="after")
    def _check_hour(self):
        if self.hour_known and self.hour is None:
            raise ValueError("hour_known=true 이면 hour 가 있어야 합니다")
        return self


class ChartResponse(BaseModel):
    chart_id: str
    features: dict
    cached: bool
    # ★ 희소도 — 이 배치가 인구에서 몇 명인가.
    #
    #   엔진에는 있었는데 **유료 리포트에서만** 쓰고 있었습니다. 무료
    #   구간에서 손님이 처음 받는 것은 자기 여덟 글자뿐이고, 그건
    #   숫자가 아니라 글자라 「그래서 뭐」 로 끝납니다.
    #
    #   「1만 명에 165명」 은 지어낸 말이 아니라 **센 값**입니다
    #   (tools/make_rarity.py 가 4만 명을 세어 표를 만듭니다).
    #   값 없이 줄 수 있는 것 중 가장 센 한 줄입니다.
    rarity: Optional[dict] = None
    # ★ 다른 만세력과 갈릴 수 있는 자리. 백 명 중 넷다섯이 걸립니다.
    #   발견당하면 「틀린 집」이 되고, 먼저 말하면 「아는 집」이 됩니다.
    divergence: Optional[dict] = None


class HookRequest(BaseModel):
    chart_id: str
    concern: Concern
    axis4: Optional[str] = Field(default=None, min_length=4, max_length=4)
    name: str = Field(default="", max_length=20)
    lens_id: Optional[str] = None
    # 여기까지 「아니오」가 몇 번 나왔는가.
    #
    # ★ 손님의 응답이 다음 단을 하나도 안 바꾸고 있었습니다. 세 번
    #   아니라 해도 도령이 방향을 안 틀었고, 그때 손님은 이게 녹음이라는
    #   걸 압니다. 둘이 쌓이면 2단이 짚는 자리를 바꿉니다 (bank.TURN_AT).
    misses: int = Field(default=0, ge=0, le=5)


class HookSegment(BaseModel):
    stage: str
    label: str
    source: Optional[str]
    # 근거를 본문 아래에 둘 것인가. 0단(찌르기)만 참입니다 —
    # 위에 놓으면 첫 문장이 강의가 되고, 안 놓으면 여느 점집과 같아집니다.
    source_below: bool = False
    html: str
    question: str
    yes: str
    no: str
    statement_id: str


class HookResponse(BaseModel):
    chart_id: str
    segments: list
    cached: bool


class ReportRequest(BaseModel):
    chart_id: str
    lens_id: str
    tier: Tier = "free"
    # ★ 자격은 이 열쇠로 봅니다. 없으면 무료 구간만 나갑니다.
    #   tier 는 손님이 **보고 싶다고 말한 것**이고, 실제로 열리는 것은
    #   치른 주문이 정합니다 (routers/report.entitled_tier).
    #   계측에는 안 실립니다 — 화면 이름·사건 이름만 나갑니다.
    session_id: Optional[str] = None
    concern: Concern = "love"
    axis4: Optional[str] = Field(default=None, min_length=4, max_length=4)
    # 손님이 적은 이름. 어떤 캐릭터는 **이름으로 부릅니다**.
    #
    # ★ 셈에는 안 씁니다. 부르는 데만 씁니다. 안 적었으면 그 캐릭터의
    #   대신 부르는 말로 물러섭니다 — 「이름」이라고 부르지 않습니다.
    name: str = Field(default="", max_length=20)
    # 결합 축의 추가 입력. {"partner": {...}} / {"context": {...}} 등.
    #
    # ★ 여기 실려 온 것은 **저장하지 않습니다.**
    #   특히 상대 사주는 제3자의 생년월일이라 본인 동의가 없습니다.
    #   컷을 만들고 버립니다. (engine/extras.py · docs/11)
    extras: Optional[dict] = None


class ReportResponse(BaseModel):
    report_id: str
    chart_id: str
    lens: dict
    tier: str
    concern: str
    cuts: list
    locked: list
    # ★ 캐릭터의 여는 말·닫는 말. 여기 없으면 응답에서 조용히 버려집니다 —
    #   실제로 그렇게 되고 있었고, 스무 명의 목소리 중 처음과 끝이 화면에
    #   닿지 않았습니다. (engine/lens.view 의 open/close)
    opening: Optional[str] = None
    closing: Optional[str] = None
    # 이 캐릭터가 더 받아야 하는 입력이 있으면 그 이름. 없으면 None.
    needs_input: Optional[str] = None
    # ★ 이 자리에서 값을 권해도 되는가.
    #   값이 없는 캐릭터(청동자 — 무거운 리포트 뒤 안전망)는 거짓입니다.
    #   화면은 이게 거짓이면 페이월도 목패로 가는 버튼도 그리지 않습니다.
    sells: bool = True
    # 받은 추가 입력이 틀렸으면 그 사유. 리포트는 그대로 나옵니다.
    extra_error: Optional[str] = None


class RelayRequest(BaseModel):
    chart_id: str
    session_id: str = "anon"
    read: list = Field(default_factory=list)
    skipped: list = Field(default_factory=list)
    last_lens: Optional[str] = None


class RelayResponse(BaseModel):
    recommend: list
    forced: list
    blocked: bool
    block_reason: Optional[str]
    breaks: dict


class FeedbackRequest(BaseModel):
    statement_id: str = Field(max_length=200)
    chart_id: str
    # 1 그렇다 / 0 아니다 / **null 글쎄올시다**
    #
    # ★ 이분법이 공감률을 오염시키고 있었습니다.
    #   그렇소·아니오 둘뿐이라 애매한 사람이 **거짓 '그렇소'** 를 눌렀습니다.
    #   그리고 답을 안 하면 다음 단이 안 열려서, 판단을 미루고 싶은 손님에게는
    #   훅이 막다른 화면이었습니다. 첫 단이면 그대로 이탈입니다.
    #
    #   null 은 **노출로만** 셉니다 (repo._counts 의 shown). 공감률의
    #   분모에는 안 들어갑니다.
    answer: Optional[int] = Field(default=None, ge=0, le=1)
    stage: Optional[str] = None
    lens_id: Optional[str] = None
    concern: Optional[Concern] = None
    axis4: Optional[str] = Field(default=None, min_length=4, max_length=4)


class FeedbackResponse(BaseModel):
    ok: bool
    recorded: int


class DailyResponse(BaseModel):
    date: str
    gz: str
    gan: str
    ji: str
    element: str
    relation: str
    score: int
    # 이 점수가 무엇을 센 것인가. 부정만 하지 않고 셈법을 펴 보입니다.
    score_why: list
    score_says: str
    text: str
    # 본문을 줄 단위로. 관계 × 일간 × 신강약 × 계절 × 용신 을 곱한 것이라
    # 같은 날 다른 사람이 받는 문장이 서로 다릅니다. (engine/daily.py)
    lines: list
    notes: list
    source: str
    statement_id: str
    free: bool
