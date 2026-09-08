"use client";
import { useEffect } from 'react';
import { onCLS, onINP, onLCP } from 'web-vitals';
import { flush, track } from '@/lib/track';
let installed=false;
export default function WebVitals() {
  useEffect(()=>{
    if(installed || window.location.pathname !== '/')return;installed=true;
    onLCP(m=>{track('web_lcp','a1',{ms:Math.round(m.value)});flush();});
    onINP(m=>{track('web_inp','a1',{ms:Math.round(m.value)});flush();});
    onCLS(m=>{track('web_cls','a1',{ms:Math.round(m.value*1000)});flush();});
  },[]);
  return null;
}
