"""Read saved client/Ollama evidence; no inference or model-loading requests."""
import argparse
from datetime import datetime
import hashlib
import json
from pathlib import Path
import re


def diagnose(run,log_root):
    execution=json.loads((run/'execution.json').read_text(encoding='utf-8'))
    times={s['label']:datetime.fromisoformat(s['utc']) for s in execution['snapshots']}
    before=times['immediately_before_qwen'];after=times['after_qwen_unload']
    matches=[]
    for path in log_root.glob('server*.log'):
        data=path.read_bytes();lines=data.decode('utf-8','replace').splitlines()
        active=False;window=[];started=None;ready=None
        for number,line in enumerate(lines,1):
            timestamp=re.search(r'time=(\S+)',line)
            instant=None
            if timestamp:
                try:instant=datetime.fromisoformat(timestamp[1])
                except ValueError:pass
            if instant and before<=instant<=after and 'starting llama-server' in line:
                active=True;started=instant
            if active:
                if instant and instant>after:break
                window.append((number,line))
                if instant and 'loaded runners' in line:ready=instant
        if window:matches.append((path,data,window,started,ready))
    result={'scope':'saved-log diagnosis; no new inference','client_errors':execution['errors'],
        'actual_limit':'client/server request deadline with cancellation','model_load_seconds':None,
        'prompt_evaluation_seconds':None,'generation_seconds':None,'generated_tokens':None,
        'phase_limitation':'logs do not separate prefill, generation or a stall after prompt submission',
        'gpu_oom_demonstrated':False,'openmp_conflict_demonstrated':False,'snapshots':execution['snapshots']}
    if len(matches)!=1:
        result['log_status']='UNAVAILABLE_OR_AMBIGUOUS';return result
    path,data,window,started,ready=matches[0]
    text='\n'.join(l for _,l in window)
    result.update(log_status='MATCHED_SAVED_RUN',source_log=path.name,source_log_sha256=hashlib.sha256(data).hexdigest(),
        model_started=started.isoformat(),model_ready=ready.isoformat() if ready else None,
        model_load_seconds=(ready-started).total_seconds() if ready else None)
    patterns={'gpu_layers':r'offloaded (\d+)/(\d+) layers','cpu_model_mib':r'CPU model buffer size\s*=\s*([\d.]+) MiB',
        'cpu_kv_mib':r'CPU KV buffer size\s*=\s*([\d.]+) MiB','scheduled_prompt_tokens':r'task.n_tokens = (\d+)'}
    for name,pattern in patterns.items():
        match=re.search(pattern,text)
        result[name]=[int(x) for x in match.groups()] if name=='gpu_layers' and match else float(match[1]) if match else None
    wanted=re.compile(r'offloaded \d+/\d+|CPU model buffer size|CPU KV buffer size|task.n_tokens =|/api/chat|cancel task')
    result['supporting_lines']=[{'line':n,'text':line} for n,line in window if wanted.search(line)]
    result['cpu_offloading_observed']=bool(result.get('cpu_model_mib'))
    result['interpretation']='Loading completed in about44s; a 1811-token prompt was submitted, then the request was cancelled at3m. CPU offload and low host RAM are observed, but the slow post-load phase is not timed. No evidence establishes GPU OOM as the cause.'
    return result


def main():
    p=argparse.ArgumentParser();p.add_argument('--run',type=Path,default=Path('outputs/accuracy/gpu-api-selection-v1'))
    p.add_argument('--log-root',type=Path,default=Path.home()/'AppData/Local/Ollama');p.add_argument('--output',type=Path,required=True)
    args=p.parse_args();data=diagnose(args.run,args.log_root);args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in data.items() if k not in ('snapshots','supporting_lines')}))


if __name__=='__main__':main()
