"use client";

/**
 * 관리자 레일 — 참조 구현체(reference/sajudang.html)의 좌측 레일을 옮긴 것.
 *
 * 전체 화면을 한 자리에서 오가며 플로우를 확인하고 고치는 용도입니다.
 *
 * ★ 켜고 끄기
 *      ?admin=1   켬 (브라우저에 기억됨)
 *      ?admin=0   끔 (레일 머리의 [숨기기] 와 같습니다)
 *
 *   기본값은 빌드가 정합니다 — NEXT_PUBLIC_ADMIN_DEFAULT.
 *   출시 전에는 켜짐이라 새 브라우저·시크릿창에서도 바로 보입니다.
 *   출시할 때 그 값을 0 으로 두면 기본 꺼짐이 되고, 그때부터는
 *   ?admin=1 을 아는 사람만 봅니다.
 *   docs/08 §5 — 좌측 개발 레일은 프로덕션 화면이 아닙니다.
 *
 * ★ 여기서 하는 일은 전부 **화면 확인용**입니다.
 *   계산은 그대로 서버(/v1/chart)가 합니다. 레일이 값을 지어내지 않습니다.
 */
import { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { api, ApiError } from "@/lib/api";
import { LENSES } from "@/lib/lenses";
import {
  CONCERNS, SCREEN_GROUPS, seasonOf, useSession,
  type Concern, type Season,
} from "@/lib/store";

const GAN = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"];
const CITIES = ["서울", "인천", "대전", "대구", "부산", "광주", "제주"];
const AXIS4 = [
  "INTJ", "INTP", "ENTJ", "ENTP", "INFJ", "INFP", "ENFJ", "ENFP",
  "ISTJ", "ISFJ", "ESTJ", "ESFJ", "ISTP", "ISFP", "ESTP", "ESFP",
];
const SEASONS: { k: Season; label: string }[] = [
  { k: "spring", label: "봄 벚꽃" },
  { k: "summer", label: "여름 능소화" },
  { k: "autumn", label: "가을 국화" },
  { k: "winter", label: "겨울 매화" },
];

/*
 * 출시 전 기본 켜짐. 출시할 때 Vercel 환경변수에 0 을 넣으면 꺼집니다.
 * 값을 안 주면 켜짐입니다 — 아직 출시 전이기 때문입니다.
 */
const ADMIN_DEFAULT = process.env.NEXT_PUBLIC_ADMIN_DEFAULT !== "0";

const EL = { 목: "나무", 화: "불", 토: "흙", 금: "쇠", 수: "물" } as Record<string, string>;

export default function DevRail() {
  const s = useSession();
  const router = useRouter();
  const path = usePathname();
  const params = useSearchParams();
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [open, setOpen] = useState(true);

  /*
   * 켜고 끄는 규칙 — 사람이 정한 것이 빌드 기본값을 이깁니다.
   *   ?admin=1 / ?admin=0  → 사람이 정했다고 기억(adminSet)
   *   정한 적이 없으면      → 빌드 기본값(ADMIN_DEFAULT)
   * 이 순서가 아니면 ?admin=0 으로 끈 레일이 다음 방문에 도로 켜집니다.
   */
  useEffect(() => {
    const v = params.get("admin");
    if (v === "1") { s.set({ admin: true, adminSet: true }); return; }
    if (v === "0") { s.set({ admin: false, adminSet: true }); return; }
    if (!s.adminSet && ADMIN_DEFAULT && !s.admin) s.set({ admin: true });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [params, s.adminSet]);

  if (!s.admin) return null;

  const here = (href: string) => {
    const [p, q] = href.split("?");
    if (p !== path) return false;
    if (!q) return true;
    const [k, v] = q.split("=");
    return (params.get(k) ?? (k === "step" ? "a1" : "b1")) === v;
  };

  /*
   * 화면 32개를 **한 줄로** 편 것. 그룹은 사람이 찾기 좋으라고 나눈
   * 것이고, 흐름을 지나가려면 순서가 필요합니다.
   */
  const FLAT = SCREEN_GROUPS.flatMap((g) => g.items);
  const navAt = FLAT.findIndex((it) => here(it.href));


  const recalc = async () => {
    // 날짜를 지역 변수로 빼서 타입을 좁힙니다 (store 는 number | null).
    const { year, month, day } = s;
    if (year === null || month === null || day === null) {
      setErr("년·월·일을 다 적어야 계산하오.");
      return;
    }
    setBusy(true);
    setErr(null);
    try {
      const r = await api.chart({
        year, month, day,
        hour: s.hourKnown ? s.hour : null,
        minute: s.hourKnown ? s.minute : null,
        hour_known: s.hourKnown, sex: s.sex, birth_city: s.city,
      });
      s.set({ chartId: r.chart_id, features: r.features });
    } catch (e) {
      setErr(e instanceof ApiError ? e.message : "계산 실패");
    } finally {
      setBusy(false);
    }
  };

  const f = s.features;

  return (
    <aside className={"rail" + (open ? "" : " closed")}>
      <button className="railtog" onClick={() => setOpen(!open)}
              title={open ? "레일 접기" : "레일 펴기"}>
        {open ? "◀" : "▶"}
      </button>

      {open && (
        <div className="railin">
          <h1>星辰堂</h1>
          <div className="v">
            관리자 · 전체 플로우
            <button
              className="railoff"
              onClick={() => s.set({ admin: false, adminSet: true })}
              title="레일을 끕니다. 다시 켜려면 주소 끝에 ?admin=1">
              숨기기
            </button>
          </div>

          {/* ── 생년월일시 ── */}
          <span className="gh">생년월일시</span>
          <div className="inrow">
            <input value={s.year ?? ""} placeholder="년"
                   onChange={(e) => s.set({ year: +e.target.value || null })} />
            <input value={s.month ?? ""} placeholder="월"
                   onChange={(e) => s.set({ month: +e.target.value || null })} />
            <input value={s.day ?? ""} placeholder="일"
                   onChange={(e) => s.set({ day: +e.target.value || null })} />
          </div>
          <div className="inrow">
            <input value={s.hour ?? ""} placeholder="시"
                   onChange={(e) => s.set({ hour: +e.target.value || 0, hourKnown: true })} />
            <input value={s.minute} placeholder="분"
                   onChange={(e) => s.set({ minute: +e.target.value || 0 })} />
            <select value={s.sex} onChange={(e) => s.set({ sex: e.target.value as "F" | "M" })}>
              <option value="F">여</option>
              <option value="M">남</option>
            </select>
          </div>
          <div className="inrow">
            <select value={s.city} onChange={(e) => s.set({ city: e.target.value })}>
              {CITIES.map((c) => <option key={c} value={c}>{c}</option>)}
            </select>
            <button
              className={"tg" + (s.hourKnown ? "" : " on")}
              onClick={() => s.set({ hourKnown: !s.hourKnown, features: null, chartId: null })}
              title="가장 잘 깨지는 조합 — docs/08 §6"
            >
              {s.hourKnown ? "시각 있음" : "시각 미상"}
            </button>
          </div>
          <button className="mini" onClick={() => void recalc()} disabled={busy}>
            {busy ? "계산 중…" : "다시 계산"}
          </button>
          {err && <div className="fx" style={{ color: "var(--ember)" }}>{err}</div>}

          {/* ── 현재 값 ── */}
          <div className="fx">
            {f ? (
              <>
                <div>{f.pillars.map((p) => p.gz).join(" ")}{f.hour_known ? "" : " ◇◇"}</div>
                <div>일간 <b>{f.day_gan}</b> · {f.strength}({f.strength_score})</div>
                <div>용신 <b>{EL[f.yongsin]}</b> · 흐름 <b>{f.flow}</b> · 없는 것 <b>{EL[f.weak_el]}</b></div>
                <div>주도십신 <b>{f.top_ten_god}</b>{f.top_ten_god_tied ? " (동률)" : ""}</div>
                <div>대운 {f.forward ? "순행" : "역행"} {f.daeun?.[0]?.start_age}수
                  {f.daeun_started ? "" : " · 진입 전"}</div>
                <div>신살 {f.sinsal?.map((x) => x.name).join(" ") || "없음"}</div>
              </>
            ) : (
              <div>명식 없음 — 다시 계산을 누르시오</div>
            )}
          </div>

          {/* ── 고민 ── */}
          <span className="gh">고민</span>
          <div className="gg c3">
            {CONCERNS.map((c) => (
              <button key={c.id} className={s.concern === c.id ? "on" : ""}
                      onClick={() => s.set({ concern: c.id as Concern })}>
                {c.label}
              </button>
            ))}
          </div>

          {/* ── 성향 4글자 ── */}
          <span className="gh">성향 4글자 (2.5단)</span>
          <div className="gg c4">
            <button className={s.axis4 === null ? "on" : ""}
                    onClick={() => s.set({ axis4: null })}>없음</button>
            {AXIS4.map((t) => (
              <button key={t} className={s.axis4 === t ? "on" : ""}
                      style={{ fontFamily: "var(--mono)", fontSize: 9 }}
                      onClick={() => s.set({ axis4: t })}>{t}</button>
            ))}
          </div>

          {/* ── 계절 ── */}
          <span className="gh">계절 (진입 서사)</span>
          <div className="gg c2">
            <button className={s.seasonOverride === null ? "on" : ""}
                    onClick={() => s.set({ seasonOverride: null })}>
              자동 · {seasonOf()}
            </button>
            {SEASONS.map((x) => (
              <button key={x.k} className={s.seasonOverride === x.k ? "on" : ""}
                      onClick={() => s.set({ seasonOverride: x.k })}>{x.label}</button>
            ))}
          </div>

          {/* ── 일간 테마색 ── */}
          <span className="gh">일간 색 (테마 확인)</span>
          <div className="gg c5">
            <button className={s.ilganOverride === null ? "on" : ""}
                    onClick={() => s.set({ ilganOverride: null })}>자동</button>
            {GAN.map((g) => (
              <button key={g} className={s.ilganOverride === g ? "on" : ""}
                      style={{ fontFamily: "var(--serif)" }}
                      onClick={() => s.set({ ilganOverride: g })}>{g}</button>
            ))}
          </div>

          {/* ── 캐릭터 ── */}
          <span className="gh">캐릭터 (렌즈)</span>
          <select className="fld sel" value={s.cur}
                  onChange={(e) => s.set({ cur: e.target.value })}>
            {LENSES.map((l) => (
              <option key={l.id} value={l.id}>
                {l.name}{l.released ? "" : " (미출시)"}
              </option>
            ))}
          </select>

          {/*
            ── 지금 어디인가 · 이전 · 다음 ──────────────────────

            ★ 화면이 32개인데 목록에서 매번 눈으로 찾아 눌러야 했습니다.
              흐름을 확인하려면 순서대로 지나가 봐야 하는데, 그 순서가
              레일 어디에도 없었습니다.

              여기서 **한 줄로 펴서** 이전·다음으로 바로 넘깁니다.
              지금 자리는 이름으로 찍습니다.
          */}
          <span className="gh">지금 자리</span>
          <div className="nav">
            <button disabled={navAt <= 0}
                    onClick={() => navAt > 0 && router.push(FLAT[navAt - 1].href)}>
              ← 이전
            </button>
            <b>{navAt < 0 ? "목록 밖" :
                `${FLAT[navAt].id} · ${FLAT[navAt].name}`}</b>
            <button disabled={navAt < 0 || navAt >= FLAT.length - 1}
                    onClick={() => navAt >= 0 && navAt < FLAT.length - 1 &&
                                   router.push(FLAT[navAt + 1].href)}>
              다음 →
            </button>
          </div>
          <div className="fx">
            <div>{navAt < 0 ? "—" : `${navAt + 1} / ${FLAT.length}`}</div>
          </div>

          {/* ── 화면 ── */}
          {SCREEN_GROUPS.map((g) => (
            <div key={g.group}>
              <span className="gh">{g.group} · {g.label}</span>
              {g.items.map((it) => (
                <Link key={it.id} href={it.href}
                      className={here(it.href) ? "on" : ""}>
                  <b>{it.id}</b> {it.name}
                </Link>
              ))}
            </div>
          ))}

          {/* ── 상태 ── */}
          <span className="gh">상태</span>
          <div className="fx">
            <div>읽음 {s.read.length} · 거절 {s.skipped.length} · 인장 {s.seals.length}</div>
            <div>티어 {s.tier} · 릴레이 {s.relayUsed} · 방문 {s.visits}</div>
          </div>
          <button className="mini gh2" onClick={() => { s.reset(); router.push("/"); }}>
            세션 초기화
          </button>
          <button className="mini gh2" onClick={() => s.set({ admin: false })}>
            레일 끄기 (?admin=1 로 다시)
          </button>
        </div>
      )}
    </aside>
  );
}
