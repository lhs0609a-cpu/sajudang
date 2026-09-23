"use client";

import {useCallback, useEffect, useRef, useState} from "react";
import {usePathname, useSearchParams} from "next/navigation";

type Mode = "intro" | "scroll" | "choose" | "continue" | "done";
type GuideState = {mode:Mode; title:string; detail:string; progress:number};

const INITIAL:GuideState = {
  mode:"intro", title:"이 화면은 아래로 이어집니다",
  detail:"천천히 읽으세요. 멈추면 다음 행동을 다시 알려드립니다.", progress:0,
};

function usable(element:Element): element is HTMLElement {
  if (!(element instanceof HTMLElement) || element.closest(".sound-float,.journey-guide,.seats-shortcut,.live-activity,.top,.devrail")) return false;
  const rect=element.getBoundingClientRect();
  const style=getComputedStyle(element);
  return rect.width>8&&rect.height>8&&style.display!=="none"&&style.visibility!=="hidden";
}

function onScreen(element:HTMLElement){
  const rect=element.getBoundingClientRect();
  return rect.bottom>72&&rect.top<innerHeight-70;
}

function shortLabel(element:HTMLElement){
  return (element.innerText||element.getAttribute("aria-label")||"다음 단계").replace(/\s+/g," ").trim().slice(0,34);
}

export default function JourneyGuide(){
  const pathname=usePathname();
  const params=useSearchParams();
  const routeKey=pathname+"?"+params.toString();
  const [guide,setGuide]=useState<GuideState>(INITIAL);
  const [visible,setVisible]=useState(false);
  const targetRef=useRef<HTMLElement|null>(null);
  const timerRef=useRef<ReturnType<typeof setTimeout>|null>(null);
  const introRef=useRef(true);

  // A long report needs quiet reading time. Short input screens can be guided
  // sooner, but never immediately after paint or a tap.
  const idleDelay=useCallback(()=>{
    const root=document.querySelector(".phone .scr")||document.querySelector("main")||document.body;
    const text=(root.textContent||"").replace(/\s+/g,"");
    const long= document.documentElement.scrollHeight>innerHeight*1.7 || text.length>2200;
    return long ? 6500 : 3800;
  },[]);

  const clearTarget=useCallback(()=>{
    targetRef.current?.classList.remove("journey-target");
    targetRef.current=null;
  },[]);

  const inspect=useCallback(()=>{
    clearTarget();
    const root=(document.querySelector(".phone .scr")||document.querySelector("main")||document.body) as HTMLElement;
    const doc=document.documentElement;
    const max=Math.max(0,doc.scrollHeight-innerHeight);
    const progress=max?Math.min(100,Math.round(scrollY/max*100)):100;

    // The first inspection is content-aware too. A generic welcome card here
    // used to cover the opening sentence before the reader had a chance to
    // understand the page.
    introRef.current=false;

    const primaries=Array.from(root.querySelectorAll<HTMLElement>(
      "button.btn:not(.gh),a.btn:not(.gh),button.go,a.go,input[type=submit]"))
      .filter(usable);
    const enabled=primaries.filter(el=>!(el instanceof HTMLButtonElement||el instanceof HTMLInputElement)||!el.disabled);
    const visibleAction=enabled.find(onScreen);
    if(visibleAction){
      targetRef.current=visibleAction;visibleAction.classList.add("journey-target");
      const label=shortLabel(visibleAction);
      setGuide({mode:"continue",title:"다음 단계 버튼이 보입니다",detail:`「${label}」을 직접 눌러 진행하세요.`,progress});
      setVisible(true);return;
    }

    const blocked=primaries.find(el=>((el instanceof HTMLButtonElement||el instanceof HTMLInputElement)&&el.disabled)&&onScreen(el));
    if(blocked){
      const choices=Array.from(root.querySelectorAll<HTMLElement>("button[aria-pressed],input,select,textarea")).filter(usable);
      targetRef.current=choices.find(onScreen)||choices[0]||blocked;
      targetRef.current?.classList.add("journey-target");
      const hasFields=choices.some(el=>el.matches("input,select,textarea"));
      setGuide({mode:"choose",title:hasFields?"먼저 정보를 채워 주세요":"먼저 하나씩 선택해 주세요",detail:"필수 항목을 마치면 다음 버튼이 열립니다.",progress});
      setVisible(true);return;
    }

    const more=scrollY+innerHeight<doc.scrollHeight-110;
    if(more){
      setGuide({mode:"scroll",title:"아래로 내려 다음 판정 읽기",detail:"누르면 다음 제목이나 선택 버튼까지 바로 이동합니다.",progress});
    }else{
      setGuide({mode:"done",title:"이 화면을 모두 읽었습니다",detail:"마지막 선택지나 이동 버튼을 확인해 보세요.",progress:100});
    }
    setVisible(true);
  },[clearTarget]);

  const schedule=useCallback((delay?:number)=>{
    if(timerRef.current)clearTimeout(timerRef.current);
    setVisible(false);
    timerRef.current=setTimeout(inspect,delay ?? idleDelay());
  },[idleDelay,inspect]);

  useEffect(()=>{
    introRef.current=true;clearTarget();schedule(7000);
    const activity=()=>schedule();
    const keys=(event:KeyboardEvent)=>{if(["ArrowDown","ArrowUp","PageDown","PageUp"," "].includes(event.key))activity();};
    addEventListener("scroll",activity,{passive:true});
    addEventListener("pointerdown",activity,{passive:true});
    addEventListener("keydown",keys);
    const observer=new MutationObserver(mutations=>{
      // The guide highlights targets by changing classes. Observing `class`
      // here would make the guide wake itself forever.
      if(mutations.every(mutation=>(mutation.target as Element).closest?.(".journey-guide,.sound-float")))return;
      schedule(idleDelay()+500);
    });
    observer.observe(document.body,{childList:true,subtree:true,attributes:true,attributeFilter:["disabled","aria-pressed"]});
    return()=>{
      if(timerRef.current)clearTimeout(timerRef.current);
      removeEventListener("scroll",activity);removeEventListener("pointerdown",activity);removeEventListener("keydown",keys);
      observer.disconnect();clearTarget();
    };
  },[routeKey,schedule,clearTarget,idleDelay]);

  const act=()=>{
    if(guide.mode==="scroll"){
      const root=(document.querySelector(".phone .scr")||document.querySelector("main")||document.body) as HTMLElement;
      const landmarks=Array.from(root.querySelectorAll<HTMLElement>("section,h1,h2,h3,.blk,.conversion-card,.reading-section,.extraask,.btn"))
        .filter(usable).filter(el=>el.getBoundingClientRect().top>innerHeight*.62);
      const next=landmarks[0];
      if(next)next.scrollIntoView({behavior:"smooth",block:"start"});
      else scrollBy({top:innerHeight*.72,behavior:"smooth"});
    }else if(targetRef.current){
      targetRef.current.scrollIntoView({behavior:"smooth",block:"center"});
      targetRef.current.classList.remove("journey-target");
      requestAnimationFrame(()=>targetRef.current?.classList.add("journey-target"));
    }else if(guide.mode==="intro"){
      scrollBy({top:Math.min(320,innerHeight*.38),behavior:"smooth"});
    }
    schedule(3000);
  };

  return <aside className={`journey-guide ${visible?"show":""} mode-${guide.mode}`} aria-live="polite" aria-label="화면 진행 안내">
    <div className="journey-guide-head"><span>진행 가이드</span><b>{guide.progress}%</b></div>
    <button type="button" onClick={act} aria-label={`${guide.title}. ${guide.detail}`}>
      <span className="journey-guide-icon" aria-hidden="true">{guide.mode==="scroll"||guide.mode==="intro"?"↓":guide.mode==="choose"?"◆":guide.mode==="continue"?"→":"✓"}</span>
      <span><strong>{guide.title}</strong><small>{guide.detail}</small></span>
    </button>
    <span className="journey-guide-track" aria-hidden="true"><i style={{width:`${guide.progress}%`}}/></span>
  </aside>;
}
