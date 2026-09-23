"use client";
import {useEffect} from 'react';
import {useSession} from '@/lib/store';
import {acceptMember,clearMember,useMember} from '@/lib/member';

export default function MemberSync(){
  useEffect(()=>{
    let alive=true;
    const sync=async()=>{
      try{
        const response=await fetch('/api/backend/v1/account/me',{cache:'no-store'});
        if(!alive)return;
        if(response.ok){const data=await response.json();if(alive)acceptMember(data.user);}
        else if(response.status===401){if(localStorage.getItem('sd.member-id'))clearMember();else useMember.setState({ready:true,user:null});}
        else useMember.setState({ready:true,saveError:'로그인 상태를 확인하지 못했습니다. 보관함에서 다시 시도해 주세요.'});
      }catch{if(alive)useMember.setState({ready:true,saveError:'보관함 연결을 확인하지 못했습니다.'});}
    };
    const unsubscribe=useSession.persist.onFinishHydration(()=>void sync());
    if(useSession.persist.hasHydrated())void sync();
    return()=>{alive=false;unsubscribe();};
  },[]);
  return null;
}
