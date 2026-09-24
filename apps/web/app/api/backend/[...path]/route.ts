import { NextRequest, NextResponse } from 'next/server';

export const dynamic='force-dynamic';
export const maxDuration=60;
const COOKIE=process.env.NODE_ENV==='production'?'__Host-sajudang-member':'sajudang_member';

async function proxy(request:NextRequest,{params}:{params:{path:string[]}}){
  const pieces=params.path;
  if(pieces[0]!=='v1'||pieces.some(p=>p==='.'||p==='..'||! /^[a-zA-Z0-9_.-]+$/.test(p)))return NextResponse.json({detail:'잘못된 요청입니다.'},{status:400});
  if(!['GET','HEAD'].includes(request.method) && request.headers.get('origin')!==new URL(request.url).origin)
    return NextResponse.json({detail:'같은 사이트에서 다시 시도해 주세요.'},{status:403});
  const base=process.env.API_BASE||process.env.NEXT_PUBLIC_API_BASE;
  if(!base)return NextResponse.json({detail:'서버 연결을 확인하고 있습니다.'},{status:503});
  const headers=new Headers();
  // 주인 문은 둘입니다 — 쪽지(x-admin-token)와 기계 열쇠(x-funnel-key).
  // x-funnel-key 를 안 흘려보내면 열쇠로 들어온 주인은 화면에서 아무것도
  // 못 엽니다 (services/api/keyguard.require_admin).
  for(const key of ['content-type','x-admin-key','x-admin-token','x-funnel-key','x-admin-view']){const value=request.headers.get(key);if(value)headers.set(key,value);}
  const token=request.cookies.get(COOKIE)?.value;
  if(token)headers.set('Authorization','Bearer '+token);
  try{
    const requestBody=['GET','HEAD'].includes(request.method)?undefined:await request.text();
    const response=await fetch(base.replace(/\/$/,'')+'/'+pieces.join('/')+new URL(request.url).search,{
      method:request.method,headers,body:requestBody,cache:'no-store',signal:AbortSignal.timeout(50000),
    });
    const forwarded=new Headers({'Cache-Control':'no-store','X-Content-Type-Options':'nosniff'});
    for(const key of ['content-type','content-disposition','x-chart-rebuild']){const value=response.headers.get(key);if(value)forwarded.set(key,value);}
    const member=pieces[1]==='account';
    if(member && ['signup','login','recover'].includes(pieces[2]) && response.ok){
      const data=await response.json();const credential=data.access_token;delete data.access_token;
      if(!credential)return NextResponse.json({detail:'로그인 정보를 확인하지 못했습니다.'},{status:502});
      const result=NextResponse.json(data,{headers:forwarded});
      result.cookies.set(COOKIE,credential,{httpOnly:true,secure:process.env.NODE_ENV==='production',sameSite:'lax',path:'/',maxAge:30*86400});
      return result;
    }
    const result=new NextResponse(response.status===204?null:await response.arrayBuffer(),{status:response.status,headers:forwarded});
    if(member && (pieces[2]==='logout'||pieces[2]==='delete'&&response.ok&&request.method==='POST')){
      // Delete's preview endpoint must not sign the member out.
      if(pieces[2]==='logout'||JSON.parse(requestBody||'{}').confirm===true)result.cookies.set(COOKIE,'',{httpOnly:true,secure:process.env.NODE_ENV==='production',sameSite:'lax',path:'/',maxAge:0});
    }
    return result;
  }catch{return NextResponse.json({detail:'서버 연결이 지연되고 있습니다. 입력을 유지한 채 다시 시도해 주세요.'},{status:502});}
}
export {proxy as GET,proxy as POST,proxy as DELETE,proxy as PUT,proxy as PATCH};
