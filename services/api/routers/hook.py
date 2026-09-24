"""POST /v1/hook — 무료 훅 5단."""
from fastapi import APIRouter, HTTPException

import store
from engine import bank, lens as lens_mod, topic as topic_mod, voice as voice_mod
from engine import character_consultation as character_consultation_mod
from engine import portrait as portrait_mod
from engine.first_reading import build_first_reading, CACHE_VERSION as READING_VERSION
from engine.features import Features
from routers.chart import load_features
from schemas.api import HookRequest, HookResponse

router = APIRouter(prefix="/v1", tags=["hook"])

HOOK_TTL = 24 * 3600


@router.post("/hook", response_model=HookResponse)
def post_hook(req: HookRequest) -> HookResponse:
    raw = load_features(req.chart_id)
    concern = lens_mod.concern_for(req.lens_id, req.concern)
    # ★ 이 사람이 안 보는 고민이면 **고른 갈래도 같이 내려놓습니다.**
    #
    #   고민이 사랑으로 갈렸는데 갈래는 돈에서 고른 「사업·장사」 인
    #   채로 두면 `topic.ask_cut` 이 목록에 없다고 422 를 냅니다 —
    #   손님 화면에는 「훅을 만들지 못했소」 만 뜨고, 까닭은 자기가
    #   본 적도 없는 사랑 갈래 목록이오. `report.build_report` 는
    #   이미 같은 자리에서 내려놓고 있었습니다. 두 자리가 갈리면
    #   한쪽만 터집니다.
    #   ★ 2026-09-24 — 갈아치우기를 뺐으니, 어긋남은 **고민을 바꿀 때**
    #     납니다. 목록에 없는 갈래만 골라 내려놓습니다.
    topic = topic_mod.keep_valid(concern, req.topic)
    # ★ 캐시 열쇠에 misses 를 넣습니다. 안 넣으면 방향을 튼 훅이
    #   안 튼 훅을 덮어써서, 다음 손님이 남의 응답으로 고쳐진 훅을
    #   받습니다.
    # ★ 꼬리표는 **글이 바뀌면 같이 바꿉니다.** 안 바꾸면 하루(TTL) 동안
    #   옛 글이 그대로 나갑니다 — 말투를 다섯 결로 가른 날(2026-09-17)
    #   「copy4-hao」 가 박힌 채였으면 고친 말투가 안 나갔습니다.
    topic_key = "%s/%s/%s/%s/%s" % (
        (req.topic or {}).get("choice", ""),
        (req.topic or {}).get("choice2", ""),
        (req.topic or {}).get("choice3", ""),
        (req.topic or {}).get("choice4", ""),
        (req.topic or {}).get("choice5", ""))
    key = store.k_hook(req.chart_id, req.concern, req.axis4 or "",
                       req.lens_id or "",
                       "%s#%d#%s#%s" % (req.name, req.misses, READING_VERSION, topic_key))
    cached = store.get_json(key)
    if cached is not None:
        return HookResponse(chart_id=req.chart_id, segments=cached, cached=True)

    f = Features(**raw)
    try:
        # ★ 손님이 고른 다섯을 **첫 해석에도 넘깁니다** (2026-09-23).
        #
        #   v2 는 이 인자가 아예 없어서, 객관식 다섯을 물어 놓고
        #   다섯 마디가 한 개도 안 봤습니다. 손님이 「제대로 물어보는
        #   것도 아니다」 한 것이 맞는 말이었소.
        segs = build_first_reading(
            f, concern, req.axis4, name=req.name,
            you=lens_mod.you_word(req.lens_id, req.name, raw.get("sex")),
            misses=req.misses, topic=topic)
        if topic:
            focused = topic_mod.ask_cut(f, concern, topic)
            if focused:
                segs.insert(0, {
                    'stage':'topic', 'label':focused['title'],
                    'html':focused['html'], 'source':focused['source'],
                    'source_below':True,
                    'statement_id':'first-reading-v3-topic:' + focused['statement_id'],
                    'question':'지금 말씀하신 상황과 맞닿아 있소?',
                    'yes':'그 장면부터 놓고 이어서 보겠소.',
                    'no':'다르게 느껴지는 부분은 억지로 맞추지 않겠소. 다음 관점에서 다시 보시오.',
                })
            specialist = (character_consultation_mod.brief(
                req.lens_id, topic,
                name=lens_mod.public(req.lens_id)["name"])
                if req.lens_id else None)
            if specialist:
                segs.insert(1, {
                    'stage':'specialist', 'label':specialist['title'],
                    'html':specialist['html'], 'source':'선택한 상황 · 이 상담자의 전문 판단 기준',
                    'source_below':True,
                    'statement_id':'first-reading-v3-specialist:%s:%s:%s' % (
                        req.lens_id, topic.get('choice4'), topic.get('choice5')),
                    'question':'이 관점이 지금 놓인 문제의 중심을 제대로 가르고 있소?',
                    'yes':specialist['close'],
                    'no':'이 관점이 전부는 아니오. 맞지 않는 대목은 버리고 다른 상담자의 눈으로 다시 보겠소.',
                })
        # ★ **사람부터 그립니다** (2026-09-24).
        #
        #   손님이 짚었습니다 — 「사주가 추상적이다. 너는 이런 사람이야
        #   하고 디테일하게 말해 줄 수 없냐」. 맞는 말이었소. 이 집의
        #   첫 화면은 여태 **고민에 대한 판정**으로 시작했는데, 손님이
        #   먼저 바라는 것은 판정이 아니라 **알아봐 주는 것**이오.
        #   알아본 다음에야 판정에 값이 서오.
        #
        #   값을 치르기 전에 세 면을 보여 줍니다. 나머지는 풀이에 있소.
        port = portrait_mod.build(
            f, req.lens_id, 3,
            you=lens_mod.you_word(req.lens_id, req.name, raw.get("sex")))
        if port:
            segs.insert(0, {
                'stage': 'portrait', 'label': portrait_mod.TITLE,
                'html': port['html'], 'source': port['source'],
                'source_below': True,
                'statement_id': port['statement_id'],
                # ★ 한 물음에 호칭을 두 번 넣지 마시오. 이름으로 부르는
                #   캐릭터에게서 「여기 적힌 서연이 서연과…」 가 됩니다.
                'question': '여기 적힌 사람이 그대와 얼마나 닮았소?',
                'yes': '그러면 이 사람을 놓고 물으신 일을 보겠소.',
                'no': '맞지 않는 그림이오. 억지로 끼워 맞추지 않겠소 — 아닌 줄은 빼고 읽으시오.',
            })
    except (bank.BankError, topic_mod.TopicInputError,
            character_consultation_mod.CharacterConsultationError) as e:
        # 뱅크에 없는 조합이면 지어내지 않고 알린다
        raise HTTPException(status_code=422, detail=str(e))

    # ★ 훅도 그 사람 말투로 나갑니다 (2026-09-03).
    #
    #   `build_hook` 은 호칭만 갈아 끼우고 **말투는 안 갈았습니다.**
    #   그래서 해요체 캐릭터를 고르고 들어온 손님이 훅에서는 하오체를
    #   듣고 리포트에서는 해요체를 들었습니다 — 사람이 바뀐 것처럼
    #   읽힙니다. 훅은 손님이 이 집에서 **처음 읽는 글**이라 여기서
    #   목소리가 어긋나면 뒤가 다 흔들립니다.
    #
    #   묻는 말과 응답 두 줄도 같이 태웁니다. 대사 세 줄 중 둘만
    #   갈면 그게 더 눈에 띕니다.
    tone = lens_mod.view(req.lens_id).get("voice")
    if tone:
        for s in segs:
            for k in ("html", "question", "yes", "no", "source"):
                if s.get(k):
                    s[k] = voice_mod.speak(voice_mod.address(s[k], lens_mod.you_word(req.lens_id, req.name, raw.get('sex'))), tone)

    store.set_json(key, segs, ttl=HOOK_TTL)
    return HookResponse(chart_id=req.chart_id, segments=segs, cached=False)
