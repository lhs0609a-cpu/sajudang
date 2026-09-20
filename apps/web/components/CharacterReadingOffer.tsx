"use client";

import type { ReportResponse } from "@shared/chart";
import { SELLABLE } from "@/lib/biz";
import ServerText from "./ServerText";

export default function CharacterReadingOffer({ report, showFree = false, onContinue }: {
  report: ReportResponse; showFree?: boolean; onContinue: () => void;
}) {
  const offer = report.reading_offer;
  if (!offer) return null;
  const free = report.cuts.filter(cut => offer.free_ids.includes(cut.id));
  const core = report.locked.find(cut => cut.id === offer.core_id);
  const paid = offer.paid_ids.map(id => report.locked.find(cut => cut.id === id)).filter(cut => !!cut);
  return <section className="character-reading-offer" aria-label={`${report.lens.name}의 무료 풀이와 추가 해석`}>
    {showFree && free.length > 0 && <div className="character-free">
      <p className="entry-eyebrow">{report.lens.name}의 관점 · 무료로 읽는 {free.length}장</p>
      {free.map((cut, index) => <article key={cut.id}>
        <p className="entry-eyebrow">{String(index + 1).padStart(2, "0")} · 무료 전문</p>
        <h2>{cut.title}</h2>
        <div className="cutbody" dangerouslySetInnerHTML={{ __html: cut.html }} />
        <details className="entry-evidence"><summary>이 풀이의 계산 근거</summary><ServerText as="div" html={cut.source} /></details>
      </article>)}
    </div>}
    {offer.free_only && <p className="entry-selection">{report.lens.name}의 이야기는 무료예요. 이 자리에서는 추가 결제를 권하지 않아요.</p>}
    {/*
      ★ 마감에서 **앞을 깎지 않습니다.** 방금 읽은 것을 「맛보기」라 부르면
        좋았다고 느낀 손님에게 그 느낌이 작은 것이었다고 말하는 셈입니다.
        무료는 한 자도 줄이지 않고, 대신 **분모를 적습니다** — 스무 사람
        가운데 한 사람. 검증 불가능한 주장이 아니라 셈이라 가드를 지납니다.

      ★ 그리고 **손님의 반응을 손님보다 먼저 말합니다.** 무료에서 이미
        느낀 것을 되읽어 주지 않으면, 그 적중이 유료의 근거로 회수되지
        않고 그냥 지나갑니다.
    */}
    {report.sells && core && <div className="character-paid">
      <p className="entry-eyebrow">여기까지 읽고 나서</p>
      <h2>“이걸 어떻게 알았지” 싶은<br />대목이 있었을 거예요.</h2>
      <p>지어낸 말이 아니라 세어 본 값이에요. 근거 줄을 펴면 그 셈이 그대로 있어요.</p>
      <p>다만 여기까지는 <b>스무 사람 가운데 한 사람</b>, {report.lens.name}의 눈으로 센 것이에요. 같은 여덟 글자를 열아홉 사람이 저마다 다른 자리에서 봅니다.</p>
      <p className="entry-eyebrow">{report.lens.name}이 값을 치른 뒤에 답하는 질문</p><h2>{offer.question}</h2>
      <div className="character-core"><span>유료 핵심 장</span><h3>{core.title}</h3>
        {core.teaser && <ServerText as="div" html={core.teaser} />}
        <p className="entry-footnote">앞부분 미리보기 · 나머지 본문은 구매한 상품 범위에서 열려요.</p>
      </div>
      {/* 분량은 **서버가 셉니다.** 화면은 받아 적기만 합니다 (CLAUDE.md). */}
      <ul>{paid.slice(0, 4).map(cut => cut && <li key={cut.id}>{cut.title}
        <span>{cut.need_tier_name ?? cut.need_tier}부터 · {cut.chars.toLocaleString()}자</span></li>)}</ul>
      <span className="src">근거 · 접힌 자리는 <b>{report.locked.length}컷</b>,
        합쳐 <b>{report.locked.reduce((n, c) => n + c.chars, 0).toLocaleString()}자</b>요 ·
        컷 수와 분량은 서버가 세어 내려보낸 것이오 〔표시가와 청구가는 한 값〕</span>
      {paid.length > 4 && <details className="entry-evidence"><summary>이 해석자의 나머지 유료 목차 {paid.length - 4}개</summary>
        <ul>{paid.slice(4).map(cut => cut && <li key={cut.id}>{cut.title}</li>)}</ul></details>}
      {core.need_tier === "one" && typeof report.lens.price === "number" && report.lens.price > 0 &&
        <p className="character-offer-price">{report.lens.price.toLocaleString()}원 <small>이 해석자 · 한 번 결제</small></p>}
      {!SELLABLE && <p className="entry-footnote">현재 유료 판매를 준비하고 있어요. 무료 풀이는 계속 읽을 수 있어요.</p>}
      <button className="btn" onClick={onContinue}>포함 내용과 결제 조건 확인하기</button>
      <p className="entry-footnote">이 버튼으로 바로 결제되지 않아요. 무료로 읽은 내용은 계속 볼 수 있어요.</p>
    </div>}
  </section>;
}
