from datetime import datetime
from fastapi import HTTPException
from . import store as s
from .models import TaskCreate,Progress
from .security import manager,task_access

STATES=['Open','Assigned','In Progress','Waiting','Submitted for Review','Completed','Cancelled']
def require_reason(reason):
    if not reason.strip(): raise HTTPException(422,'A reason is required.')
def version(doc,expected):
    if doc['version']!=expected: raise HTTPException(409,{'message':'This record changed. Refresh and compare before retrying.','current':doc})
def validate_links(db,data):
    for user in [data['owner'],*data.get('supporters',[])]:
        if not db.execute('SELECT 1 FROM users WHERE id=? AND active=1',(user,)).fetchone(): raise HTTPException(422,'Owner and supporting members must be active users.')
    for field,kind in [('equipment_id','equipment'),('vendor_id','vendors'),('purchase_id','purchases'),('project_id','projects'),('parent_id','tasks'),('related_id','tasks')]:
        if data.get(field):
            doc=s.get(db,data[field])
            if not doc or doc['kind']!=kind: raise HTTPException(422,f'Invalid {field}.')
    if data.get('due'):
        try:
            dt=datetime.fromisoformat(data['due'])
            if not dt.tzinfo: raise ValueError()
        except ValueError: raise HTTPException(422,'Due date must include a timezone.')
def create(db,user,data):
    data=TaskCreate(**data).model_dump()
    if user['role']!='manager':
        if data['owner']!=user['id'] or data['supporters']: raise HTTPException(403,'Members record work for themselves; managers assign work.')
        data['review_required']=True
        for key in ['parent_id','related_id']:
            if data[key]: task_access(user,s.get(db,data[key]))
    validate_links(db,data)
    data.update(status='Assigned' if user['role']=='manager' else 'Open',created_by=user['id'],assigned_by=user['id'],acknowledged=[],completion_summary='',test_results='',blocker='',checked=[],submitted_at=None,approved_at=None,returned=False,not_applicable=False,start_time='',finish_time='',effort_minutes=0)
    # Sequence allocation occurs inside the same IMMEDIATE transaction as insertion.
    sequence=db.execute("SELECT count(*) FROM documents WHERE kind='tasks'").fetchone()[0]+1
    data['number']=f'KIT-{sequence:06d}'
    task=s.insert(db,'tasks',data,user['id'])
    s.notify(db,[data['owner'],*data['supporters']],f"New assignment: {task['number']} — {task['title']}",task['id'])
    from .intelligence import enqueue
    enqueue(db,user,task,automatic=True)
    return task
def change(db,user,task,cmd):
    task_access(user,task); version(task,cmd.version)
    action=cmd.action; data=cmd.data; reason=cmd.reason
    if task['archived']: raise HTTPException(409,'Archived records cannot be edited.')
    if action in ['approve','return','cancel','reopen','assign','edit','archive']: manager(user)
    if task['status'] in ['Completed','Cancelled'] and action not in ['reopen','archive']:
        raise HTTPException(409,'Reopen with a reason before correcting an approved or cancelled record.')
    if action in ['update','submit','not_applicable','acknowledge'] and task['status']=='Submitted for Review':
        raise HTTPException(409,'Withdraw the submission or ask the manager to return it before editing.')
    if action=='acknowledge':
        task['acknowledged']=list(set([*task['acknowledged'],user['id']]))
    elif action=='update':
        try: data=Progress(**data).model_dump(exclude_none=True,exclude_unset=True)
        except Exception: raise HTTPException(422,'Progress fields are invalid.')
        allowed={'note','status','blocker','completion_summary','test_results','checked','start_time','finish_time','effort_minutes','work_date'}
        if set(data)-allowed: raise HTTPException(422,'Unsupported progress field.')
        if data.get('status','In Progress') not in ['Open','Assigned','In Progress','Waiting']: raise HTTPException(422,'Use Submit for Review for completion.')
        if data.get('status')=='Waiting' and not data.get('blocker','').strip(): raise HTTPException(422,'Enter the waiting reason or help needed.')
        if 'effort_minutes' in data and (not isinstance(data['effort_minutes'],(int,float)) or not 0<=data['effort_minutes']<=1000000): raise HTTPException(422,'Invalid effort.')
        if 'checked' in data and (not isinstance(data['checked'],list) or any(v not in task['checklist'] for v in data['checked'])): raise HTTPException(422,'Invalid checklist selection.')
        for key in ['start_time','finish_time']:
            if data.get(key):
                try:
                    if not datetime.fromisoformat(data[key]).tzinfo: raise ValueError()
                except ValueError: raise HTTPException(422,'Work times must include timezone.')
        note=data.pop('note','')
        task.update(data);task['latest_note']=note;task['last_contributor']=user['id']
        if task.get('blocker'): s.notify(db,s.managers(db),f"Help requested: {task['number']} — {task['blocker']}",task['id'])
    elif action in ['submit','not_applicable']:
        if action=='not_applicable':
            require_reason(reason);task['not_applicable']=True;task['completion_summary']=reason
        else:
            for key in ['completion_summary','test_results']:
                if data.get(key):
                    if not isinstance(data[key],str) or len(data[key])>20000: raise HTTPException(422,'Invalid completion text.')
                    task[key]=data[key]
            if not task['completion_summary'].strip(): raise HTTPException(422,'Enter a completion summary.')
            if set(task['checklist'])-set(task['checked']): raise HTTPException(422,'Complete the checklist before submitting.')
            if task['required_evidence'] and not any(a['task_id']==task['id'] for a in s.listing(db,'attachments')): raise HTTPException(422,'Attach the required evidence before submitting.')
        task['submitted_at']=s.now();task['returned']=False
        # Explicit review requirement also governs N/A, irrespective of task defaults.
        task['status']='Submitted for Review' if task['review_required'] or action=='not_applicable' else 'Completed'
        s.notify(db,s.managers(db),f"Review requested: {task['number']}",task['id'])
    elif action=='approve':
        if task['status']!='Submitted for Review': raise HTTPException(409,'Only submitted work can be approved.')
        task.update(status='Completed',approved_at=s.now(),approved_by=user['id'])
    elif action in ['return','withdraw']:
        require_reason(reason)
        if task['status']!='Submitted for Review': raise HTTPException(409,'Only submitted work can be returned or withdrawn.')
        task.update(status='In Progress',returned=True)
    elif action=='cancel':
        require_reason(reason);task['status']='Cancelled'
    elif action=='reopen':
        require_reason(reason)
        if task['status'] not in ['Completed','Cancelled']: raise HTTPException(409,'Only completed or cancelled records can be reopened.')
        task.update(status='In Progress',approved_at=None,returned=True,not_applicable=False)
    elif action in ['assign','edit']:
        require_reason(reason)
        if task['status']=='Submitted for Review': raise HTTPException(409,'Return submitted work before revising its assignment or details.')
        merged={k:task[k] for k in TaskCreate.model_fields};merged.update(data)
        try: merged=TaskCreate(**merged).model_dump()
        except Exception: raise HTTPException(422,'Invalid task fields.')
        validate_links(db,merged)
        if merged['parent_id']==task['id'] or merged['related_id']==task['id']: raise HTTPException(422,'A task cannot link to itself.')
        task.update(merged);task['assigned_by']=user['id'];task['acknowledged']=[]
    elif action=='archive':
        require_reason(reason)
        if task['status'] not in ['Completed','Cancelled']: raise HTTPException(409,'Finish or cancel the task before archiving.')
        task['archived']=True
    else: raise HTTPException(422,'Unknown action.')
    result=s.save(db,task,user['id'],action,reason)
    if action in ['update','submit','not_applicable','edit','assign','reopen','return','withdraw']:
        from .intelligence import enqueue
        enqueue(db,user,result,automatic=True)
    if action in ['approve','return','reopen','assign','edit']:
        s.notify(db,[task['owner'],*task['supporters']],f"{task['number']}: {action}. {reason}",task['id'])
    return result
