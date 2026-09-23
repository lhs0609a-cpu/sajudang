/** Decorative masking only: the paid text is never passed to this component. */
export default function LockedVeil() {
  return <div className="locked-veil" aria-label="원인과 선택 기준을 가르는 결론은 구매 후 열립니다">
    <div className="locked-veil-lines" aria-hidden="true"><i /><i /><i /></div>
    <span className="locked-veil-label"><svg width="16" height="18" viewBox="0 0 16 18" fill="none" aria-hidden="true"><rect x="2" y="8" width="12" height="9" rx="2" stroke="currentColor" /><path d="M5 8V5a3 3 0 0 1 6 0v3" stroke="currentColor" /></svg> 반복 원인 · 선택 기준 · 오늘 행동은 구매 후 공개</span>
  </div>;
}
