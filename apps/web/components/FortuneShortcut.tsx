import Link from "next/link";
import Image from "next/image";

/** 20자리 바로 위에 고정되는 추가 운세 분석 진입점. */
export default function FortuneShortcut() {
  return (
    <nav className="fortune-shortcut noprint" aria-label="대운 세운 월운 궁합 상세 분석">
      <Link href="/fortune" aria-label="대운 세운 월운 궁합 상세 분석 보기">
        <Image src="/images/fortune-flow-v1.webp" alt="" width={42} height={42} sizes="42px" />
        <span className="fortune-shortcut-copy">
          <b>운세 분석</b>
          <small>대운 · 세운 · 월운 · 궁합</small>
        </span>
        <span className="fortune-shortcut-arrow" aria-hidden="true">→</span>
      </Link>
    </nav>
  );
}
