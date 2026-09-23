"use client";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useMember, clearMember, memberCall } from "@/lib/member";
import { useSession } from "@/lib/store";
export default function AccountBar(){
 const router=useRouter(); const user=useMember(s=>s.user), ready=useMember(s=>s.ready);
 const fresh=()=>{useSession.getState().reset();router.push("/");};
 const logout=async()=>{try{await memberCall("/logout",{});}catch{} clearMember();router.push("/");};
 return <nav className="account-bar" aria-label="계정 메뉴">{!ready?<Link href="/me" className="account-bar-link muted">계정 확인 중</Link>:user?<><span className="account-bar-user">{user.username}</span><Link href="/me" className="account-bar-link">보관함</Link><button type="button" className="account-bar-link" onClick={fresh}>새로 시작</button><button type="button" className="account-bar-link" onClick={logout}>로그아웃</button></>:<><Link href="/me?mode=login" className="account-bar-link">로그인</Link><Link href="/me?mode=signup" className="account-bar-link signup">회원가입</Link></>}</nav>;
}
