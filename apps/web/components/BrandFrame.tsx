import Link from "next/link";

export function chapter(screen?: string) {
  if (!screen || screen === "a1") return {number:"序",name:"이야기의 문을 열다",line:"마음에 오래 남은 질문을 들고 오시오."};
  if (["a2","a3","a4","a4b","a5","a6"].includes(screen)) return {number:"一",name:"그대의 이야기를 듣다",line:"태어난 순간에서, 지금의 고민으로."};
  if (["a7","d0"].includes(screen)) return {number:"二",name:"마음의 결을 읽다",line:"익숙한 패턴에, 새로운 질문 하나."};
  if (screen.startsWith("b") || screen === "h1") return {number:"三",name:"다른 시선을 만나다",line:"같은 여덟 글자. 저마다 다른 스무 시선."};
  if (screen.startsWith("d")) return {number:"四",name:"한 겹 더 깊이 읽다",line:"무엇이 열리는지 살펴보고 결정하시오."};
  if (screen.startsWith("f")) return {number:"藏",name:"그대의 이야기를 간직하다",line:"다시 펼치고 싶은 문장을 모아 두었소."};
  if (screen.startsWith("g")) return {number:"日",name:"오늘의 한 줄을 읽다",line:"먼 훗날보다, 오늘의 작은 선택부터."};
  return {number:"讀",name:"나를 읽는 시간",line:"답을 서두르지 말고, 한 장씩 펼쳐 보시오."};
}

export default function BrandFrame({screen}:{screen?:string}) {
  const part=chapter(screen);
  return <aside className="brand-rail" aria-label="성신당 이야기">
    <Link className="brand-signature" href="/?step=a1"><span className="brand-seal" aria-hidden="true">星<br/>辰</span><span>성신당<small>별에 묻고, 나를 읽다</small></span></Link>
    <div className="brand-orbit" aria-hidden="true"><i/><i/><i/><b>星 辰 堂</b><span>✦</span></div>
    <div className="brand-rail-copy"><span className="brand-overline">그대만의 이야기를 펼치는 곳</span><h2>마음이 머문 곳에<br/>별 하나를 켜두오.</h2><p>태어난 순간을 읽고,<br/>오늘의 나를 바라보오.</p></div>
    <div className="brand-chapter"><span>{part.number}</span><div><strong>{part.name}</strong><p>{part.line}</p></div></div>
    <p className="brand-colophon">전통 사주로 읽는 자기 이해 · 성신당</p>
  </aside>;
}

export function FolioLabel({screen,title}:{screen?:string;title?:string}) {
  const part=chapter(screen);
  return <div className="folio-label"><span>星辰堂 <i>성신당</i></span><span>{title || part.name}</span></div>;
}
