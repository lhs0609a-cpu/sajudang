export type FortuneProductId = "daeun_deep" | "annual_flow" | "monthly_calendar" | "sinsal_detail" | "compatibility" | "couple_compatibility" | "taekil";
export type FortuneProduct = { id: FortuneProductId; name: string; price: number; kind: "time" | "relationship" | "detail"; summary: string; requiresPartner?: boolean };
export const FORTUNE_PRODUCTS: FortuneProduct[] = [
 {id:"daeun_deep",name:"대운 심층 분석",price:9900,kind:"time",summary:"지금 대운의 핵심 사건과 다음 전환점"},
 {id:"annual_flow",name:"세운·연도별 분석",price:7900,kind:"time",summary:"올해부터 5년의 변화와 기회"},
 {id:"monthly_calendar",name:"월운 캘린더",price:5900,kind:"time",summary:"이번 해 월별로 움직일 때와 멈출 때"},
 {id:"sinsal_detail",name:"신살 전체 해석",price:5900,kind:"detail",summary:"명식에 실제로 성립한 신살만 해석"},
 {id:"compatibility",name:"궁합 분석 1쌍",price:9900,kind:"relationship",summary:"두 명식의 끌림·충돌·지속 조건",requiresPartner:true},
 {id:"couple_compatibility",name:"연인·부부 심층 궁합",price:14900,kind:"relationship",summary:"갈등 장면과 관계를 지키는 합의",requiresPartner:true},
 {id:"taekil",name:"택일 분석",price:7900,kind:"detail",summary:"목적에 맞는 날짜 후보 비교"}
];
export const FORTUNE_BUNDLES = [
 {id:"time_bundle",name:"시간 흐름 패키지",price:19900,includes:["daeun_deep","annual_flow","monthly_calendar"] as FortuneProductId[]},
 {id:"relationship_bundle",name:"관계 패키지",price:19900,includes:["compatibility","couple_compatibility"] as FortuneProductId[]},
 {id:"all_bundle",name:"전체 분석 패키지",price:29900,includes:FORTUNE_PRODUCTS.map(p=>p.id)}
] as const;
export function fortuneProduct(id:string){return FORTUNE_PRODUCTS.find(p=>p.id===id)??null;}
