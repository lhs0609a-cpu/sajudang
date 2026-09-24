"use client";
import {useEffect,useState} from 'react';
import Link from 'next/link';
import {useRouter,useSearchParams} from 'next/navigation';
import {acceptMember,clearMember,downloadReading,memberCall,saveCurrentReading,useMember} from '@/lib/member';
import {useSession} from '@/lib/store';
import {ReadingSpeaker} from '@/components/ReadingVoice';
import {api} from '@/lib/api';
/* ★ 상품 이름표는 한 곳에서 옵니다 — 화면이 내부 아이디를 보이면
   손님은 「daeun_deep」 을 읽습니다 (2026-09-24). */
import {fortuneProduct} from '@/lib/fortune-products';

export async function selectSavedReading(row:any){
  const b=row.birth;
  const chart=await api.chart(b);
  useSession.getState().set({year:b.year,month:b.month,day:b.day,hour:b.hour,minute:b.minute??0,hourKnown:b.hour_known,sex:b.sex,sexSet:true,city:b.birth_city,name:row.name,axis4:row.axis4,chartId:chart.chart_id,features:chart.features,rarity:chart.rarity??null,divergence:chart.divergence??null,cur:row.lens_id,concern:row.concern,concernSet:true,topicPick:null,hookReview:null,tier:'all'});
}
import FriendInvite from './FriendInvite';
export default function MemberLibrary(){
  const {user,ready,saveError}=useMember(),s=useSession(),router=useRouter(),params=useSearchParams();
  const [mode,setMode]=useState(params.get('mode')==='signup'?'signup':params.get('mode')==='recover'?'recover':'login'),[username,setUsername]=useState(''),[password,setPassword]=useState(''),[repeat,setRepeat]=useState(''),[code,setCode]=useState(''),[recovery,setRecovery]=useState(''),[consent,setConsent]=useState(false),[busy,setBusy]=useState(false),[error,setError]=useState(''),[rows,setRows]=useState<any[]>([]),[orders,setOrders]=useState<any[]>([]),[loaded,setLoaded]=useState(false),[deleting,setDeleting]=useState(false),[deletePassword,setDeletePassword]=useState('');
  const back=params.get('returnTo');const returnTo=back?.startsWith('/')&&!back.startsWith('//')&&!back.includes('\\')?back:null;
  async function refresh(){const data=await memberCall('/library');setRows(data.readings);setOrders(data.orders);setLoaded(true);}
  useEffect(()=>{setLoaded(false);if(user)refresh().catch(e=>setError(e.message));},[user?.id]);
  async function submit(e:React.FormEvent){e.preventDefault();setBusy(true);setError('');try{
    if(mode!=='login'&&password!==repeat)throw new Error('비밀번호가 서로 다릅니다.');
    // ★ session_id 를 **가입에만** 실었습니다. 이 집은 값을 먼저 치르고
    //   들어오는 집이라, 이미 계정이 있는 손님은 로그인으로 들어옵니다 —
    //   그 길에는 치른 주문을 잇는 자리가 없어 구매가 그대로 떨어졌습니다.
    //   세 길에 다 싣습니다 (서버의 accounts.attach 가 잇습니다).
    const data=await memberCall('/'+mode,{username,password,session_id:s.sessionId,...(mode==='signup'?{consent}:{}),...(mode==='recover'?{recovery_code:code}:{})});
    acceptMember(data.user);setPassword('');setRepeat('');setCode('');if(data.recovery_code)setRecovery(data.recovery_code);
    await saveCurrentReading();await refresh();
  }catch(e){setError((e as Error).message);}finally{setBusy(false);}}
  async function run(action:()=>Promise<unknown>){setBusy(true);setError('');try{await action();}catch(e){setError((e as Error).message);}finally{setBusy(false);}}
  return <section className="conversion-card member-library" aria-label="회원 사주 보관함">
    <p className="conversion-kicker">언제든 다시 펼치는 나의 풀이</p><h1>내 사주 보관함</h1>
    <FriendInvite />
    {!ready?<p>로그인 상태를 확인하고 있습니다.</p>:!user?<>
      <p>회원가입하면 이 브라우저의 기존 구매를 연결합니다. 로그인한 뒤 읽은 기본 풀이는 자동으로 보관되며, 다른 기기에서도 다시 읽고 다운로드할 수 있습니다.</p>
      <div className="member-tabs">{[['login','로그인'],['signup','회원가입'],['recover','비밀번호 찾기']].map(([id,label])=><button key={id} className="btn gh" type="button" aria-pressed={mode===id} onClick={()=>{setMode(id);setError('');}}>{label}</button>)}</div>
      <form onSubmit={submit} className="member-form">
        <label>아이디<input required autoComplete="username" value={username} onChange={e=>setUsername(e.target.value.toLowerCase())} pattern="[a-z0-9_]{4,32}" minLength={4} maxLength={32} placeholder="영문 소문자·숫자·밑줄 4~32자"/></label>
        {mode==='recover'&&<label>가입할 때 저장한 복구 코드<input required value={code} onChange={e=>setCode(e.target.value)} autoComplete="off"/><small>이메일 대신 복구 코드로 본인을 확인합니다. 코드가 없으면 비밀번호를 재설정할 수 없습니다.</small></label>}
        <label>{mode==='recover'?'새 비밀번호':'비밀번호'}<input required type="password" autoComplete={mode==='login'?'current-password':'new-password'} minLength={10} maxLength={128} value={password} onChange={e=>setPassword(e.target.value)} placeholder="10자 이상"/></label>
        {mode!=='login'&&<label>비밀번호 확인<input required type="password" autoComplete="new-password" minLength={10} maxLength={128} value={repeat} onChange={e=>setRepeat(e.target.value)}/></label>}
        {mode==='signup'&&<label className="member-consent"><input type="checkbox" required checked={consent} onChange={e=>setConsent(e.target.checked)}/> 아이디·암호화된 비밀번호와 입력한 생년월일·성별·출생 지역·선택한 MBTI·풀이를 회원 탈퇴까지 보관하는 데 동의합니다. <Link href="/legal?tab=privacy">개인정보 처리 안내</Link></label>}
        <button className="btn" disabled={busy}>{busy?'확인 중…':mode==='signup'?'가입하고 구매·풀이 연결하기':mode==='recover'?'비밀번호 재설정하기':'로그인하고 보관함 열기'}</button>
      </form>
    </>:<>
      <p><b>{user.username}</b>님의 보관함입니다. 로그인한 기기에서 구매한 해석을 다시 열 수 있습니다.</p>
      {recovery&&<div className="conversion-card" role="status"><h2>복구 코드를 안전하게 저장해 주세요</h2><p>다시 표시되지 않습니다. 비밀번호를 잊으면 이 코드가 필요합니다. 다른 사람에게 알려주지 마세요.</p><code style={{overflowWrap:'anywhere'}}>{recovery}</code><button className="btn gh" onClick={()=>run(async()=>{await navigator.clipboard.writeText(recovery);})}>복구 코드 복사</button><button className="btn gh" onClick={()=>setRecovery('')}>안전한 곳에 저장했습니다</button></div>}
      {returnTo&&<Link className="btn" href={returnTo}>이어서 진행하기</Link>}
      <div className="member-tabs"><button className="btn" disabled={busy||!s.chartId} onClick={()=>run(async()=>{await saveCurrentReading();await refresh();})}>지금 풀이 보관하기</button><button className="btn gh" onClick={()=>{s.set({year:null,month:null,day:null,hour:null,hourKnown:false,sexSet:false,chartId:null,features:null,rarity:null,divergence:null,name:'',axis4:null,concernSet:false,topicPick:null,hookReview:null,tier:'free',cur:'pungun'});router.push('/');}}>새 사주 입력하기</button></div>
      <p className="sm">본인 또는 보관 동의를 받은 사주를 입력해 주세요. 추가로 입력한 상대방 정보·일회성 상담 답변은 저장하지 않으며, 보관함에는 기본 풀이가 남습니다. 이미 구매한 범위는 다시 결제하지 않습니다.</p>
      {!loaded?<p>보관한 풀이를 불러오고 있습니다.</p>:!rows.length?<p>아직 보관한 풀이가 없습니다. 사주를 입력하고 캐릭터의 풀이를 읽으면 여기에 모입니다.</p>:rows.map(row=><article className="conversion-card" key={row.id}>
        <ReadingSpeaker lensId={row.lens_id} label="보관한 이야기"/>
        <p className="conversion-kicker">{row.name||'이름 없는 사주'} · {row.birth.year}.{row.birth.month}.{row.birth.day} · {row.axis4||'MBTI 미선택'}</p><h2>{row.lens_name}의 풀이</h2><p className="sm">{row.tier==='free'?'무료 풀이':'구매한 풀이'} · {new Date(row.saved_at*1000).toLocaleDateString('ko-KR')} 보관</p>
        <Link className="btn" href={'/library/'+row.id}>보관한 풀이 다시 읽기</Link><button className="btn gh" disabled={busy} onClick={()=>run(()=>downloadReading(row.id))}>풀이 다운로드 · 인쇄/PDF</button><button className="btn gh" disabled={busy} onClick={()=>run(async()=>{await selectSavedReading(row);router.push('/lobby?tab=b2');})}>이 사주로 다른 캐릭터 보기</button>
      </article>)}
      {orders.filter(o=>o.product_id).length>0&&<section className="fortune-orders" aria-label="추가 분석 구매 내역"><h2>추가 분석 보관함</h2>{orders.filter(o=>o.product_id).map(o=><article className="fortune-order" key={o.order_id}><div><strong>{fortuneProduct(o.product_id||'')?.name ?? o.product_id}</strong><p className="sm">{o.status==='paid'?'결제 완료':'환불됨'} · {Number(o.amount||0).toLocaleString()}원</p></div>{o.status==='paid'&&<Link className="btn" href={`/fortune/result?product=${encodeURIComponent(o.product_id)}`}>결과 열기</Link>}</article>)}</section>}
      {orders.length>0&&<p className="sm">구매·환불 내역 {orders.length}건이 연결되어 있습니다. 가입 전 저장하지 않은 사주는 생년월일을 다시 입력해 주세요. 구매 범위는 서버에서 확인합니다.</p>}
      <button className="btn gh" disabled={busy} onClick={()=>run(async()=>{await memberCall('/logout',{});clearMember();setRows([]);setRecovery('');})}>로그아웃</button>
      <details><summary>회원 탈퇴</summary><p>보관한 사주와 풀이를 삭제합니다. 법정 보관 대상 결제 기록은 분리 보관합니다. 구독 중이면 먼저 아래에서 구독을 해지해 주세요.</p><label>비밀번호<input type="password" autoComplete="current-password" value={deletePassword} onChange={e=>{setDeletePassword(e.target.value);setDeleting(false);}}/></label><button className="btn gh" disabled={busy||!deletePassword} onClick={()=>run(async()=>{await memberCall('/delete',{password:deletePassword,confirm:deleting});if(deleting){clearMember();setDeletePassword('');setDeleting(false);}else setDeleting(true);})}>{deleting?'보관함을 삭제하고 탈퇴하기':'탈퇴 전 삭제 범위 확인하기'}</button></details>
    </>}
    {(error||saveError)&&<div role="alert"><p>{error||saveError}</p>{user&&<button className="btn gh" disabled={busy} onClick={()=>run(async()=>{await saveCurrentReading();await refresh();})}>저장·불러오기 다시 시도</button>}</div>}
  </section>;
}
