"use client";

/**
 * 장면의 소리 — **눈에 보이는 장면**을 따라갑니다.
 *
 * ★ 왜 화면이 아니라 장면을 보나 (2026-09-07)
 *
 *   손님이 말했습니다 — "어떤 페이지던 애니메이션 들어간건 다 소리가
 *   나와야해". 그런데 배경음을 거는 자리가 `Shell` 한 곳이었고,
 *   거기서 `playBgm("hall")` 을 **한 번 못 박아** 두고 있었습니다.
 *   스물여섯 장면이 어디를 지나든 대청 소리였다는 뜻입니다.
 *
 *   그렇다고 화면(step) 이름으로 표를 짜면 화면이 늘 때마다 그 표를
 *   같이 고쳐야 하고, 안 고치면 그 화면만 조용해집니다. **소리를
 *   내는 것은 장면이니 장면이 들고 있는 것이 맞습니다** — 장면에
 *   `bed` 를 적어 두었습니다 (`components/scene/manifest.ts`).
 *
 * ★ 한 페이지에 장면이 여덟이라서
 *
 *   `app/page.tsx` 와 리포트는 `<Scene>` 을 여덟 개까지 얹어 두고
 *   그중 하나만 보여 줍니다. 얹힐 때 소리를 걸면 **여덟이 동시에**
 *   겁니다 — 마지막에 걸린 것이 이깁니다. 그건 손님이 보고 있는
 *   장면이 아닙니다.
 *
 *   그래서 **보이는지를 봅니다.** 가장 많이 보이는 장면이 소리를
 *   가져갑니다. 스크롤로 다음 장면이 올라오면 소리도 따라 넘어가고,
 *   `lib/sound` 가 겹쳐 넘깁니다(rampDown) — 뚝 끊기지 않습니다.
 *
 * ★ 같은 결이면 손을 안 댑니다
 *
 *   서재 장면 넷을 잇달아 지나도 종이 소리는 **한 번도 안 끊깁니다.**
 *   `playBgm` 이 같은 이름을 무시하고, 결이 자리마다 묶여 있어서
 *   그렇습니다. 방이 바뀔 때만 소리가 바뀝니다.
 */
import { useEffect } from "react";

import { playBgm } from "@/lib/sound";

/** 지금 얼마나 보이는가. 0 이면 화면 밖. */
const seen = new Map<Element, { bed: string; ratio: number }>();
let cur = "";

/**
 * 가장 많이 보이는 장면의 결을 건다.
 *
 * 한 톨이라도 보이면(0 초과) 셉니다 — 화면 위아래로 살짝 걸친 장면도
 * 아무것도 안 보이는 것보다는 낫습니다.
 */
function settle() {
  let best = "";
  let bestRatio = 0;
  seen.forEach((v) => {
    if (v.ratio > bestRatio) { bestRatio = v.ratio; best = v.bed; }
  });
  // 아무것도 안 보이면 **직전 것을 그대로 둡니다.** 화면 사이를
  // 지나는 찰나에 소리를 끊으면 그게 더 거슬립니다.
  if (!best || best === cur) return;
  cur = best;
  playBgm(best);
}

let io: IntersectionObserver | null = null;

function observer(): IntersectionObserver | null {
  if (io) return io;
  if (typeof IntersectionObserver === "undefined") return null;
  io = new IntersectionObserver(
    (entries) => {
      entries.forEach((e) => {
        const got = seen.get(e.target);
        if (got) got.ratio = e.isIntersecting ? e.intersectionRatio : 0;
      });
      settle();
    },
    // 촘촘히 잡아야 「더 많이 보이는 쪽」이 실시간으로 갈립니다.
    { threshold: [0, 0.1, 0.25, 0.5, 0.75, 1] },
  );
  return io;
}

/**
 * 이 장면이 보이는 동안 이 결을 낸다.
 *
 * `bed` 가 없으면(아직 안 적은 장면) 아무 일도 안 합니다 — 소리
 * 때문에 화면이 멈추면 안 됩니다.
 */
export function useAmbience(bed: string | undefined,
                            ref: React.RefObject<Element | null>) {
  useEffect(() => {
    const el = ref.current;
    if (!bed || !el) return;
    const ob = observer();
    if (!ob) {
      // IntersectionObserver 가 없는 아주 옛 브라우저. 그냥 겁니다 —
      // 조용한 것보다는 낫습니다.
      playBgm(bed);
      return;
    }
    seen.set(el, { bed, ratio: 0 });
    ob.observe(el);
    return () => {
      ob.unobserve(el);
      seen.delete(el);
      settle();
    };
  }, [bed, ref]);
}
