/**
 * 공유 카드 이미지 — 카톡·트위터 썸네일.
 *
 * docs/10 §5 는 cardbg 영상 + html2canvas 로 PNG 를 만들라고 했지만,
 * 그건 사용자가 "이미지로 저장" 을 눌러야 나옵니다. 링크를 **붙여넣는
 * 순간** 뜨는 썸네일은 서버가 만들어 줘야 합니다.
 *
 * next/og 로 요청 때 그립니다. 에셋이 없어도 지금 동작합니다.
 * cardbg 아트가 들어오면 배경만 갈아끼우면 됩니다.
 *
 * ★ 카드에도 생년월일시는 넣지 않습니다.
 * ★ 적중률·통계 같은 말을 쓰지 않습니다.
 */
import { ImageResponse } from "next/og";

export const runtime = "edge";
export const alt = "성신당 星辰堂";
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";

const BASE =
  process.env.API_BASE ??
  process.env.NEXT_PUBLIC_API_BASE ??
  "http://localhost:8000";

/**
 * satori(next/og 렌더러)는 8자리 hex 투명도(#RRGGBBAA)를 못 읽습니다.
 * 그대로 쓰면 그라디언트가 검은 박스로 나옵니다. rgba 로 넘깁니다.
 */
function rgba(hex: string, a: number): string {
  const h = hex.replace("#", "");
  const n = parseInt(h.length === 3 ? h.replace(/(.)/g, "$1$1") : h, 16);
  return `rgba(${(n >> 16) & 255}, ${(n >> 8) & 255}, ${n & 255}, ${a})`;
}

/** 일간 10색 — docs/09 §2 */
const ILGAN_COLOR: Record<string, string> = {
  甲: "#7FB08A", 乙: "#A8C97F", 丙: "#E5B87A", 丁: "#D98BA5", 戊: "#C9A87F",
  己: "#D4C29A", 庚: "#A9B3C4", 辛: "#DCD6E2", 壬: "#7FA0C4", 癸: "#7FC4BC",
};

interface Shared {
  from_name: string | null;
  day_gan: string;
  ilgan_name: string;
  headline: string;
  three_lines: string[];
  strength: string;
  flow: string;
  pillars?: { label: string; gz: string }[];
  hour_known?: boolean;
}

export default async function Image({ params }: { params: { token: string } }) {
  let d: Shared | null = null;
  try {
    const res = await fetch(
      `${BASE}/v1/share/${encodeURIComponent(params.token)}`,
      { next: { revalidate: 300 } },
    );
    if (res.ok) d = (await res.json()) as Shared;
  } catch {
    /* 못 불러오면 기본 카드로 */
  }

  const c = d ? ILGAN_COLOR[d.day_gan] ?? "#E5B87A" : "#E5B87A";
  const who = d?.from_name ? `${d.from_name}님이 보낸` : "성신당 星辰堂";

  return new ImageResponse(
    (
      <div
        style={{
          width: "100%", height: "100%", display: "flex",
          flexDirection: "column", justifyContent: "center",
          padding: "64px 72px", background: "#0C0A12", color: "#F2ECE4",
          fontFamily: "sans-serif", position: "relative",
        }}
      >
        {/* 위에서 내려오는 빛기둥 — 장면 공통 요소 (docs/09 §4) */}
        <div style={{
          position: "absolute", top: 0, right: 0, width: "46%", height: "100%",
          background: `linear-gradient(200deg, ${rgba(c, 0.16)}, ${rgba(c, 0)} 68%)`,
          display: "flex",
        }} />
        {/* 성좌 원륜 — 오른쪽에 크게 */}
        <div style={{
          position: "absolute", right: -90, top: 150, width: 420, height: 420,
          borderRadius: 420, border: `1px solid ${rgba(c, 0.28)}`, display: "flex",
        }} />
        {/* 왼쪽 강조선 */}
        <div style={{
          position: "absolute", left: 0, top: 0, width: 10, height: "100%",
          background: c, display: "flex",
        }} />

        <div style={{ display: "flex", fontSize: 26, color: "#B5ABBE", letterSpacing: 2 }}>
          {who}
        </div>

        <div style={{
          display: "flex", alignItems: "baseline", gap: 20, marginTop: 12,
        }}>
          <span style={{ fontSize: 92, color: c, fontWeight: 700 }}>
            {d?.day_gan ?? "四"}
          </span>
          <span style={{ fontSize: 44, color: "#F2ECE4" }}>
            {d?.ilgan_name ?? "여덟 글자"}
          </span>
        </div>

        <div style={{
          display: "flex", fontSize: 34, color: "#F2ECE4", marginTop: 8,
        }}>
          {d?.headline ?? "맞히는 집이 아니라, 근거 대는 집."}
        </div>

        <div style={{ display: "flex", flexDirection: "column", marginTop: 30, gap: 12 }}>
          {(d?.three_lines ?? []).slice(0, 3).map((l, i) => (
            <div key={i} style={{ display: "flex", alignItems: "center", gap: 14 }}>
              <div style={{
                display: "flex", alignItems: "center", justifyContent: "center",
                width: 30, height: 30, border: `2px solid ${c}`, color: c,
                fontSize: 17,
              }}>
                {i + 1}
              </div>
              <span style={{ fontSize: 27, color: "#B5ABBE" }}>
                {l.length > 46 ? l.slice(0, 46) + "…" : l}
              </span>
            </div>
          ))}
        </div>

        <div style={{
          display: "flex", gap: 18, marginTop: 34, alignItems: "center",
        }}>
          {(d?.pillars ?? []).map((p) => (
            <div key={p.label} style={{
              display: "flex", fontSize: 30, color: c,
              border: "1px solid #2E2740", padding: "6px 14px",
            }}>
              {p.gz}
            </div>
          ))}
          {d?.hour_known === false && (
            <div style={{
              display: "flex", fontSize: 30, color: "#726A80",
              border: "1px dashed #3A3150", padding: "6px 14px",
            }}>
              ◇◇
            </div>
          )}
        </div>

        <div style={{
          display: "flex", marginTop: 26, fontSize: 22, color: "#726A80",
        }}>
          성신당 星辰堂 · {d ? `${d.strength} · 흐름 ${d.flow}` : "전통 명리 해석"}
        </div>
      </div>
    ),
    size,
  );
}
