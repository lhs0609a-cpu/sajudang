import Link from "next/link";
import Shell from "@/components/Shell";
import CompanionCat from "@/components/CompanionCat";

export default function NotFound(){
  return <Shell title="이야기를 다시 찾다"><header className="editorial-heading"><p className="conversion-kicker">찾을 수 없는 페이지</p><h1>이곳의 등불은<br/>아직 켜지지 않았소.</h1><p>주소가 바뀌었거나 더는 열 수 없는 페이지요.<br/>대문에서 다시 길을 찾아보시오.</p></header><CompanionCat message="길을 잃었다면, 내가 대문까지 함께 가겠소."/><Link className="btn mt" href="/?step=a1">성신당 대문으로</Link></Shell>;
}
