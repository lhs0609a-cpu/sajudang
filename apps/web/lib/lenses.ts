/**
 * 캐릭터 20인 — 화면 표시용 최소 정보.
 * 프롬프트·금지어·조건식은 서버에만 있습니다. (docs/02 §7)
 */
export interface LensInfo {
  id: string;
  name: string;
  hanja: string;
  group: string;
  archetype: string;
  color: string;
  price: number;
  released: boolean;
  quote: string;
}

export const LENSES: LensInfo[] = [
  { id: "pungun", name: "풍운도령", hanja: "風雲道令", group: "정통", archetype: "차가운 미남", color: "#E5B87A", price: 19900, released: true, quote: "월지에 巳가 있고 일간이 丙이오. 통근했다는 뜻이지. 그래서 그대는—" },
  { id: "baegun", name: "백운선사", hanja: "白雲禪師", group: "정통", archetype: "백발 미청년", color: "#BFD3D6", price: 15900, released: false, quote: "나는 십신을 세지 않소. 계절과 온도만 보오." },
  { id: "cheongam", name: "청암거사", hanja: "靑巖居士", group: "정통", archetype: "무뚝뚝한 장년", color: "#8FA6B8", price: 15900, released: false, quote: "격을 먼저 잡아야 하오. 그 다음이 용신이지." },
  { id: "sigye", name: "시계장이", hanja: "時計匠", group: "정통", archetype: "안경 미남", color: "#C4B8A0", price: 15900, released: false, quote: "언제인지가 궁금하시오? 그럼 대운부터 봅시다." },
  { id: "eunbyeol", name: "은별 무녀", hanja: "銀星巫女", group: "검사", archetype: "은발 무녀", color: "#DCD6E2", price: 19900, released: false, quote: "그대의 넉 자와 여덟 글자가 어긋난 자리를 보겠소." },
  { id: "jeokhyeol", name: "적혈랑", hanja: "赤血郞", group: "검사", archetype: "붉은 눈", color: "#C9707A", price: 4900, released: false, quote: "피의 기운이 어디로 도는지만 보오." },
  { id: "monghwa", name: "몽화", hanja: "夢花", group: "검사", archetype: "몽환 소녀", color: "#D98BA5", price: 15900, released: false, quote: "간밤 꿈이 무엇이었소?" },
  { id: "seoyeok", name: "서역 별지기", hanja: "西域星師", group: "술수", archetype: "이방인", color: "#7FA0C4", price: 19900, released: false, quote: "동쪽 여덟 글자와 서쪽 별자리를 겹쳐 보겠소." },
  { id: "paeseon", name: "패선생", hanja: "牌先生", group: "술수", archetype: "노름꾼", color: "#D4C29A", price: 4900, released: false, quote: "한 장 뽑으시오. 재미로 보는 것이오." },
  { id: "myeonsang", name: "면상선생", hanja: "面相先生", group: "술수", archetype: "관상가", color: "#C9A87F", price: 9900, released: false, quote: "얼굴은 보지만 남기지는 않소." },
  { id: "wolha", name: "월하선녀", hanja: "月下仙女", group: "관계", archetype: "달빛 선녀", color: "#A896D4", price: 15900, released: true, quote: "일지가 흔들리오. 사람 자리부터 보겠소." },
  { id: "hongmae", name: "홍매파", hanja: "紅媒婆", group: "관계", archetype: "능란한 중년", color: "#D98BA5", price: 19900, released: false, quote: "자네, 관과 재를 같이 가졌구먼." },
  { id: "yeondam", name: "연담", hanja: "戀談", group: "관계", archetype: "다정한 청년", color: "#E5A0B8", price: 6900, released: false, quote: "지난 사람 이야기를 하러 오셨소." },
  { id: "hwagyeong", name: "화경", hanja: "花鏡", group: "관계", archetype: "거울 미인", color: "#DCC0D0", price: 15900, released: false, quote: "그 사람이 아니라 그대를 비추겠소." },
  { id: "haengsu", name: "상단 행수", hanja: "商團行首", group: "맥락", archetype: "장사꾼", color: "#C4A87F", price: 12900, released: true, quote: "재가 둘이오. 돈이 도는 자리를 보겠소." },
  { id: "hunjang", name: "훈장", hanja: "訓長", group: "맥락", archetype: "엄한 스승", color: "#A9B3C4", price: 12900, released: false, quote: "자네, 관이 둘일세. 책임이 앞장서는 사람이지." },
  { id: "yakcho", name: "약초의원", hanja: "藥草醫員", group: "맥락", archetype: "온화한 의원", color: "#7FB08A", price: 9900, released: false, quote: "편차가 크오. 모자란 것부터 채웁시다." },
  { id: "ilgwan", name: "일관", hanja: "日官", group: "맥락", archetype: "천문관", color: "#7FC4BC", price: 9900, released: false, quote: "절기와 날을 보는 사람이오." },
  { id: "nopa", name: "삼거리 노파", hanja: "三巨里老婆", group: "정서", archetype: "노파", color: "#B5ABBE", price: 9900, released: false, quote: "자네, 바닥이 보이는구먼. 앉게." },
  { id: "dongja", name: "청동자", hanja: "靑童子", group: "정서", archetype: "동자", color: "#7FC4BC", price: 0, released: false, quote: "아저씨, 차 한 잔 하고 가시오." },
];

export const LENS_BY_ID: Record<string, LensInfo> =
  Object.fromEntries(LENSES.map((l) => [l.id, l]));

export const DEFAULT_LENS = "pungun";
