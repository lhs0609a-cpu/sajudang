"use client";
import {create} from 'zustand';
import {useSession} from './store';
import type {ReportResponse} from '@shared/chart';

export type Member={id:string;username:string;session_id:string};
export const useMember=create<{user:Member|null;ready:boolean;saveError:string|null}>(()=>({user:null,ready:false,saveError:null}));
const BASE='/api/backend/v1/account';
let hydratePromise:Promise<void>|null=null;
export async function memberCall<T=any>(path:string,body?:unknown,method?:string):Promise<T>{
  const response=await fetch(BASE+path,{method:method??(body?'POST':'GET'),headers:{'Content-Type':'application/json'},body:body?JSON.stringify(body):undefined,cache:'no-store'});
  const data=await response.json();
  if(!response.ok)throw new Error(data.detail||'보관함을 불러오지 못했습니다.');
  return data;
}
export function acceptMember(user:Member){
  const previous=localStorage.getItem('sd.member-id');
  if(previous && previous!==user.id)useSession.getState().reset();
  localStorage.setItem('sd.member-id',user.id);
  useSession.getState().set({sessionId:user.session_id});
  useMember.setState({user,ready:true,saveError:null});
}
export function clearMember(){
  localStorage.removeItem('sd.member-id');sessionStorage.removeItem('sd.reading-intent');
  Object.keys(sessionStorage).filter(key=>key.startsWith('sd.checkout')).forEach(key=>sessionStorage.removeItem(key));
  useSession.getState().reset();useMember.setState({user:null,ready:true,saveError:null});
  saved.clear();
}
export function hydrateMember(){
  if (hydratePromise) return hydratePromise;
  hydratePromise=memberCall<{user:Member}>('/me')
    .then(data=>acceptMember(data.user))
    .catch(()=>useMember.setState({ready:true}))
    .finally(()=>{hydratePromise=null;});
  return hydratePromise;
}
const saved=new Map<string,Promise<unknown>>();
export async function saveCurrentReading(report?:ReportResponse){
  const member=useMember.getState().user,s=useSession.getState();
  if(!member || !s.chartId || !s.year || !s.month || !s.day)return;
  if(report && report.chart_id!==s.chartId)return;
  // Account linking must not silently open a paid report before the reader does.
  const lens=report?.lens.id??s.cur,concern=report?.concern??s.concern,tier=report?.tier??'free';
  const key=[member.id,s.chartId,lens,concern,s.axis4,tier,new Date().toDateString()].join(':');
  if(saved.has(key))return saved.get(key);
  const topic=s.topicPick?.concern===concern&&s.topicPick.choice
    ? {choice:s.topicPick.choice,...(s.topicPick.choice2?{choice2:s.topicPick.choice2}:{}),...(s.topicPick.choice3?{choice3:s.topicPick.choice3}:{}),...(s.topicPick.choice4?{choice4:s.topicPick.choice4}:{}),...(s.topicPick.choice5?{choice5:s.topicPick.choice5}:{})}
    : undefined;
  const task=memberCall('/save',{birth:{year:s.year,month:s.month,day:s.day,hour:s.hourKnown?s.hour:null,minute:s.hourKnown?s.minute:null,hour_known:s.hourKnown,sex:s.sex,birth_city:s.city},lens_id:lens,concern,axis4:s.axis4,name:s.name,tier,topic})
    .then(result=>{useMember.setState({saveError:null});window.dispatchEvent(new Event('sd:reading-saved'));return result;})
    .catch(error=>{saved.delete(key);useMember.setState({saveError:error.message});throw error;});
  saved.set(key,task);return task;
}
export async function downloadReading(id:string){
  const response=await fetch(BASE+'/download/'+encodeURIComponent(id),{cache:'no-store'});
  if(!response.ok){const error=await response.json();throw new Error(error.detail||'다운로드하지 못했습니다.');}
  const url=URL.createObjectURL(await response.blob());const a=document.createElement('a');a.href=url;a.download='성신당-보관한-풀이.html';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
}
