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


class HookRequest(BaseModel):
    chart_id: str
    concern: Concern
    axis4: Optional[str] = Field(default=None, min_length=4, max_length=4)
    name: str = Field(default="", max_length=20)
    lens_id: Optional[str] = None


class HookSegment(BaseModel):
    stage: str
    label: str
    source: Optional[str]
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
    concern: Concern = "love"
    axis4: Optional[str] = Field(default=None, min_length=4, max_length=4)
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
    answer: int = Field(ge=0, le=1)   # 1 그렇다 / 0 아니다
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
    text: str
    # 본문을 줄 단위로. 관계 × 일간 × 신강약 × 계절 × 용신 을 곱한 것이라
    # 같은 날 다른 사람이 받는 문장이 서로 다릅니다. (engine/daily.py)
    lines: list
    notes: list
    source: str
    statement_id: str
    free: bool
