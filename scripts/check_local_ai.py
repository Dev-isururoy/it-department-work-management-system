"""Real local-model smoke test. Synthetic records only; no production tasks are created."""
import sys,json,time,os,base64,io
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from backend.intelligence import SYSTEM,validate_result
from backend.providers import OllamaProvider
from PIL import Image,ImageDraw
knowledge=json.loads(Path('backend/seeds/department_knowledge.json').read_text(encoding='utf-8'))
context={'department_knowledge':knowledge,'allowed_categories':['Uncategorized','Infrastructure','Access management','Documentation','Backups','Support','Routine check'],'users':[{'name':n,'active':True} for n in ['Isuru','Pasan','Wathsala','Thilakshana']],'related_authorized_records':[]}
results=[]
cases=[('monthly-printer-billing','Check the monthly rented black-and-white printer meter counts against the rental invoice. Record discrepancies and coordinate with the rental vendor.','Thilakshana','work-22',[]),('backup-handover','Collect this week\'s manual backup media and hand it over to Isuru, recording the handover.','Thilakshana','work-24',[])]
for name,description,owner,match,images in cases:
    print('Testing real model:',name,flush=True);start=time.monotonic()
    result=validate_result(OllamaProvider('gemma3:4b').analyze(SYSTEM,json.dumps({'record':{'title':name,'description':description},'context':context}),images),context)
    passed=result['suggested_owner']==owner and match in result['matched_responsibility_ids']
    results.append({'case':name,'seconds':round(time.monotonic()-start,1),'passed':passed,'result':result})
    Path('test-results/local-ai-live.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
    print(json.dumps(results[-1]),flush=True)
if not all(r['passed'] for r in results):raise SystemExit('Model did not match expected responsibility; inspect results before enabling.')
