"""Read-only post-deploy check; explicitly distinguishes free launch from sales."""
import argparse
import json
import urllib.request

parser = argparse.ArgumentParser()
parser.add_argument('--web', default='https://sajudang-three.vercel.app')
parser.add_argument('--api', default='https://sajudang-api.fly.dev')
parser.add_argument('--require-sales', action='store_true')
args = parser.parse_args()
result = {}
for name, url in [('web', args.web), ('api', args.api + '/health'), ('sales', args.web + '/api/sales-status')]:
    try:
        with urllib.request.urlopen(url, timeout=20) as response:
            result[name] = {'http': response.status}
            if name == 'sales':
                data = json.load(response)
                result[name].update(ready=data.get('ready') is True, reason=data.get('reason'))
    except Exception as error:
        result[name] = {'available': False, 'error_type': type(error).__name__}
result['free_service_ready'] = all(result[name].get('http') == 200 for name in ('web', 'api'))
result['sales_ready'] = result.get('sales', {}).get('ready', False)
print(json.dumps(result, ensure_ascii=False, indent=2))
raise SystemExit(0 if result['free_service_ready'] and (not args.require_sales or result['sales_ready']) else 1)
