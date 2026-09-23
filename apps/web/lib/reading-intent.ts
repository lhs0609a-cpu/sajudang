export type ReadingIntent = {chartId: string; lensId: string; concern: string; question: string; title: string; tier: string; tierId?: string; chapterId?: string; at: number};
const KEY = 'sd.reading-intent';
export function saveReadingIntent(intent: Omit<ReadingIntent, 'at'>) {
  try { sessionStorage.setItem(KEY, JSON.stringify({...intent, at: Date.now()})); } catch { /* Navigation still works without storage. */ }
}
export function loadReadingIntent(chartId: string | null, lensId: string, concern: string): ReadingIntent | null {
  try {
    const value = JSON.parse(sessionStorage.getItem(KEY) ?? 'null');
    if (value?.chartId !== chartId || value?.lensId !== lensId || value?.concern !== concern || Date.now() - value.at > 30 * 60 * 1000) return null;
    if (![value.question, value.title, value.tier].every(v => typeof v === 'string' && v.length > 0 && v.length < 400)) return null;
    return value;
  } catch { return null; }
}
