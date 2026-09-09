import type { ReportCut } from '@shared/chart';

export const READING_QUESTIONS: Record<string,string> = {
  money:'버는 힘과 남기는 힘은 왜 다르오?',
  work:'잘하는 일이 왜 나를 지치게 하오?',
  love:'마음을 줬는데, 왜 같은 곳에서 서운하오?',
  people:'좋은 사람이 되려다 내 몫을 놓치지는 않소?',
  dir:'선택 앞에서 늘 같은 이유로 멈추는 것이오?',
  health:'하루를 버티는 힘과 회복하는 틈은 다르오.',
};

/** Use actual free report text; never invent a personalized claim for the teaser. */
export function readingText(html: string) {
  return html.replace(/<i\b[^>]*class=["']gl["'][^>]*>[\s\S]*?<\/i>/gi,'')
    .replace(/<\/?(?:p|div|br|li|section)\b[^>]*>/gi,' ').replace(/<[^>]+>/g,'').replace(/&nbsp;/g,' ').replace(/&amp;/g,'&')
    .replace(/&quot;/g,'"').replace(/&#39;/g,"'").replace(/\s+/g,' ').trim();
}
export function freeRevelation(cuts: ReportCut[]) {
  const cut=cuts.find(c=>c.id==='why');
  if (!cut) return null;
  const bite=cut.html.match(/<p\b[^>]*class=["'][^"']*\bbite\b[^"']*["'][^>]*>([\s\S]*?)<\/p>/i)?.[1];
  if (!bite) return null;
  const marked=bite.match(/<mark\b[^>]*>([\s\S]*?)<\/mark>/i);
  const title=readingText(marked?.[1] ?? bite);
  const body=marked ? readingText(bite.replace(marked[0],'')) : '';
  return {title,body,source:readingText(cut.source)};
}
