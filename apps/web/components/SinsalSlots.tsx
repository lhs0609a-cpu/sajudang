"use client";

/**
 * 신살 카드에 인물 그림을 꽂는다.
 *
 * ★ 왜 이게 필요한가 (2026-09-03)
 *
 *   분석지(/summary)에서는 신살마다 인물이 그려지고 눌러서 제작
 *   프롬프트까지 볼 수 있는데, **리포트의 신살 컷에는 그게 없었습니다.**
 *   같은 신살인데 한쪽에는 얼굴이 있고 한쪽에는 한자만 있었습니다.
 *   손님이 값을 치르고 보는 쪽이 오히려 허전했습니다.
 *
 *   리포트 컷은 서버가 만든 HTML 한 덩이라 그 안에 리액트 컴포넌트를
 *   섞을 수 없습니다. 그래서 서버가 **빈 자리**만 남기고
 *   (`<div class="ssfig" data-sinsal="taegeuk">`), 여기서 그 자리에
 *   포털로 그림을 꽂습니다. 서버가 글을 바꿔도 코드는 안 바뀝니다.
 *
 * ★ 자리가 없으면 아무 일도 안 일어납니다. 다른 컷에 써도 안전합니다.
 */
import { useEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";
import SinsalFigure from "@/components/scene/SinsalFigure";

export default function SinsalSlots({ html }: { html: string }) {
  const ref = useRef<HTMLDivElement>(null);
  const [slots, setSlots] = useState<{ el: Element; key: string }[]>([]);

  useEffect(() => {
    const root = ref.current;
    if (!root) return;
    const found = Array.from(root.querySelectorAll<HTMLElement>("[data-sinsal]"))
      .map((el) => ({ el, key: el.dataset.sinsal || "" }))
      .filter((s) => s.key);
    setSlots(found);
  }, [html]);

  return (
    <>
      <div ref={ref} className="cutbody"
           dangerouslySetInnerHTML={{ __html: html }} />
      {slots.map(({ el, key }, i) =>
        createPortal(<SinsalFigure sinsalKey={key} size={104} />, el,
                     key + ":" + i))}
    </>
  );
}
