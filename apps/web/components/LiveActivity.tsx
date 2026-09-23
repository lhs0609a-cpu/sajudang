'use client';

import { useEffect, useState } from 'react';
import { usePathname } from 'next/navigation';
import { analyticsId } from '@/lib/track';

type Notice = {id:string; minutes_ago:number; text:string};

/** No sample visitors or purchases. Silence is the empty/error state. */
export default function LiveActivity() {
  const path = usePathname();
  const [count, setCount] = useState(0);
  const [notice, setNotice] = useState<Notice | null>(null);
  const [hidden, setHidden] = useState(false);
  const screen = path === '/' ? 'entry' : path === '/lobby' ? 'seats' : path.startsWith('/report/') ? 'reading' : null;
  useEffect(() => {
    setCount(0); setNotice(null);
    try {setHidden(!!sessionStorage.getItem('sd.activity.dismissed'));} catch {}
    const visitor = analyticsId();
    if (!screen || !visitor) return;
    let disposed = false;
    let dismissTimer: ReturnType<typeof setTimeout>;
    const abort = new AbortController();
    const poll = async () => {
      if (document.visibilityState !== 'visible') {setCount(0); setNotice(null); return;}
      try {
        const response = await fetch('/api/backend/v1/activity', {method:'POST', headers:{'Content-Type':'application/json'},
          body:JSON.stringify({visitor,screen}), signal:abort.signal, cache:'no-store'});
        if (!response.ok) throw new Error('unavailable');
        const data = await response.json();
        if (disposed) return;
        setCount(Number.isInteger(data.active_browsers) ? data.active_browsers : 0);
        if (sessionStorage.getItem('sd.activity.dismissed')) return;
        const seen: string[] = JSON.parse(sessionStorage.getItem('sd.activity.seen') || '[]');
        const last = Number(sessionStorage.getItem('sd.activity.last') || 0);
        if (seen.length >= 3 || Date.now() - last < 60000) return;
        const next = (data.purchases as Notice[]).find(row => !seen.includes(row.id));
        if (!next) return;
        sessionStorage.setItem('sd.activity.seen', JSON.stringify([...seen, next.id]));
        sessionStorage.setItem('sd.activity.last', String(Date.now()));
        setNotice(next);
        clearTimeout(dismissTimer);
        dismissTimer = setTimeout(() => setNotice(null), 7000);
      } catch {if (!disposed) {setCount(0); setNotice(null);}}
    };
    void poll();
    const timer = setInterval(poll, 30000);
    document.addEventListener('visibilitychange', poll);
    return () => {disposed = true; abort.abort(); clearInterval(timer); clearTimeout(dismissTimer); document.removeEventListener('visibilitychange', poll);};
  }, [screen]);
  if (!screen || hidden || (!notice && count < 2)) return null;
  return <aside className="live-activity" aria-label="실제 이용 현황">
    <button type="button" className="live-activity-close" aria-label="이용 현황 알림 끄기" onClick={() => {
      setHidden(true); try {sessionStorage.setItem('sd.activity.dismissed', '1');} catch {}
    }}>×</button>
    {notice && <p role="status"><strong>{notice.text}</strong><small>{notice.minutes_ago < 1 ? '1분 이내' : `${notice.minutes_ago}분 전`} · 실제 결제 승인 기준</small></p>}
    {count >= 2 && <p><span className="live-activity-dot" />최근 1분 이 화면 접속 <strong>{count.toLocaleString()}개</strong><small>브라우저 기준 · 30초마다 갱신</small></p>}
  </aside>;
}
