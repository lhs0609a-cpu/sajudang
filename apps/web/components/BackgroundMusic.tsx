"use client";
import {useEffect} from 'react';
import {BGM_TRACK,enableSound,playBgm,soundState} from '@/lib/sound';
import SoundToggle from '@/components/SoundToggle';

/** Root layout survives navigation, keeping the same audio source alive. */
export default function BackgroundMusic(){
  useEffect(()=>{
    playBgm(BGM_TRACK);
    const resume=()=>{if(soundState()==='on')enableSound();};
    window.addEventListener('pointerdown',resume);
    window.addEventListener('keydown',resume);
    return()=>{window.removeEventListener('pointerdown',resume);window.removeEventListener('keydown',resume);};
  },[]);
  return <div className="sound-float noprint" role="region" aria-label="배경 음악 설정">
    <SoundToggle />
  </div>;
}
