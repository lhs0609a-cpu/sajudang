"use client";
import React from 'react';
import { useSession } from '@/lib/store';
import { characterText } from '@/lib/character-voice';
import { usePathname } from 'next/navigation';

/** Transform authored dialogue before rendering; never mutate the DOM or form values. */
export function speechNodes(node:React.ReactNode,lensId:string,name:string,sex:'M'|'F'):React.ReactNode {
  if(typeof node==='string')return characterText(node,lensId,name,sex);
  if(Array.isArray(node))return node.map((item,i)=><React.Fragment key={i}>{speechNodes(item,lensId,name,sex)}</React.Fragment>);
  if(!React.isValidElement(node))return node;
  // Custom components own their speaker. User controls and quoted examples are UI, not the character.
  if(typeof node.type!=='string'&&node.type!==React.Fragment)return node;
  if(['button','input','textarea','select','option','code','pre','q'].includes(node.type as string))return node;
  const el=node as React.ReactElement<{children?:React.ReactNode;dangerouslySetInnerHTML?:{__html:string};'data-voice-fixed'?:boolean}>;
  if(el.props['data-voice-fixed']||el.props.dangerouslySetInnerHTML)return node;
  return React.cloneElement(el,{},speechNodes(el.props.children,lensId,name,sex));
}
export default function CharacterSpeech({children,lensId}:{children:React.ReactNode;lensId?:string}){
  const s=useSession();
  const path=usePathname();
  const reportLens=path.startsWith('/report/')?path.split('/')[2]:undefined;
  return <>{speechNodes(children,lensId??reportLens??s.cur,s.name,s.sex)}</>;
}
