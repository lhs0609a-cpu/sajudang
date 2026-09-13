"use client";
import { useEffect, useState } from 'react';
const KEY='sd.reading-preferences';

export default function ReadingControls({reveal}: {reveal:()=>void}) {
  const [instant,setInstant]=useState(false);
  const [large,setLarge]=useState(false);
  useEffect(()=>{
    try {const v=JSON.parse(localStorage.getItem(KEY)||'{}');setInstant(v.instant===true);setLarge(v.large===true);
      document.documentElement.dataset.readingMode=v.instant?'instant':'story';
      document.documentElement.dataset.readingSize=v.large?'large':'normal';
      if(v.instant)reveal();
    } catch { /* No personal data required. */ }
  },[reveal]);
  function change(nextInstant:boolean,nextLarge:boolean){
    setInstant(nextInstant);setLarge(nextLarge);
    document.documentElement.dataset.readingMode=nextInstant?'instant':'story';
    document.documentElement.dataset.readingSize=nextLarge?'large':'normal';
    try{localStorage.setItem(KEY,JSON.stringify({instant:nextInstant,large:nextLarge}));}catch{/* Applies to this page. */}
    if(nextInstant)reveal();
  }
  return <div className="reading-controls noprint" role="group" aria-label="읽기 설정">
    <button type="button" aria-pressed={instant} onClick={()=>change(!instant,large)}>{instant?'바로 읽기 켜짐':'기다리지 않고 바로 읽기'}</button>
    <button type="button" aria-pressed={large} onClick={()=>change(instant,!large)}>{large?'큰 글자 켜짐':'글자 크게'}</button>
  </div>;
}
