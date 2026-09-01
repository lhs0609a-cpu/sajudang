"use client";

/**
 * 첫 대면 — 도령의 얼굴이 처음으로 크게 나오는 자리.
 *
 * ★ 왜 필요한가
 *
 *   이 집이 파는 것은 해석이 아니라 **그 사람**입니다. 스무 명이 각자의
 *   관점으로 본다는 것이 이 서비스의 한 줄인데, 손님은 일곱 화면을
 *   지나도록 그 사람의 얼굴을 한 번도 못 봤습니다. 배경과 글자뿐이었고
 *   초상은 진열대(b2)에서야 나왔습니다 — 결제 갈림길 **뒤**입니다.
 *
 *   얼굴을 보고 나서 값을 치를지 정하는 것이지, 값을 치를 마음을 먹은
 *   뒤에 얼굴을 보는 게 아닙니다.
 *
 * ★ 왜 하필 a4 인가
 *
 *   a4 의 첫 줄이 「도령이 고개를 들었다」입니다. 고개를 드는데 얼굴이
 *   없으면 그 문장이 거짓말입니다. 글이 이미 그 자리를 가리키고
 *   있었는데 그림만 없었습니다.
 *
 * ★ 그림이 없으면 어떻게 되나
 *
 *   자리표시로 자리만 잡습니다. 반쯤 그린 얼굴은 없는 것보다 나쁘므로
 *   흉내내지 않습니다 (CharArt 와 같은 규칙). 그림이 오는 날
 *   `public/char/{id}/bust.png` 에 넣기만 하면 그때부터 나옵니다.
 */
import CharArt from "@/components/CharArt";
import { LENS_BY_ID } from "@/lib/lenses";
import { useSession } from "@/lib/store";

export default function Meet({ lens, note }: {
  /** 누구를 만나는가. 없으면 지금 고른 캐릭터. */
  lens?: string;
  /** 이름 아래 한 줄. 없으면 그 사람의 전문 분야. */
  note?: string;
}) {
  const cur = useSession((s) => s.cur);
  const l = LENS_BY_ID[lens ?? cur];
  if (!l) return null;

  return (
    <div className="meet" style={{ ["--c" as string]: l.color }}>
      <div className="meetart">
        <CharArt lens={l} size="full" />
      </div>
      <div className="meetname">
        <b>{l.name}</b>
        <i>{l.hanja}</i>
      </div>
      <div className="meetnote">{note ?? l.specialty}</div>
    </div>
  );
}
