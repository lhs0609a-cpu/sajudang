"use client";

/**
 * 쉬어 가는 자리 — 아프게 한 뒤의 책임.
 *
 * ★ 손님이 시킨 것 (2026-09-16)
 *
 *   "이거의 핵심은 정말 팩폭하면서도 동시에 위로를 줘야 한다는 거야.
 *    희망이 생겨야 해 삶에. 그로 인해서 자살하는 사람이 늘어나지
 *    않도록 설계해줘."
 *
 * ★ 이 자리가 **안 하는** 것 셋
 *
 *   조르지 않소     여기서는 아무것도 안 팝니다. 값을 권하지 않습니다
 *   진단하지 않소   「우울하시군요」 는 이 집이 할 말이 아니오.
 *                  병명은 가드가 막고 있고, 막는 게 맞습니다
 *   붙잡지 않소     「더 보시오」 가 아니라 「오늘은 여기까지」 요
 *
 *   하는 것은 하나요 — 오늘 그만두어도 된다고 말하고, 도움 받을 곳을
 *   적어 둡니다.
 *
 * ★ 튀어나오지 않습니다
 *
 *   힘든 사람 앞에 상담 전화를 들이미는 것은 「당신 위험해 보여요」
 *   라고 말하는 것이라, 도리어 문을 닫게 합니다. 덮개도 아니고
 *   알림도 아니오 — 글의 끝에 조용히 서는 한 자리입니다.
 */
import { CARE_LINES, careSignals, type CareSignal } from "@/lib/care";

/** 신호마다 다른 한 줄. 이 자리는 셈을 대지 않소 — 그만두어도 된다고 말하는 자리요. */
function body(why: CareSignal[]): string {
  if (why.includes("되풀이"))
    return "오늘 이 집에 여러 번 오셨소. 같은 글자를 여러 번 읽는다고 답이 더 나오지는 않소 — 여덟 글자는 오늘도 어제와 같소.";
  if (why.includes("안 맞음"))
    return "여러 마디를 두고 아니라 하셨소. 그건 그대가 틀린 게 아니라 이 집의 말이 그대에게 안 맞는 것이오. 안 맞는 말을 더 읽을 까닭이 없소.";
  if (why.includes("늦은 때"))
    return "늦은 시각이오. 밤에 읽은 말은 아침에 읽은 것보다 무겁게 남소 — 같은 글인데도 그렇소. 내일 다시 펴도 글자는 그대로 있소.";
  return "오늘은 여기서 덮어 두셔도 되오. 여덟 글자는 도망가지 않소.";
}

export default function RestHere({
  visits, hookMisses, hour, concern, returning,
}: {
  visits?: number;
  hookMisses?: number;
  hour?: number | null;
  concern?: string | null;
  returning?: boolean;
}) {
  const why = careSignals({ visits, hookMisses, hour, concern, returning });
  if (why.length < 2) return null;
  return (
    <section className="resthere" role="note" aria-label="쉬어 가는 자리">
      <p className="lab">쉬어 가는 자리</p>
      <p className="rest-head">오늘은 여기까지 두시오.</p>
      <p className="rest-body">{body(why)}</p>
      {/* ★ 이 집이 못 하는 일이 있다는 것을 적습니다. 겸양이 아니라
          사실이오 — 명식은 사람을 못 살립니다. */}
      <p className="rest-limit">이 집은 여덟 글자를 셀 뿐이오. 마음이 많이 힘들 때는 사람에게 말하시오 — 셈으로는 안 되는 자리가 있소.</p>
      <ul className="rest-lines">
        {CARE_LINES.map((l) => (
          <li key={l.tel}>
            <a href={`tel:${l.tel.replace(/-/g, "")}`}>{l.name} {l.tel}</a>
            <small>{l.when}</small>
          </li>
        ))}
      </ul>
    </section>
  );
}
