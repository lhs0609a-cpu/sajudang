/**
 * 신살 의인화 — 이름만 뜨는 표가 아니라, 곁에 선 인물로.
 *
 * ★ 여기 있는 건 **그림 정보**입니다. 해석 문장은 서버(seed/sinsal.json)에
 *   있고 클라이언트로 내려오지 않습니다. (docs/02 §7)
 *
 * ★ 문구 원칙 (docs/14 §7)
 *   "지켜준다" 처럼 단정하지 않습니다. 옛사람들이 그 자리를 어떤 모습으로
 *   그렸는지를 전합니다. 신화의 어법이지 예언의 어법이 아닙니다.
 *
 * ★ 그림 원칙 (docs/09)
 *   로판 웹툰. 다크판타지 아님. 미형 · 큰 눈 · 림라이트.
 *   움직임은 화면의 20% 이내, 얼굴은 눈 깜빡임 정도만.
 */
export type Aura = "wrap" | "edge" | "drift" | "absent";
export type Fx = "petal" | "spark" | "dust" | "leaf" | "snow" | "none";
export type Prop =
  | "sleeve" | "ring" | "brush" | "palanquin" | "hand"
  | "blade" | "tiger" | "twin" | "flower" | "horse"
  | "canopy" | "star" | "none";

export interface SinsalFigure {
  key: string;
  /** 신화적 호칭 — 화면에 크게 뜨는 이름 */
  title: string;
  /** 정체 한 줄 */
  who: string;
  /** 어떤 모습으로 곁에 있는가 — 단정하지 않는 어법 */
  beside: string;
  color: string;
  aura: Aura;
  prop: Prop;
  fx: Fx;
  female: boolean;
  /** 사람이 아닌 것 (범·빈자리) 은 실루엣을 다르게 그린다 */
  human: boolean;
}

export const FIGURES: Record<string, SinsalFigure> = {
  cheoneul: {
    key: "cheoneul", title: "흰 소매의 귀인", who: "천을귀인 天乙貴人",
    beside: "옛사람들은 이 자리를, 일이 틀어질 때 소매를 펼쳐 앞을 가려 " +
            "주는 사람으로 그렸소.",
    color: "#E5B87A", aura: "wrap", prop: "sleeve", fx: "spark",
    female: true, human: true,
  },
  taegeuk: {
    key: "taegeuk", title: "태극을 인 이", who: "태극귀인 太極貴人",
    beside: "시작과 끝을 함께 든 모습으로 그리던 자리요. 끝을 보고야 마는 " +
            "사람 곁에 선다고 했소.",
    color: "#7FC4BC", aura: "wrap", prop: "ring", fx: "spark",
    female: false, human: true,
  },
  munchang: {
    key: "munchang", title: "붓을 든 서생", who: "문창귀인 文昌貴人",
    beside: "배운 것이 밖으로 나갈 때 붓을 쥐여 주던 자리라 했소.",
    color: "#A896D4", aura: "wrap", prop: "brush", fx: "spark",
    female: false, human: true,
  },
  geumyeo: {
    key: "geumyeo", title: "가마를 끄는 이", who: "금여 金輿",
    beside: "굳이 걷지 않아도 실려 가던 자리로 그렸소. 몸이 편한 쪽이오.",
    color: "#D98BA5", aura: "wrap", prop: "palanquin", fx: "petal",
    female: true, human: true,
  },
  amrok: {
    key: "amrok", title: "그림자 속의 손", who: "암록 暗祿",
    beside: "얼굴을 보이지 않고 뒤에서 받치던 손이오. 본인은 모르고 " +
            "지나가는 일이 많다고 했소.",
    color: "#8FA6B8", aura: "wrap", prop: "hand", fx: "dust",
    female: false, human: true,
  },
  yangin: {
    key: "yangin", title: "칼을 쥔 무인", who: "양인 羊刃",
    beside: "날이 선 연장을 쥔 모습이오. 쓰면 강하고, 두면 벤다고 했소.",
    color: "#C9707A", aura: "edge", prop: "blade", fx: "spark",
    female: false, human: true,
  },
  baekho: {
    key: "baekho", title: "흰 범", who: "백호대살 白虎大殺",
    beside: "사람이 아니라 짐승으로 그리던 자리요. 사나운 기운이 뭉친 " +
            "모습이오. 무슨 일이 난다는 뜻으로 쓰지 않소.",
    color: "#DCD6E2", aura: "edge", prop: "tiger", fx: "dust",
    female: false, human: false,
  },
  wonjin: {
    key: "wonjin", title: "등을 돌린 그림자", who: "원진 怨嗔",
    beside: "까닭을 대기 어려운 껄끄러움이오. 부딪히지는 않고 서로 " +
            "등을 돌린 모습으로 그렸소.",
    color: "#726A80", aura: "drift", prop: "twin", fx: "none",
    female: false, human: true,
  },
  dohwa: {
    key: "dohwa", title: "꽃그늘의 사람", who: "도화 桃花",
    beside: "사람의 눈이 모이던 자리요. 요즘은 매력과 표현력으로 읽는 " +
            "쪽이 많소.",
    color: "#D98BA5", aura: "drift", prop: "flower", fx: "petal",
    female: true, human: true,
  },
  yeokma: {
    key: "yeokma", title: "말 위의 나그네", who: "역마 驛馬",
    beside: "한자리에 매이지 않던 자리요. 길 위에 있을 때 제 모습이라 했소.",
    color: "#C4A87F", aura: "drift", prop: "horse", fx: "dust",
    female: false, human: true,
  },
  hwagae: {
    key: "hwagae", title: "일산 아래 홀로", who: "화개 華蓋",
    beside: "꽃 일산을 혼자 인 모습이오. 무리에서 한 발 떨어져 안으로 " +
            "파고들던 자리요.",
    color: "#A896D4", aura: "drift", prop: "canopy", fx: "leaf",
    female: true, human: true,
  },
  gwaegang: {
    key: "gwaegang", title: "북두를 인 장수", who: "괴강 魁罡",
    beside: "우두머리 기질로 보던 일주요. 중간이 잘 없다고 했소.",
    color: "#A9B3C4", aura: "edge", prop: "star", fx: "spark",
    female: false, human: true,
  },
  gongmang: {
    key: "gongmang", title: "빈 자리", who: "공망 空亡",
    beside: "아무도 앉지 않은 자리요. 없다는 뜻이 아니라, 그 자리에 " +
            "기대를 걸기 어렵다는 뜻으로 썼소.",
    color: "#3A3150", aura: "absent", prop: "none", fx: "none",
    female: false, human: false,
  },
};

export const figureOf = (key: string): SinsalFigure | undefined => FIGURES[key];
