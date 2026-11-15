"""Versioned package inference only. Local host performs all source verification."""
import argparse
import importlib.metadata
import json
import os
import platform
import sys
from pathlib import Path
import time

from pipeline.inference.packages import validate_input,create_result,result_archive
from pipeline.inference.structured import schema_prefix


def main():
    p=argparse.ArgumentParser();p.add_argument('--input',type=Path,required=True)
    p.add_argument('--expected-input-sha256',required=True);p.add_argument('--device',type=int,choices=[0,1],default=0)
    p.add_argument('--output',type=Path,required=True);args=p.parse_args()
    os.environ['CUDA_VISIBLE_DEVICES']=str(args.device)
    manifest,packet,request,runtime=validate_input(args.input,args.expected_input_sha256)
    args.output.mkdir(parents=True,exist_ok=False)
    started=time.perf_counter();raw='';candidates=None
    execution={'status':'FAILED','execution_kind':'remote_model_inference','requested_model':runtime['requested_model'],
        'generation':runtime['generation'],'quantization':runtime['quantization'],'physical_device':args.device,
        'response_contract':request.get('response_contract'),
        'environment_profile':runtime.get('environment_profile'),
        'python_version':platform.python_version(),'python_executable':sys.executable,
        'code_commit':manifest['code_commit'],'prompt_tokens':None,'generated_tokens':None,'finish_reason':None}
    error=None
    try:
        import torch
        import jsonschema
        from transformers import AutoTokenizer,AutoModelForCausalLM,BitsAndBytesConfig
        from pipeline.extraction.clients import parse_object
        execution.update(torch_version=torch.__version__,torch_cuda=torch.version.cuda)
        if runtime.get('environment_profile'):
            from kaggle.environment import verify_environment
            execution['environment']=verify_environment(runtime['environment_profile'],torch,
                                                         os.environ.get('RGPT_OVERLAY_PATH'))
        if not torch.cuda.is_available():raise RuntimeError('requested GPU unavailable')
        free,total=torch.cuda.mem_get_info(0)
        execution.update(device_name=torch.cuda.get_device_name(0),free_vram_before_load=free,total_vram=total)
        profile=runtime.get('environment_profile')
        if profile and profile['device_name_contains'] not in execution['device_name']:
            raise RuntimeError('device differs from prepared environment profile')
        config=runtime['requested_model'];g=runtime['generation'];q=runtime['quantization']
        if free<config['minimum_free_bytes']:raise RuntimeError('insufficient free VRAM; export a different supported job, no silent model substitution')
        if q!={'method':'bitsandbytes_nf4','compute_dtype':'float16','double_quant':True}:raise ValueError('unsupported quantization')
        load=time.perf_counter()
        tokenizer=AutoTokenizer.from_pretrained(config['model'],revision=config['revision'])
        # The same schema controls generation and post-validation. No output
        # conversion, label-to-ID matching, truncation, or retry repairs exist.
        prefix=schema_prefix(tokenizer,request['output_schema'])
        text=tokenizer.apply_chat_template(request['messages'],tokenize=False,add_generation_prompt=True,
                                           enable_thinking=g['enable_thinking'])
        inputs=tokenizer(text,return_tensors='pt',add_special_tokens=False)
        execution['prompt_tokens']=int(inputs.input_ids.shape[1])
        if execution['prompt_tokens']+g['max_new_tokens']>g['context_window']:raise ValueError('complete evidence does not fit; no truncation')
        model=AutoModelForCausalLM.from_pretrained(config['model'],revision=config['revision'],device_map={'':0},
            torch_dtype=torch.float16,quantization_config=BitsAndBytesConfig(load_in_4bit=True,bnb_4bit_quant_type='nf4',
                bnb_4bit_use_double_quant=True,bnb_4bit_compute_dtype=torch.float16))
        torch.cuda.synchronize();execution['load_seconds']=time.perf_counter()-load
        inputs=inputs.to('cuda:0')
        torch.manual_seed(g['seed']);torch.cuda.reset_peak_memory_stats();generation=time.perf_counter()
        with torch.inference_mode():tokens=model.generate(**inputs,max_new_tokens=g['max_new_tokens'],
            do_sample=g['do_sample'],prefix_allowed_tokens_fn=prefix)
        torch.cuda.synchronize();ids=tokens[0,inputs.input_ids.shape[1]:]
        raw=tokenizer.decode(ids,skip_special_tokens=True)
        execution.update(generated_tokens=len(ids),generation_seconds=time.perf_counter()-generation,
            peak_allocated_bytes=torch.cuda.max_memory_allocated(),peak_reserved_bytes=torch.cuda.max_memory_reserved())
        eos=model.generation_config.eos_token_id
        eos=set(eos if isinstance(eos,list) else [eos])|{tokenizer.eos_token_id}
        execution['finish_reason']='eos' if len(ids) and int(ids[-1]) in eos else 'length'
        if execution['finish_reason']!='eos':raise ValueError('incomplete generation')
        candidates=parse_object(raw)
        jsonschema.validate(candidates,request['output_schema'])
        execution['status']='COMPLETED'
    except Exception as exc:
        execution.update(error_type=type(exc).__name__,error=str(exc));error=exc
    finally:
        execution['runtime_seconds']=time.perf_counter()-started
        try:
            execution['packages']={name:importlib.metadata.version(name) for name in
                                   {d.metadata['Name'] for d in importlib.metadata.distributions() if d.metadata.get('Name')}}
        except Exception as inventory_error:
            execution['packages']={}
            execution['package_inventory_error']=type(inventory_error).__name__+': '+str(inventory_error)
        create_result(args.output,args.input,raw,candidates,execution)
        (args.output/'result.zip').write_bytes(result_archive(args.output))
    print(json.dumps({'status':execution['status'],'output':str(args.output),'error_type':execution.get('error_type')}))
    if error:raise SystemExit(2)


if __name__=='__main__':main()
