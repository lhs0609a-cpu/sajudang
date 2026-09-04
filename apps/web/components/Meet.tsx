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
import { useState } from "react";
import CharArt from "@/components/CharArt";
import { LENS_BY_ID } from "@/lib/lenses";
import { useSession } from "@/lib/store";

export default function Meet({ lens, note, nameOnly, greet }: {
  /** 누구를 만나는가. 없으면 지금 고른 캐릭터. */
  lens?: string;
  /** 이름 아래 한 줄. 없으면 그 사람의 전문 분야. */
  note?: string;
  /**
   * ★ 초상은 장면이 이미 세웠고 여기서는 **이름만** 낸다.
   *   같은 얼굴을 두 번 그리면 두 사람으로 보입니다.
   */
  nameOnly?: boolean;
  /**
   * 처음 만나는 자리인가.
   *
   * ★ 참이면 **소리까지 있는 인사**가 한 번 돕니다 (CharArt.greet).
   *   이 집에서 도령이 손님에게 말을 거는 첫 순간이라, 여기서만
   *   소리를 냅니다 — 뒤에 또 나오면 인사가 아니라 배경음입니다.
   */
  greet?: boolean;
}) {
  const cur = useSession((s) => s.cur);
  /*
   * ★ 소리 스위치는 여기 삽니다 — 초상 **밖**입니다.
   *
   *   `.meetart` 도 `.charart` 도 네 변을 마스크로 녹입니다. 초상이
   *   네모로 잘려 보이면 스티커가 되기 때문입니다. 그런데 마스크는
   *   그 안의 것을 다 녹여서, 귀퉁이에 단추를 얹으면 단추도 같이
   *   사라집니다. 그래서 이름 아래, 마스크가 안 닿는 자리에 둡니다.
   *
   *   브라우저가 막기 전에는 **안 보입니다.** 소리는 이미 나고 있고,
   *   끌 일이 있는 사람만 손을 뻗으면 되니 그때 나옵니다.
   */
  const [on, setOn] = useState(true);
  const [blocked, setBlocked] = useState(false);
  const l = LENS_BY_ID[lens ?? cur];
  if (!l) return null;

  return (
    <div className="meet" style={{ ["--c" as string]: l.color }}>
      {!nameOnly && (
        <div className="meetart">
          <CharArt lens={l} size="full" greet={greet}
                   soundOn={on} onSoundBlocked={() => {
                     setBlocked(true); setOn(false);
                   }} />
        </div>
      )}
      <div className="meetname">
        <b>{l.name}</b>
        <i>{l.hanja}</i>
      </div>
      <div className="meetnote">{note ?? l.specialty}</div>
      {greet && (blocked || on) && (
        <button type="button" className="sndline"
                onClick={() => { setBlocked(false); setOn(!on); }}>
          {on ? "소리를 끄겠습니다" : "소리를 듣겠습니다"}
        </button>
      )}
    </div>
  );
}
