"use client";
import type { WantRow } from '@shared/chart';
import { useSession } from '@/lib/store';
import ServerText from '@/components/ServerText';
import LockedVeil from '@/components/LockedVeil';

const TURNS: Record<string, { question: string; reveal: string }> = {
  재물: { question: '다만, 돈을 좇는 힘과 내 몫으로 남기는 힘은 같지 않소.', reveal: '내 사주가 재물을 감당하는 방식과 그 이유' },
  사랑: { question: '끌리는 마음 뒤에, 가까워질수록 드러나는 내 모습은 어떻소?', reveal: '배우자 자리로 읽는 가까운 관계의 모습' },
  운명: { question: '다음 나이는 보였소. 그렇다면 그때는 무엇이 달라지는 것이오?', reveal: '대운의 흐름과 시기별 해석' },
  사람: { question: '같은 성향이 어떤 관계에서는 힘이 되고, 어떤 관계에서는 짐이 되는 까닭은?', reveal: '사람과의 관계를 읽는 명식의 단서' },
};

/*
 * 네 자리 — 재물 · 사랑 · 운명 · 사람.
 *
 * ★ 서버가 내려보내는데 **그리는 화면이 없었습니다** (2026-09-21).
 *
 *   `routers/report` 가 `wants` 를 만들어 응답에 실어 보낸 지 오래인데
 *   (`engine/peek.build_wants`), 앱 어느 파일에서도 그 낱말을 읽지
 *   않고 있었습니다. 손님이 값을 치를지 정하는 그 자리에서, 이 집이
 *   가진 가장 센 장치가 **한 번도 안 켜졌다**는 뜻이오.
 *
 * ★ 흐린 것이 아니라 여기 없습니다.
 *
 *   `head` 까지는 **진짜 글**이오. 그 뒤는 글자가 아예 안 내려옵니다 —
 *   `mask` 는 가린 **글자 수**일 뿐입니다. 화면에서 CSS 로 뭉개는
 *   흉내가 아니라, 브라우저를 뒤져도 없는 글입니다. 문장 뱅크를
 *   클라이언트로 안 보낸다는 규칙이 여기서도 그대로요 (CLAUDE.md).
 *
 * ★ 여는 사실(`fact`)은 **센 값**입니다.
 *
 *   「재물 글자가 3개 있소」 는 손님이 만세력을 펴고 대 볼 수 있는
 *   말이오. 틀릴 수 있는 말이라야 맞았을 때 소름이 돋소. 근거 줄도
 *   가리지 않습니다 — 근거는 보이되 규칙만 감춥니다.
 */
export default function Wants({ rows, onOpen }: { rows: WantRow[]; onOpen?: () => void }) {
  const concern = useSession(s => s.concern);
  const category: Record<string,string> = {money:'재물',love:'사랑',people:'사람',work:'운명',dir:'운명'};
  const relevant = (rows ?? []).filter(r => r.want === category[concern]).slice(0,1);
  if (!relevant.length) return null;
  return <section className="wants" aria-label="아직 안 편 네 자리">
    <p className="conversion-kicker">아직 안 편 자리</p>
    <h2>여기까지 읽고도<br />마음에 남는 한 가지.</h2>
    <p className="conversion-note">보이는 글자는 시작이오. 그 글자가 그대 삶에서 어떤 뜻으로 읽히는지, 다음 풀이에서 이어지오.</p>
    {relevant.map((r) => (
      <article className="want" key={r.want}>
        <h3 className="want-name">{r.want}</h3>
        <ServerText as="p" className="want-fact" html={r.fact} />
        {TURNS[r.want] && <p className="want-turn">{TURNS[r.want].question}</p>}
        <p className="want-ask">{r.ask}</p>
        <p className="want-head">
          {r.head}
          <span aria-hidden="true"> …</span>
        </p>
        <LockedVeil />
        <p className="want-len">{TURNS[r.want]?.reveal ?? '이 질문에 이어지는 해석과 근거'}</p>
        {r.source && <ServerText as="span" className="src" html={`근거 · ${r.source}`} />}
        {onOpen && <button className="btn" onClick={onOpen}>{r.want}의 이어지는 해석 · 구성과 가격 보기</button>}
      </article>
    ))}
  </section>;
}
