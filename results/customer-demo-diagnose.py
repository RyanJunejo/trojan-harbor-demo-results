"""One response-metadata diagnostic per stalled model; no tools are executed.

The conversation is reconstructed from the saved trajectory up to its first
empty response. Parsed command JSON is reserialized, so this is a diagnostic
retest, not a byte-identical replay or another agent trial.
"""
import asyncio
import hashlib
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import litellm
from customer_demo_budget import Budget, RATES, guarded_completion


async def main():
    out = ROOT / '.context/customer-demo-diagnostics'
    out.mkdir(exist_ok=False)
    manifest = json.loads((ROOT / '.context/customer-demo-claude-pilot/manifest.json').read_text())
    budget = Budget(ROOT / '.context/customer-demo-budget.json')
    budget.initialize(100)
    os.environ['ANTHROPIC_API_KEY'] = os.environ.get('ANTHROPIC_API_KEY') or os.environ['CLAUDE_KEY']
    results = []
    for model in list(RATES)[1:]:
        trial = next(t for t in manifest['trials'] if t['model'] == model and t['variant'] == 'attack')
        job = ROOT / '.context/customer-demo-claude-pilot/runs' / trial['job']
        trajectory_path = next(job.rglob('trajectory.json'))
        trajectory = json.loads(trajectory_path.read_text())
        messages = [{'role':'user', 'content':trajectory['steps'][0]['message']}]
        for step in trajectory['steps'][1:]:
            if not step.get('message') and not step.get('tool_calls'):
                break
            content = step.get('message','')
            if step.get('tool_calls'):
                analysis, _, plan = content.partition('\nPlan: ')
                content = json.dumps({
                    'analysis': analysis.removeprefix('Analysis: '), 'plan': plan,
                    'commands': [c['arguments'] for c in step['tool_calls']],
                    'task_complete': False,
                })
            messages.append({'role':'assistant','content':content})
            observation = '\n'.join(o['content'] for o in step.get('observation',{}).get('results',[]))
            messages.append({'role':'user','content':observation})
        name = model.split('/')[-1]
        request_path = out / (name + '-conversation.json')
        request_path.write_text(json.dumps(messages,indent=2)+'\n')
        metadata = {}
        def capture(event):
            if event.get('log_event_type') != 'post_api_call': return
            raw = event.get('original_response')
            if isinstance(raw,str):
                try: raw=json.loads(raw)
                except ValueError: return
            if not isinstance(raw,dict): return
            for key in ('id','model','stop_reason','stop_details','usage'):
                if key in raw: metadata[key] = raw[key]
        ir, outr = RATES[model]
        litellm.register_model({model:{'max_input_tokens':1000000,'max_output_tokens':128000,
            'input_cost_per_token':float(ir/1000000),'output_cost_per_token':float(outr/1000000),
            'litellm_provider':'anthropic','mode':'chat'}})
        response = await guarded_completion(litellm.acompletion, budget, model,
            model=model, messages=messages, logger_fn=capture)
        result = {'model':model, 'kind':'reconstructed-context diagnostic; no command execution',
            'source_trajectory':str(trajectory_path), 'conversation':str(request_path),
            'conversation_sha256':hashlib.sha256(request_path.read_bytes()).hexdigest(),
            'provider_metadata':metadata, 'normalized_finish_reason':response.choices[0].finish_reason,
            'has_text':bool(response.choices[0].message.content),
            'usage':response.usage.model_dump()}
        results.append(result)
        (out/'results.json').write_text(json.dumps(results,indent=2)+'\n')
        print(model, json.dumps(metadata),flush=True)


asyncio.run(main())
