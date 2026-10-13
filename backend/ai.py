import json,httpx
from fastapi import APIRouter,Depends,HTTPException,Request
from pydantic import Field
from . import store as s,security as sec,tasks
from .main import user_dep,db_dep,idem
from .models import Strict,Record,TaskCreate
from .intelligence import config,enqueue,process_one,knowledge,task_analysis

router=APIRouter()
@router.get('/api/ai/status')
def ai_status(user=Depends(user_dep)):return config()

@router.get('/api/ai/knowledge')
def department_knowledge(user=Depends(user_dep),db=Depends(db_dep)):return knowledge(db)

class KnowledgeRow(Strict):
    id:str
    owner:str=Field(min_length=1,max_length=100)
    work_area:str=Field(min_length=1,max_length=200)
    responsibility:str=Field(min_length=1,max_length=4000)
    frequency:str=Field(default='Not specified',max_length=300)
    review_or_handover:str=Field(default='',max_length=500)
    source_row:int|None=None

@router.put('/api/ai/knowledge')
def update_knowledge(body:Record,request:Request,user=Depends(user_dep),db=Depends(db_dep)):
    sec.manager(user)
    def write():
        doc=knowledge(db);tasks.version(doc,body.version);tasks.require_reason(body.reason)
        if set(body.data)!={'work','reviews'}:raise HTTPException(422,'Provide work and review responsibilities.')
        names={r[0] for r in db.execute('SELECT name FROM users')}
        for section in ['work','reviews']:
            try: rows=[KnowledgeRow(**r).model_dump() for r in body.data[section]]
            except Exception:raise HTTPException(422,'Invalid responsibility row.')
            if len(rows)>300 or len({r['id'] for r in rows})!=len(rows):raise HTTPException(422,'Responsibility IDs must be unique; maximum 300 rows.')
            if any(r['owner'] not in names for r in rows):raise HTTPException(422,'Choose an existing team member.')
            doc[section]=rows
        return s.save(db,doc,user['id'],'update AI department knowledge',body.reason)
    return idem(db,user,request,body.model_dump(),write)

@router.get('/api/ai/jobs')
def jobs(user=Depends(user_dep),db=Depends(db_dep)):
    result=[]
    for job in s.listing(db,'ai_jobs'):
        target=s.get(db,job['target_id'])
        if target and (user['role']=='manager' or job['requested_by']==user['id'] and target['kind']=='tasks' and sec.can_task(user,target)):
            safe={k:v for k,v in job.items() if k!='context'}
            if safe.get('result'):
                safe['result']=safe['result'].copy();safe['result']['related_task_ids']=[id for id in safe['result'].get('related_task_ids',[]) if (t:=s.get(db,id)) and sec.can_task(user,t)]
            result.append(safe)
    return result

class Job(Strict):target_id:str
@router.post('/api/ai/jobs')
def new_job(body:Job,request:Request,user=Depends(user_dep),db=Depends(db_dep)):
    if not config()['available']:raise HTTPException(503,'AI is not connected yet. Your work is saved and can be categorized manually.')
    target=s.get(db,body.target_id)
    if not target or target['kind'] not in ['tasks','reports']:raise HTTPException(404,'Source record not found.')
    if target['kind']=='reports':sec.manager(user)
    else:
        sec.task_access(user,target)
        if target.get('archived') or target['status'] in ['Completed','Cancelled']:raise HTTPException(409,'Reopen the task before requesting new analysis.')
    return idem(db,user,request,body.model_dump(),lambda:enqueue(db,user,target))

@router.post('/api/ai/jobs/{id}/retry')
def retry(id:str,user=Depends(user_dep),db=Depends(db_dep)):
    job=s.get(db,id)
    if not job or job['kind']!='ai_jobs':raise HTTPException(404,'Job not found.')
    target=s.get(db,job['target_id'])
    if target['kind']=='reports':sec.manager(user)
    else:sec.task_access(user,target)
    if user['role']!='manager' and job['requested_by']!=user['id']:raise HTTPException(403,'This analysis belongs to another account.')
    if job['status']!='failed':raise HTTPException(409,'Only failed analyses can be retried.')
    if not config()['available']:raise HTTPException(503,'Connect AI before retrying.')
    tasks.version(target,job['source_version'])
    job.update(status='queued',not_before=s.now());return s.save(db,job,user['id'],'retry analysis')

@router.post('/api/ai/jobs/{id}/accept')
def accept(id:str,body:Record,request:Request,user=Depends(user_dep),db=Depends(db_dep)):
    def write():
        job=s.get(db,id)
        if not job or job['kind']!='ai_jobs' or job['status']!='ready':raise HTTPException(409,'Suggestion is not ready.')
        target=s.get(db,job['target_id'])
        if target['kind']=='reports':sec.manager(user)
        else:
            sec.task_access(user,target)
            if user['role']!='manager' and job['requested_by']!=user['id']:raise HTTPException(403,'This analysis belongs to another account.')
        tasks.version(target,body.version)
        if target['version']!=job['source_version']:raise HTTPException(409,'Work has changed. Wait for the new analysis or request it again.')
        permitted={'summary'} if target['kind']=='reports' else {'title','description','category','priority','owner','related_id'} if user['role']=='manager' else {'category','related_id'}
        if not body.data or set(body.data)-permitted:raise HTTPException(403,'Only managers can change assignments, priority, or original text. Members may confirm category and related work.')
        result=job['result']
        for key,value in body.data.items():
            if key=='owner':
                owner=db.execute('SELECT id FROM users WHERE name=? AND active=1',(result.get('suggested_owner',''),)).fetchone()
                if not owner or owner[0]!=value:raise HTTPException(422,'Suggested owner is not an active account.')
            elif key=='related_id':
                if value not in result.get('related_task_ids',[]):raise HTTPException(422,'Select a suggested related task.')
                sec.task_access(user,s.get(db,value))
            elif value!=result.get('report_summary' if key=='summary' else key):raise HTTPException(422,'Selected content does not match the suggestion.')
        if target['kind']=='tasks':
            if target.get('archived') or target['status'] in ['Completed','Cancelled']:raise HTTPException(409,'Reopen the task before making changes.')
            if target['status']=='Submitted for Review' and set(body.data)-{'category','related_id'}:raise HTTPException(409,'Return the submission before changing its content or assignment.')
            merged={k:target[k] for k in TaskCreate.model_fields};merged.update(body.data)
            try:validated=TaskCreate(**merged).model_dump()
            except Exception:raise HTTPException(422,'Invalid suggestion content.')
            tasks.validate_links(db,validated);target.update(validated)
            if 'owner' in body.data:
                target['assigned_by']=user['id'];target['acknowledged']=[]
                s.notify(db,[target['owner']],f"Assignment confirmed by manager: {target['number']}",target['id'])
        else:
            if target['finalized']:raise HTTPException(409,'Finalized report is locked.')
            target.update(body.data)
        updated=s.save(db,target,user['id'],'confirmed AI organization','Human confirmed: '+', '.join(body.data))
        job.update(status='accepted',accepted_fields=list(body.data),accepted_target_version=updated['version'])
        s.save(db,job,user['id'],'accepted suggestion');return updated
    return idem(db,user,request,body.model_dump(),write)
