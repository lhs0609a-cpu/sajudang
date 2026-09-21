"use client";

/**
 * 이어지는 자리 — 무료가 끝난 뒤 **누구에게 물을지** 잇는다.
 *
 * ★ 손님이 시킨 것 (2026-09-17)
 *
 *   "자연스럽게 무료가 끝나면 20명 보여주고 누구한테 상담받을지도
 *    연결되어야하고"
 *
 *   무료 6단 끝에는 「값을 고르겠습니다」 와 「한 장으로 받겠습니다」
 *   둘뿐이었습니다. 이 사람 말이 안 맞는 손님에게는 나가는 길밖에
 *   없었소 — 이 집이 파는 것은 「겹치는 데와 갈리는 데」 인데요.
 *
 * ★ 릴레이를 씁니다 — 목록이 아니라 **추천**이오
 *
 *   스무 명을 그냥 늘어놓으면 고르는 일이 손님 몫이 됩니다. 이 집은
 *   **사주 조건이 다음 사람을 고르는** 집이라(CLAUDE.md 한 줄 소개),
 *   `engine/relay` 가 근거를 대며 골라 줍니다. 그 근거를 같이 냅니다.
 *
 * ★ 브레이크는 그대로 둡니다
 *
 *   세션당 릴레이 둘 · 거절한 사람 재권유 없음 — 서버가 셉니다
 *   (`api.consumeRelay`). 여기서 그 셈을 건너뛰면 브레이크가
 *   헐거워집니다. 누르는 순간에만 셉니다 — 보여 주는 것은 안 셉니다.
 */
import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import CharArt from "@/components/CharArt";
import ServerText from "@/components/ServerText";
import { LENS_BY_ID } from "@/lib/lenses";
import { CHARACTER_QUESTIONS } from "@/lib/curiosity";
import { useSession } from "@/lib/store";

type Row = { lens_id: string; name: string; reason: string;
             price?: number | null; quote?: string | null };

export default function NextSeats() {
  const router = useRouter();
  const s = useSession();
  const [rows, setRows] = useState<Row[] | null>(null);

  const load = useCallback(() => {
    if (!s.chartId) return;
    api.relay({
      chart_id: s.chartId, session_id: s.sessionId,
      read: s.read, skipped: s.skipped, last_lens: s.cur,
      concern: s.concern,
    })
      .then((d) => setRows((d.recommend ?? []) as Row[]))
      .catch(() => setRows([]));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [s.chartId, s.sessionId, s.cur, s.concern]);

  useEffect(() => { load(); }, [load]);

  const go = async (lensId: string) => {
    /* 브레이크 셈은 서버가 합니다 — 빠뜨리면 세션 2명 제한이 헐거워지오. */
    try {
      const r = await api.consumeRelay(s.sessionId);
      s.set({ cur: lensId, relayUsed: r.used });
    } catch {
      s.set({ cur: lensId });
    }
    s.markRead(lensId);
    router.push("/report/" + lensId);
  };

  if (!rows || !rows.length) return null;
  return (
    <section className="nextseats">
      <p className="lab">이어지는 자리</p>
      {/* ★ 이 줄이 「왜 다음 사람이 필요한가」 입니다. 없으면 목록이
          그냥 메뉴판이 되오. */}
      <p className="sm">여기까지가 <b>한 사람</b>이 본 것이오. 같은 여덟 글자를 <b>20명</b>이 저마다 다른 데서 읽소 — 그대의 글자가 <b>다음 사람</b>을 골랐소.</p>
      {rows.slice(0, 2).map((r) => {
        const l = LENS_BY_ID[r.lens_id];
        return (
          <div className="dz face" key={r.lens_id}>
            <div className="dzhead">
              {l && <CharArt lens={l} size="chip" />}
              <div>
                <p className="nsname" style={{ color: l?.color }}>{r.name}</p>
                {l && (
                  <span className="topics">
                    {l.topics.split(" · ").map((t) => <i key={t}>{t}</i>)}
                  </span>
                )}
              </div>
            </div>
            <h3 className="reading-next-question">{CHARACTER_QUESTIONS[r.lens_id]}</h3>
            {/* 근거는 서버 글이라 **그려야** 하오 — 풀이가 붙어 옵니다. */}
            <ServerText className="src" html={`근거 · ${r.reason}`} />
            <button className="btn mt" onClick={() => void go(r.lens_id)}>
              {r.name}에게 듣겠습니다
            </button>
          </div>
        );
      })}
      <button className="btn gh" onClick={() => router.push("/lobby?tab=b2")}>
        스무 사람을 다 보겠습니다
      </button>
    </section>
  );
}
