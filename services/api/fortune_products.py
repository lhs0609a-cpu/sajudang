from dataclasses import asdict, dataclass

@dataclass(frozen=True)
class FortuneProduct:
    id: str
    name: str
    price: int
    kind: str
    summary: str
    requires_partner: bool = False

PRODUCTS = (
    FortuneProduct('daeun_deep','대운 심층 분석',9900,'time','지금 대운의 핵심 사건과 다음 전환점'),
    FortuneProduct('annual_flow','세운·연도별 분석',7900,'time','올해부터 5년의 변화와 기회'),
    FortuneProduct('monthly_calendar','월운 캘린더',5900,'time','이번 해 월별로 움직일 때와 멈출 때'),
    FortuneProduct('sinsal_detail','신살 전체 해석',5900,'detail','명식에 실제로 성립한 신살만 해석'),
    FortuneProduct('compatibility','궁합 분석 1쌍',9900,'relationship','두 명식의 끌림·충돌·지속 조건',True),
    FortuneProduct('couple_compatibility','연인·부부 심층 궁합',14900,'relationship','갈등 장면과 관계를 지키는 합의',True),
    FortuneProduct('taekil','택일 분석',7900,'detail','목적에 맞는 날짜 후보 비교'),
)
BUNDLES = (
    {'id':'time_bundle','name':'시간 흐름 패키지','price':19900,'includes':['daeun_deep','annual_flow','monthly_calendar']},
    {'id':'relationship_bundle','name':'관계 패키지','price':19900,'includes':['compatibility','couple_compatibility']},
    {'id':'all_bundle','name':'전체 분석 패키지','price':29900,'includes':[p.id for p in PRODUCTS]},
)

def public_products():
    return {'products':[asdict(p) for p in PRODUCTS], 'bundles':list(BUNDLES), 'currency':'KRW'}

def get_product(product_id):
    return next((p for p in PRODUCTS if p.id == product_id), None)

def get_offer(offer_id):
    product = get_product(offer_id)
    if product is not None: return product
    return next((b for b in BUNDLES if b['id'] == offer_id), None)
