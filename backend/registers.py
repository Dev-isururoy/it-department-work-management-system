"""Small typed operational registers. Their field catalogue also drives web forms."""
import json, math
from datetime import date,datetime,time
from zoneinfo import ZoneInfo,ZoneInfoNotFoundError
from fastapi import HTTPException
from . import store as s
from .security import manager
from .tasks import version,require_reason

# field specification: label, control type, required, choices (when applicable)
CATALOG={
'equipment': {'title':'Equipment','manager':True,'fields':{'asset_id':['Asset ID','text',True],'name':['Name','text',True],'type':['Equipment type','text',True],'department':['Department','text',False],'location':['Location','text',False],'owner':['Responsible user','user',True],'serial':['Serial number','text',False],'notes':['Notes','textarea',False]}},
'backups': {'title':'Backup handovers','fields':{'title':['Handover reference','text',True],'systems':['Systems covered','textarea',True],'backup_dates':['Backup dates','text',True],'media':['Media / storage references','textarea',True],'missing':['Missing items','textarea',False],'handed_by':['Person handing over','user',True],'receipt':['Receipt acknowledgement','text',False],'verification':['Verification outcome (separate from receipt)','textarea',False],'task_id':['Related task','task',False]}},
'purchases': {'title':'Purchase requests','fields':{'reference':['Reference','text',True],'description':['Description','textarea',True],'requester':['Requester','user',True],'items':['Items and quantities','textarea',True],'estimated_cost':['Estimated cost (optional)','number',False],'currency':['Currency','text',False],'owner':['Owner','user',True],'status':['Status','select',True,['Draft','Manager Review','Submitted','Ordered','Received','Closed','Returned','Cancelled']],'task_id':['Related task / attachments','task',False]}},
'vendors': {'title':'Vendor follow-up','fields':{'name':['Vendor','text',True],'contact':['Contact details','textarea',False],'equipment_id':['Equipment','equipment',False],'task_id':['Related task','task',False],'ticket':['Ticket reference','text',False],'last_contact':['Last contact','date',False],'promised_response':['Promised response','date',False],'next_followup':['Next follow-up','date',False],'outcome':['Outcome','textarea',False]}},
'readings': {'title':'Server-room readings','fields':{'title':['Location / room','text',True],'work_date':['Reading date','date',True],'temperature':['Temperature (°C)','number',True],'rh':['Relative humidity (%)','number',True],'followup':['Follow-up','textarea',False],'review':['Manager review','textarea',False],'task_id':['Related routine task','task',False]}},
'projects': {'title':'Projects & milestones','manager':True,'fields':{'name':['Project','text',True],'description':['Scope','textarea',False],'owner':['Owner','user',True],'start':['Start date','date',False],'due':['Target date','date',False],'milestones':['Milestones / dates / results','textarea',False],'status':['Status','select',True,['Planned','Active','Waiting','Completed','Cancelled']]}},
'maintenance': {'title':'Maintenance templates','manager':True,'fields':{'title':['Template name','text',True],'equipment_type':['Equipment type','text',True],'instructions':['Instructions / checklist','textarea',True],'evidence':['Required evidence','textarea',False],'frequency':['Frequency (leave unconfigured if unknown)','text',False]}},
'roster': {'title':'Roster & calendar','manager':True,'fields':{'title':['Shift / event','text',True],'member':['Member','user',True],'start':['Start date','date',True],'end':['End date','date',True],'location':['Location','text',False],'notes':['Notes','textarea',False]}},
'leave': {'title':'Leave requests','private':True,'fields':{'title':['Request','text',True],'member':['Member','user',True],'start':['From','date',True],'end':['To','date',True],'reason':['Reason','textarea',True],'decision':['Decision','select',True,['Pending','Approved','Returned','Declined']],'decision_reason':['Manager decision reason','textarea',False]}},
'handovers': {'title':'Handover notes','fields':{'title':['Handover','text',True],'member':['From member','user',True],'covering':['Temporary covering member','user',True],'start':['From','date',True],'end':['To','date',True],'notes':['Work and follow-ups','textarea',True],'task_id':['Related shared task','task',False]}},
'knowledge': {'title':'Knowledge base','fields':{'title':['Article','text',True],'category':['Category','text',False],'issue':['Issue','textarea',True],'resolution':['Resolution / verified procedure','textarea',True],'task_id':['Resolved source task','task',False]}},
'responsibilities': {'title':'Responsibilities','manager':True,'fields':{'title':['Responsibility','text',True],'owner_name':['Default owner name','text',True],'frequency':['Supplied frequency','text',True],'review_required':['Review required','checkbox',False],'notes':['Notes / clarification','textarea',False],'schedule_id':['Configured schedule ID','text',False]}}
}
def visible(user,kind,doc): return not CATALOG[kind].get('private') or user['role']=='manager' or doc.get('created_by')==user['id']
def validate(db,kind,data,user,old=None):
    spec=CATALOG[kind];fields=spec['fields']
    if spec.get('manager'): manager(user)
    if set(data)-set(fields): raise HTTPException(422,'Unknown register fields.')
    result={}
    for key,(label,typ,required,*choices) in fields.items():
        val=data.get(key,False if typ=='checkbox' else '')
        if val is None: val=''
        if required and val=='': raise HTTPException(422,f'{label} is required.')
        if val!='':
            if typ=='number':
                try: val=float(val)
                except (ValueError,TypeError): raise HTTPException(422,f'{label} must be numeric.')
                if not math.isfinite(val): raise HTTPException(422,'Value must be finite.')
            elif typ=='checkbox':
                if not isinstance(val,bool): raise HTTPException(422,'Expected a checkbox value.')
            elif typ=='user':
                if not isinstance(val,int) or not db.execute('SELECT 1 FROM users WHERE id=?',(val,)).fetchone(): raise HTTPException(422,'Invalid user.')
            elif typ in ['task','equipment']:
                linked=s.get(db,val)
                if not linked or linked['kind']!=('tasks' if typ=='task' else 'equipment'): raise HTTPException(422,f'Invalid {label}.')
                if typ=='task':
                    from .security import task_access
                    task_access(user,linked)
            elif typ=='date':
                try: date.fromisoformat(val)
                except (ValueError,TypeError): raise HTTPException(422,f'Invalid {label}.')
            elif not isinstance(val,str) or len(val)>20000: raise HTTPException(422,'Text is too long or invalid.')
            if choices and val not in choices[0]: raise HTTPException(422,f'Invalid {label}.')
        result[key]=val
    if result.get('start') and result.get('end') and result['end']<result['start']: raise HTTPException(422,'End precedes start.')
    if user['role']!='manager':
        if old and old.get('created_by')!=user['id']: raise HTTPException(403,'Only the author or manager may edit this record.')
        for key,default in [('receipt',''),('verification',''),('review',''),('decision','Pending'),('decision_reason','')]:
            if key in fields and result[key]!=(old.get(key,default) if old else default): raise HTTPException(403,'Manager review required for this field.')
        for key in ['member','handed_by','requester','owner']:
            if key in fields and result[key]!=user['id']: raise HTTPException(403,'Record work using your own account.')
        if kind=='purchases' and result['status'] not in ['Draft','Manager Review']: raise HTTPException(403,'Manager controls purchase progression.')
        if kind=='purchases' and old and old.get('status') not in ['Draft','Returned']:raise HTTPException(409,'The manager must return a submitted purchase request before you revise it.')
        if old and (old.get('review') or old.get('receipt') or old.get('decision') in ['Approved','Declined'] or old.get('status') in ['Closed','Received']): raise HTTPException(409,'Ask the manager to record a correction to reviewed work.')
    if kind=='equipment':
        if any(x['asset_id']==result['asset_id'] and (not old or x['id']!=old['id']) for x in s.listing(db,kind)): raise HTTPException(409,'Asset ID already exists.')
    if kind=='readings':
        if not 0<=result['rh']<=100: raise HTTPException(422,'RH must be between 0 and 100%.')
        settings=json.loads(db.execute('SELECT body FROM settings WHERE id=1').fetchone()[0]);flags=[]
        for value in ['temperature','rh']:
            for suffix,compare in [('min',lambda a,b:a<b),('max',lambda a,b:a>b)]:
                limit=settings.get(f'{value}_{suffix}')
                if limit is not None and compare(result[value],limit): flags.append(f'{value} outside configured {suffix}: {limit}')
        result.update(flags=flags,limits_snapshot={k:settings[k] for k in ['temperature_min','temperature_max','rh_min','rh_max']})
    if kind=='backups' and result['verification'] and not result['receipt']: raise HTTPException(422,'Acknowledge receipt separately before verification.')
    result['created_by']=old.get('created_by',user['id']) if old else user['id']
    if old and any(result.get(k)!=old.get(k) for k in ['receipt','verification','review','decision'] if k in fields): result['reviewed_at']=s.now();result['reviewed_by']=user['id']
    elif old:
        for key in ['reviewed_at','reviewed_by']:
            if key in old: result[key]=old[key]
    return result

def validate_settings(data):
    allowed={'timezone','temperature_min','temperature_max','rh_min','rh_max','retention_days','categories'}
    if set(data)!=allowed: raise HTTPException(422,'Provide all settings fields.')
    try: ZoneInfo(data['timezone'])
    except (ZoneInfoNotFoundError,TypeError): raise HTTPException(422,'Invalid timezone.')
    for key in allowed-{'timezone','categories'}:
        if data[key] is not None and (not isinstance(data[key],(float,int)) or not math.isfinite(data[key])): raise HTTPException(422,'Limits must be numbers or empty.')
    for prefix in ['temperature','rh']:
        lo=data[f'{prefix}_min'];hi=data[f'{prefix}_max']
        if lo is not None and hi is not None and lo>hi: raise HTTPException(422,'Minimum exceeds maximum.')
    if any(data[k] is not None and not 0<=data[k]<=100 for k in ['rh_min','rh_max']): raise HTTPException(422,'RH limits must be within 0–100%.')
    if data['retention_days'] is not None and data['retention_days']<1: raise HTTPException(422,'Retention must be positive or blank.')
    if not isinstance(data['categories'],list) or not all(isinstance(v,str) and 0<len(v)<100 for v in data['categories']): raise HTTPException(422,'Invalid categories.')
    return data
