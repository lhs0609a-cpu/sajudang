"use client";

import type { CSSProperties, ReactNode } from 'react';
import { LENS_BY_ID } from '@/lib/lenses';
import { useSession } from '@/lib/store';
import CharacterSpeech from './CharacterSpeech';

/** Keep the speaking character explicit, including reports opened by URL. */
export function ReadingSpeaker({lensId, label = '함께 짚어볼 이야기', soft = false}: {lensId?: string; label?: string; soft?: boolean}) {
  const selected = useSession(s => s.cur);
  const lens = LENS_BY_ID[lensId ?? selected] ?? LENS_BY_ID.pungun;
  return <div className="reading-speaker" data-speaker={lens.id}>
    <img key={`${lens.id}:${soft}`} src={`/char/${lens.id}/${soft ? 'bust_soft' : 'bust'}.webp`}
      width={76} height={88} alt="" loading="lazy" decoding="async"
      onError={e => {const img = e.currentTarget; if (!img.dataset.fallback) {img.dataset.fallback = 'true'; img.src = `/char/${lens.id}/bust.webp`;}}} />
    <div><CharacterSpeech lensId={lens.id}><span>{label}</span></CharacterSpeech><strong>{lens.name}</strong><small>{lens.specialty}</small></div>
  </div>;
}

export default function ReadingVoice({lensId, children, label, soft = false}: {lensId?: string; children: ReactNode; label?: string; soft?: boolean}) {
  const selected = useSession(s => s.cur);
  const lens = LENS_BY_ID[lensId ?? selected] ?? LENS_BY_ID.pungun;
  const style = {'--reading-portrait': `url("/char/${lens.id}/bust.webp")`, '--reading-accent': lens.color} as CSSProperties;
  return <div className="reading-voice" style={style}>
    <ReadingSpeaker lensId={lens.id} label={label} soft={soft} />
    <div className="reading-voice-body"><CharacterSpeech lensId={lens.id}>{children}</CharacterSpeech></div>
  </div>;
}
