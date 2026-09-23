from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from datetime import date
import store
from fortune_products import public_products, get_product, get_offer
router = APIRouter(prefix='/v1/fortune', tags=['fortune'])
@router.get('/products')
def products():
    return public_products()
@router.get('/products/{product_id}')
def product(product_id: str):
    row = get_offer(product_id)
    if row is None: raise HTTPException(404, '상품을 찾을 수 없습니다.')
    return row if isinstance(row, dict) else {'id':row.id,'name':row.name,'price':row.price,'kind':row.kind,'summary':row.summary,'requires_partner':row.requires_partner}


class CalculateRequest(BaseModel):
    session_id: str
    chart_id: str
    product_id: str
    year: int | None = Field(default=None, ge=1900, le=2100)
    month: int | None = Field(default=None, ge=1, le=12)
    partner_chart_id: str | None = None
    dates: list[str] = Field(default_factory=list, max_length=14)


def _entitled(session_id: str, product_id: str) -> bool:
    for oid in store.get_json("orders:" + session_id) or []:
        order = store.get_json("order:" + str(oid)) or {}
        if order.get("status") != "paid": continue
        if f"fortune:{product_id}" in (order.get("unlocked") or []): return True
        if order.get("product_id") == product_id: return True
        if order.get("product_id") == "all_bundle": return True
        if order.get("product_id") == "time_bundle" and product_id in {"daeun_deep","annual_flow","monthly_calendar"}: return True
        if order.get("product_id") == "relationship_bundle" and product_id in {"compatibility","couple_compatibility"}: return True
    return False


def _features(chart_id: str):
    from engine.features import Features
    from routers.chart import load_features
    return Features(**load_features(chart_id))


@router.post('/calculate')
def calculate(req: CalculateRequest) -> dict:
    if not _entitled(req.session_id, req.product_id):
        raise HTTPException(403, '이 상품을 먼저 결제해 주세요.')
    f = _features(req.chart_id)
    pid = req.product_id
    if pid == 'daeun_deep':
        rows = []
        for d in f.daeun:
            rows.append({'age': d['start_age'], 'gz': d['gz'], 'ten_god': d['ten_god'], 'reading': f"{d['start_age']}살부터 10년 동안 {d['gz']} 기운이 중심이 됩니다. {d['ten_god']} 작용이 커지는 구간입니다."})
        return {'product_id': pid, 'title':'대운 심층 분석', 'basis': {'daeun_now': f.daeun_now, 'started': f.daeun_started}, 'rows': rows}
    if pid in ('annual_flow','monthly_calendar'):
        y = req.year or date.today().year
        if pid == 'annual_flow':
            rows=[]
            from engine.calendar import year_ganji
            for yy in range(y, y+5):
                gz = ''.join(year_ganji(yy))
                rows.append({'year': yy, 'gz': gz, 'focus': '확장·결정·정리 중 하나를 실제 일정과 대조해 보세요.', 'action': '그 해에 반드시 끝낼 한 가지를 정하세요.'})
            return {'product_id':pid,'title':'세운·연도별 분석','rows':rows,'note':'현재 명식의 대운과 해당 연도의 기운을 함께 읽습니다.'}
        m = req.month or date.today().month
        rows=[{'month': mm, 'signal': ('움직이기 좋은 달' if mm in (3,6,9,11) else '준비와 점검이 먼저인 달'), 'action': '약속·계약·지출을 하루 단위로 기록하세요.'} for mm in range(1,13)]
        return {'product_id':pid,'title':'월운 캘린더','year':y,'focus_month':m,'rows':rows}
    if pid == 'sinsal_detail':
        return {'product_id':pid,'title':'신살 전체 해석','rows':[{'name':x.get('name'),'hanja':x.get('hanja'),'at':x.get('at'),'target':x.get('target'),'reading':f"{x.get('name')}이 {x.get('at')} 자리에 성립했습니다. 이름보다 실제 사건과 겹치는지 확인하세요."} for x in f.sinsal]}
    if pid in ('compatibility','couple_compatibility'):
        if not req.partner_chart_id: raise HTTPException(422,'상대방 명식이 필요합니다.')
        p = _features(req.partner_chart_id)
        same = f.day_gan == p.day_gan
        return {'product_id':pid,'title':'궁합 분석','rows':[{'axis':'끌림','reading':'서로의 익숙한 방식이 빠르게 맞습니다.' if same else '서로 다른 반응 속도가 끌림과 오해를 함께 만듭니다.'},{'axis':'충돌','reading':f"본인 {f.flow} 흐름과 상대 {p.flow} 흐름이 부딪히는 순간을 먼저 합의하세요."},{'axis':'지속 조건','reading':'감정이 커질수록 말로 확인할 규칙과 돈·시간의 경계를 정해야 오래 갑니다.'}]}
    if pid == 'taekil':
        candidates=[]
        for text_date in req.dates:
            try: d=date.fromisoformat(text_date)
            except ValueError: continue
            score=70 + (10 if d.weekday() in (1,3) else 0) + (5 if d.month in (3,4,9,10) else 0)
            candidates.append({'date':text_date,'score':min(score,95),'verdict':'우선 후보' if score>=80 else '조건부 후보','reason':'목적·시간·준비 조건을 함께 맞추면 진행하기 좋은 날입니다.'})
        return {'product_id':pid,'title':'택일 분석','rows':sorted(candidates,key=lambda x:x['score'],reverse=True)}
    raise HTTPException(404,'지원하지 않는 상품입니다.')

