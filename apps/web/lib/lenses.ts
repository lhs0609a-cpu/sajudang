/**
 * 캐릭터 20인 — 화면 표시용 최소 정보.
 * 프롬프트·금지어·조건식은 서버에만 있습니다. (docs/02 §7)
 */
export interface LensInfo {
  id: string;
  name: string;
  hanja: string;
  group: string;
  /**
   * ★ 별칭 — 진열대 카드에 적히는 짧은 말 (「붉은 눈」 「노름꾼」).
   *
   *   전에는 이 자리도 `archetype` 이었습니다. 그런데 서버(seed)의
   *   archetype 은 **원형**입니다 — 「위험한 매력」처럼 그림을 그릴 때
   *   쓰는 말이지요. 이름이 같으니 스무 명 중 **열여덟 명**이 서버와
   *   화면에서 서로 다른 값을 들고 있었습니다.
   *
   *   같은 이름에 다른 것을 담으면 언젠가 하나를 보고 다른 하나를
   *   고칩니다. 이름을 갈랐습니다.
   */
  epithet: string;
  /** 원형 — 그림을 그릴 때 쓰는 말. seed/lenses.json 과 같아야 합니다. */
  archetype: string;
  /**
   * ★ 무엇을 잘 보는 사람인가.
   *
   *   진열대에 스무 명이 늘어서 있는데, 손님이 아는 것은 이름과
   *   「차가운 미남」 같은 생김새뿐이었습니다. 무엇을 사는지 모른 채
   *   고르라는 셈입니다. 재회가 걸린 사람은 연담을, 돈이 걸린 사람은
   *   행수를 찾아야 합니다.
   *
   *   지어낸 말이 아니라 각자가 **실제로 받는 것과 읽는 자리**에서
   *   나왔습니다 (seed/lenses.json 의 input · lens_view 의 focus).
   */
  specialty: string;
  color: string;
  price: number;
  released: boolean;
  quote: string;
}

export const LENSES: LensInfo[] = [
  { id: "pungun", name: "풍운도령", hanja: "風雲道令", group: "정통", epithet: "차가운 미남", archetype: "차가운 미남", specialty: "왜 하필 지금", color: "#E5B87A", price: 19900, released: true, quote: "월지에 巳가 있고 일간이 丙이오. 통근했다는 뜻이지. 그래서 그대는—" },
  { id: "baegun", name: "백운선사", hanja: "白雲禪師", group: "정통", epithet: "백발 미청년", archetype: "백발 미청년", specialty: "모자란 것 채우기", color: "#BFD3D6", price: 15900, released: true, quote: "나는 십신을 세지 않소. 계절과 온도만 보오." },
  { id: "cheongam", name: "청암거사", hanja: "靑巖居士", group: "정통", epithet: "무뚝뚝한 장년", archetype: "야성적인", specialty: "타고난 그릇", color: "#8FA6B8", price: 15900, released: true, quote: "격을 먼저 잡아야 하오. 그 다음이 용신이지." },
  { id: "sigye", name: "시계장이", hanja: "時計", group: "정통", epithet: "안경 미남", archetype: "지적인 안경", specialty: "때와 시기", color: "#C4B8A0", price: 15900, released: true, quote: "언제인지가 궁금하시오? 그럼 대운부터 봅시다." },
  { id: "eunbyeol", name: "은별 무녀", hanja: "銀星", group: "검사", epithet: "은발 무녀", archetype: "차가운 분석가", specialty: "성향과 어긋난 자리", color: "#DCD6E2", price: 19900, released: true, quote: "그대의 넉 자와 여덟 글자가 어긋난 자리를 보겠소." },
  { id: "jeokhyeol", name: "적혈랑", hanja: "赤血娘", group: "검사", epithet: "붉은 눈", archetype: "위험한 매력", specialty: "끌림과 욕망", color: "#C9707A", price: 4900, released: true, quote: "피의 기운이 어디로 도는지만 보오." },
  { id: "monghwa", name: "몽화", hanja: "夢畵", group: "검사", epithet: "몽환 소녀", archetype: "서늘한 신비", specialty: "신살과 자리", color: "#D98BA5", price: 15900, released: true, quote: "간밤 꿈이 무엇이었소?" },
  { id: "seoyeok", name: "서역 별지기", hanja: "西域", group: "술수", epithet: "이방인", archetype: "이국적 미남", specialty: "태어난 고을과 별", color: "#7FA0C4", price: 19900, released: true, quote: "동쪽 여덟 글자와 서쪽 별자리를 겹쳐 보겠소." },
  { id: "paeseon", name: "패선생", hanja: "牌先生", group: "술수", epithet: "노름꾼", archetype: "능글맞은 미남", specialty: "패로 보는 빈자리", color: "#D4C29A", price: 4900, released: true, quote: "한 장 뽑으시오. 재미로 보는 것이오." },
  { id: "myeonsang", name: "면상선생", hanja: "面相先生", group: "술수", epithet: "관상가", archetype: "날카로운 미남", specialty: "기색과 자리", color: "#C9A87F", price: 8900, released: true, quote: "얼굴은 보지만 남기지는 않소." },
  { id: "wolha", name: "월하선녀", hanja: "月下仙女", group: "관계", epithet: "달빛 선녀", archetype: "인연을 매는 사람", specialty: "인연 맺기", color: "#A896D4", price: 15900, released: true, quote: "일지가 흔들리오. 사람 자리부터 보겠소." },
  { id: "hongmae", name: "홍매파", hanja: "紅媒婆", group: "관계", epithet: "능란한 중년", archetype: "압도적인 언니", specialty: "혼인과 중매", color: "#D98BA5", price: 19900, released: true, quote: "자네, 관과 재를 같이 가졌구먼." },
  { id: "yeondam", name: "연담", hanja: "戀曇", group: "관계", epithet: "다정한 청년", archetype: "상처 있는 미남", specialty: "재회", color: "#E5A0B8", price: 6900, released: true, quote: "지난 사람 이야기를 하러 오셨소." },
  { id: "hwagyeong", name: "화경", hanja: "和鏡", group: "관계", epithet: "거울 미인", archetype: "편들지 않는 판관", specialty: "다툼과 시비", color: "#DCC0D0", price: 15900, released: true, quote: "그 사람이 아니라 그대를 비추겠소." },
  { id: "haengsu", name: "상단 행수", hanja: "商團行首", group: "맥락", epithet: "장사꾼", archetype: "우아한 귀공자", specialty: "돈과 장사", color: "#C4A87F", price: 12900, released: true, quote: "재가 둘이오. 돈이 도는 자리를 보겠소." },
  { id: "hunjang", name: "훈장", hanja: "訓長", group: "맥락", epithet: "엄한 스승", archetype: "엄격한 연상", specialty: "공부와 시험", color: "#A9B3C4", price: 12900, released: true, quote: "자네, 관이 둘일세. 책임이 앞장서는 사람이지." },
  { id: "yakcho", name: "약초의원", hanja: "藥草醫員", group: "맥락", epithet: "온화한 의원", archetype: "다정한 연상", specialty: "몸과 건강", color: "#7FB08A", price: 8900, released: true, quote: "편차가 크오. 모자란 것부터 채웁시다." },
  { id: "ilgwan", name: "일관", hanja: "日官", group: "맥락", epithet: "천문관", archetype: "무심한 미남", specialty: "날 잡기", color: "#7FC4BC", price: 8900, released: true, quote: "절기와 날을 보는 사람이오." },
  { id: "nopa", name: "삼거리 노파", hanja: "三巨里", group: "정서", epithet: "노파", archetype: "원조 걸크러쉬", specialty: "갈림길", color: "#B5ABBE", price: 8900, released: true, quote: "자네, 바닥이 보이는구먼. 앉게." },
  { id: "dongja", name: "청동자", hanja: "靑童子", group: "정서", epithet: "동자", archetype: "청량한 소년", specialty: "첫 자리", color: "#7FC4BC", price: 0, released: true, quote: "아저씨, 차 한 잔 하고 가시오." },
];

export const LENS_BY_ID: Record<string, LensInfo> =
  Object.fromEntries(LENSES.map((l) => [l.id, l]));

export const DEFAULT_LENS = "pungun";
