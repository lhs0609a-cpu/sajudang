import Link from 'next/link';
import Image from 'next/image';

export default function SeatsShortcut() {
  return <nav className="seats-shortcut noprint" aria-label="해석자 바로가기">
    <Link href="/lobby?tab=b2" aria-label="20자리 보기 · 모든 해석자 둘러보기">
      <span className="seats-shortcut-faces" aria-hidden="true">
        {['pungun', 'jeokhyeol', 'baegun'].map(id => <Image key={id} src={`/char/${id}/bust.webp`} alt="" width={36} height={36} sizes="36px" />)}
      </span>
      <span>20자리 보기</span>
    </Link>
  </nav>;
}
