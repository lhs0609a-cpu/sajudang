"""10,000 synthetic visits against an isolated API; never defaults to production."""
import argparse, asyncio, json, math, time
from collections import Counter, defaultdict
from datetime import date, timedelta
from pathlib import Path
from urllib.parse import urlparse
import httpx

async def main(args):
    if urlparse(args.base).hostname not in ('127.0.0.1','localhost','::1'):
        raise SystemExit('This runner only targets an isolated loopback service.')
    latency=defaultdict(list);errors=Counter();semaphore=asyncio.Semaphore(args.concurrency)
    started=time.perf_counter();completed=0
    async with httpx.AsyncClient(base_url=args.base,timeout=120,limits=httpx.Limits(max_connections=args.concurrency)) as client:
        async def post(path,body):
            at=time.perf_counter()
            try:
                response=await client.post(path,json=body)
                latency[path].append(1000*(time.perf_counter()-at))
                response.raise_for_status()
                return response.json()
            except Exception as e:
                errors[f'{path}:{type(e).__name__}']+=1
                return None
        async def visit(i):
            nonlocal completed
            async with semaphore:
                born=date(1970,1,1)+timedelta(days=i)
                c=await post('/v1/chart',{'year':born.year,'month':born.month,'day':born.day,'hour':i%24 if i%2 else None,'minute':i%60,'hour_known':bool(i%2),'sex':'M' if i%3 else 'F','birth_city':'서울'})
                if not c:return
                concern=['money','work','love','people','dir','health'][i%6]
                r=await post('/v1/report',{'chart_id':c['chart_id'],'lens_id':args.lenses[i%len(args.lenses)],'concern':concern,'tier':'free'})
                if not r:return
                if not r.get('practice'):
                    errors['missing_practice']+=1
                    return
                completed+=1
                if completed%1000==0:print(f'{completed}/{args.users} visits',flush=True)
        await asyncio.gather(*(visit(i) for i in range(args.users)))
    elapsed=time.perf_counter()-started
    def percentile(values,p):
        values=sorted(values);return round(values[max(0,math.ceil(len(values)*p)-1)],2)
    result={'users':args.users,'completed':completed,'concurrency':args.concurrency,
            'elapsed_seconds':round(elapsed,2),'visits_per_second':round(completed/elapsed,2),
            'errors':dict(errors),'environment':'isolated local API; not production capacity proof',
            'requests':{path:{'count':len(v),'p50_ms':percentile(v,.5),'p95_ms':percentile(v,.95),'p99_ms':percentile(v,.99)} for path,v in latency.items()}}
    Path(args.output).write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result),flush=True)
    return 1 if errors or completed!=args.users else 0

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--base',default='http://127.0.0.1:8026')
    parser.add_argument('--users',type=int,default=10000)
    parser.add_argument('--concurrency',type=int,default=40)
    parser.add_argument('--output',default='load-result.json')
    args=parser.parse_args()
    bank=json.loads((Path(__file__).resolve().parents[1]/'seed/lenses.json').read_text(encoding='utf-8'))
    args.lenses=[x['id'] for x in (bank if isinstance(bank,list) else bank['lenses'])]
    raise SystemExit(asyncio.run(main(args)))
