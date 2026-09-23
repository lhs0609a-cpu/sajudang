import Link from "next/link";
import Image from "next/image";

/** 20자리 바로 위에 고정되는 추가 운세 분석 진입점. */
export default function FortuneShortcut() {
  return (
    <nav className="fortune-shortcut noprint" aria-label="대운 세운 월운 궁합 상세 분석">
      <Link href="/fortune" aria-label="대운 세운 월운 궁합 상세 분석 보기">
        <Image src="/images/reading/direction-v1.webp" alt="" width={44} height={44} sizes="44px" />
        <span className="fortune-shortcut-copy">
          <b>대운 · 세운 · 월운 · 궁합</b>
          <small>내 명식의 다음 흐름을 더 깊게 보기</small>
        </span>
        <span className="fortune-shortcut-arrow" aria-hidden="true">→</span>
      </Link>
    </nav>
  );
}
