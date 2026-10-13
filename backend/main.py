import asyncio, json, os, secrets, sqlite3, hashlib, io, re, time, logging, zipfile,warnings
from contextlib import asynccontextmanager
from datetime import datetime,date,time as day_time,timedelta,timezone
from pathlib import Path
from zoneinfo import ZoneInfo
from fastapi import FastAPI,Request,Response,Depends,HTTPException,UploadFile,File,Form
from fastapi.responses import FileResponse,StreamingResponse,JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.trustedhost import TrustedHostMiddleware
from PIL import Image,UnidentifiedImageError
from . import store as s,security as sec,tasks,registers,scheduler
from .models import Login,UserEdit,TaskCreate,Change,Record,Schedule

log=logging.getLogger('kelun')
async def worker():
    while True:
        try:
            with s.connect() as db:
                db.execute('BEGIN IMMEDIATE');scheduler.tick(db)
        except Exception as exc: log.error('Background operation failed: %s',type(exc).__name__)
        await asyncio.sleep(10)
async def ai_worker():
    from .ai import process_one
    while True:
        try: await asyncio.to_thread(process_one)
        except Exception as exc: log.error('AI operation failed: %s',type(exc).__name__)
        await asyncio.sleep(10)
@asynccontextmanager
async def lifespan(app):
    s.initialize()
    with s.connect() as db:
        for job in s.listing(db,'ai_jobs'):
            if job['status']=='processing': job['status']='queued';s.save(db,job,None,'recovered interrupted AI job')
    runner=asyncio.create_task(worker())
    ai_runner=asyncio.create_task(ai_worker())
    yield
    runner.cancel()
    try: await runner
    except asyncio.CancelledError: pass
    ai_runner.cancel()
    try: await ai_runner
    except asyncio.CancelledError: pass
app=FastAPI(title='Kelun IT Work Manager',version='1.0.0',lifespan=lifespan)
app.add_middleware(TrustedHostMiddleware,allowed_hosts=os.getenv('ALLOWED_HOSTS','localhost,127.0.0.1,testserver').split(','))

@app.middleware('http')
async def controls(request,call_next):
    if request.method not in ['GET','HEAD','OPTIONS'] and request.url.path.startswith('/api/'):
        origin=request.headers.get('origin')
        if origin and origin.rstrip('/') not in [str(request.base_url).rstrip('/'),os.getenv('PUBLIC_ORIGIN','http://127.0.0.1:8000')]: return JSONResponse({'detail':'Untrusted request origin.'},403)
        if request.cookies.get('kelun_session') and request.headers.get('x-kelun-client')!='web' and not request.headers.get('authorization'): return JSONResponse({'detail':'Missing browser request protection.'},403)
    try: length=int(request.headers.get('content-length','0'))
    except ValueError: return JSONResponse({'detail':'Invalid content length.'},400)
    limit=(int(os.getenv('MAX_UPLOAD_MB','20'))+1)*1024*1024 if '/attachments' in request.url.path else 2*1024*1024
    if length>limit: return JSONResponse({'detail':'Request exceeds the configured size limit.'},413)
    if request.method in ['POST','PUT','PATCH'] and '/attachments' not in request.url.path:
        chunks=[];received=0
        async for chunk in request.stream():
            received+=len(chunk)
            if received>limit:return JSONResponse({'detail':'Request exceeds the configured size limit.'},413)
            chunks.append(chunk)
        request._body=b''.join(chunks)
    response=await call_next(request)
    response.headers.update({'X-Content-Type-Options':'nosniff','X-Frame-Options':'DENY','Referrer-Policy':'same-origin','Content-Security-Policy':"default-src 'self'; img-src 'self' blob: data:; style-src 'self'; script-src 'self'; connect-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'; form-action 'self'",'Cache-Control':'no-store'})
    return response

@app.exception_handler(sqlite3.IntegrityError)
async def integrity_error(request,exc): return JSONResponse({'detail':'Conflicting record. Refresh before retrying.'},409)

def db_dep():
    db=s.connect()
    try:
        db.execute('BEGIN IMMEDIATE')
        yield db
        db.commit()
    except Exception:
        db.rollback();raise
    finally: db.close()
def user_dep(request:Request,db=Depends(db_dep)): return sec.authenticate(db,request)
def idem(db,user,request,payload,operation):
    key=request.headers.get('idempotency-key','')
    if not key or len(key)>100: raise HTTPException(422,'A unique Idempotency-Key is required.')
    fingerprint=sec.digest(request.method+request.url.path+s.encode(payload))
    previous=db.execute('SELECT * FROM idempotency WHERE key=? AND actor=?',(key,user['id'])).fetchone()
    if previous:
        if previous['fingerprint']!=fingerprint: raise HTTPException(409,'This retry key belongs to different content.')
        return json.loads(previous['response'])
    result=operation();db.execute('INSERT INTO idempotency VALUES(?,?,?,?)',(key,user['id'],fingerprint,s.encode(result)));return result

@app.get('/api/health')
def health():
    with s.connect() as db: db.execute('SELECT 1')
    return {'status':'ok','application':'Kelun IT Work Manager'}
@app.get('/api/setup-status')
def setup_status(db=Depends(db_dep)): return {'required':not bool(db.execute("SELECT 1 FROM users WHERE role='manager' AND password IS NOT NULL").fetchone())}
@app.post('/api/setup')
def setup(body:Login,db=Depends(db_dep)):
    if db.execute("SELECT 1 FROM users WHERE role='manager' AND password IS NOT NULL").fetchone(): raise HTTPException(409,'Setup is already complete.')
    if not secrets.compare_digest(body.setup_key,(s.DATA/'.setup-key').read_text().strip()): raise HTTPException(403,'Use the setup key from the server computer.')
    if not re.fullmatch('[a-z0-9._-]{1,80}',body.username): raise HTTPException(422,'Use lowercase letters, numbers, dots, hyphens, or underscores.')
    db.execute('UPDATE users SET username=?,password=?,active=1 WHERE id=1',(body.username,sec.hash_password(body.password)))
    s.audit(db,'user:1',1,'first-run setup',{'name':'Isuru','username':body.username});return {'ok':True}
@app.post('/api/login')
def login(body:Login,request:Request,response:Response,db=Depends(db_dep)):
    key=sec.digest((request.client.host if request.client else 'unknown')+body.username.lower());cut=time.time()-900
    db.execute('DELETE FROM login_attempts WHERE at<?',(cut,))
    if db.execute('SELECT count(*) FROM login_attempts WHERE key=?',(key,)).fetchone()[0]>=8: raise HTTPException(429,'Too many attempts. Try again after 15 minutes.')
    row=db.execute('SELECT * FROM users WHERE username=?',(body.username.lower(),)).fetchone()
    if not sec.verify(row['password'] if row else None,body.password) or not row or not row['active']:
        db.execute('INSERT INTO login_attempts VALUES(?,?)',(key,time.time()));db.commit()
        raise HTTPException(401,'Incorrect account details or inactive account.')
    db.execute('DELETE FROM login_attempts WHERE key=?',(key,));user={k:row[k] for k in ['id','name','username','role','active']};value=sec.issue(db,user)
    response.set_cookie('kelun_session',value,httponly=True,samesite='strict',secure=os.getenv('COOKIE_SECURE','false').lower()=='true',max_age=43200)
    return {'user':user,**({'token':value} if request.headers.get('x-kelun-client')=='android' else {})}
@app.post('/api/logout')
def logout(request:Request,response:Response,user=Depends(user_dep),db=Depends(db_dep)):
    db.execute('DELETE FROM sessions WHERE hash=?',(sec.digest(sec.token(request)),));response.delete_cookie('kelun_session');return {'ok':True}
@app.get('/api/me')
def me(user=Depends(user_dep)): return user
@app.get('/api/users')
def users(user=Depends(user_dep),db=Depends(db_dep)):
    return [dict(r) for r in db.execute('SELECT id,name,username,role,active FROM users ORDER BY id')]
@app.post('/api/users')
def add_user(body:UserEdit,user=Depends(user_dep),db=Depends(db_dep)):
    sec.manager(user)
    if not body.password: raise HTTPException(422,'Set a unique password and share it privately.')
    data=body.model_dump();password=sec.hash_password(data.pop('password'))
    cursor=db.execute('INSERT INTO users(name,username,role,active,password) VALUES(?,?,?,?,?)',(body.name,body.username,body.role,body.active,password));s.audit(db,f'user:{cursor.lastrowid}',user['id'],'create user',data)
    return {'id':cursor.lastrowid,**data}
@app.put('/api/users/{id}')
def edit_user(id:int,body:UserEdit,user=Depends(user_dep),db=Depends(db_dep)):
    sec.manager(user);row=db.execute('SELECT * FROM users WHERE id=?',(id,)).fetchone()
    if not row: raise HTTPException(404,'User not found.')
    if row['role']=='manager' and (not body.active or body.role!='manager') and db.execute("SELECT count(*) FROM users WHERE role='manager' AND active=1").fetchone()[0]<=1: raise HTTPException(409,'Keep at least one active manager.')
    password=sec.hash_password(body.password) if body.password else row['password']
    if body.active and not password: raise HTTPException(422,'Set a password before activating this account.')
    db.execute('UPDATE users SET name=?,username=?,role=?,active=?,password=? WHERE id=?',(body.name,body.username,body.role,body.active,password,id))
    db.execute('DELETE FROM sessions WHERE user_id=?',(id,));data=body.model_dump(exclude={'password'});s.audit(db,f'user:{id}',user['id'],'edit user',data);return {'id':id,**data}

@app.get('/api/tasks')
def list_tasks(archived:bool=False,user=Depends(user_dep),db=Depends(db_dep)):
    return [t for t in s.listing(db,'tasks',archived) if sec.can_task(user,t)]
@app.post('/api/tasks')
def new_task(body:TaskCreate,request:Request,user=Depends(user_dep),db=Depends(db_dep)):
    return idem(db,user,request,body.model_dump(),lambda:tasks.create(db,user,body.model_dump()))
@app.get('/api/tasks/{id}')
def get_task(id:str,user=Depends(user_dep),db=Depends(db_dep)):
    task=s.get(db,id);sec.task_access(user,task)
    from .intelligence import task_analysis
    return {'task':task,'analysis':task_analysis(db,user,task),'attachments':[a for a in s.listing(db,'attachments') if a['task_id']==id],'history':[dict(r)|{'snapshot':json.loads(r['snapshot'])} for r in db.execute('SELECT * FROM history WHERE entity=? ORDER BY seq',(id,))]}
@app.post('/api/tasks/{id}/actions')
def task_action(id:str,body:Change,request:Request,user=Depends(user_dep),db=Depends(db_dep)):
    return idem(db,user,request,body.model_dump(),lambda:tasks.change(db,user,s.get(db,id),body))

@app.post('/api/tasks/{id}/attachments')
async def upload(id:str,request:Request,file:UploadFile=File(...),version:int=Form(...),caption:str=Form(''),phase:str=Form('Evidence'),work_time:str=Form(''),user=Depends(user_dep),db=Depends(db_dep)):
    task=s.get(db,id);sec.task_access(user,task)
    raw=await file.read(int(os.getenv('MAX_UPLOAD_MB','20'))*1024*1024+1)
    if not raw or len(raw)>int(os.getenv('MAX_UPLOAD_MB','20'))*1024*1024: raise HTTPException(413,'Empty file or upload size limit exceeded.')
    ext=Path(file.filename or '').suffix.lower()
    allowed=os.getenv('ALLOWED_EXTENSIONS','.jpg,.jpeg,.png,.webp,.pdf,.xlsx,.docx,.txt,.csv').split(',')
    if ext not in allowed: raise HTTPException(422,'File type is not allowed.')
    if len(caption)>1000 or phase not in ['Before','After','Evidence']: raise HTTPException(422,'Invalid caption or photo phase.')
    payload={'hash':hashlib.sha256(raw).hexdigest(),'caption':caption,'phase':phase,'work_time':work_time,'version':version,'name':file.filename}
    def write():
        tasks.version(task,version)
        if task['status'] in ['Completed','Cancelled','Submitted for Review'] or task['archived']: raise HTTPException(409,'Return, withdraw, or reopen the task before adding evidence.')
        thumb=None;metadata={};mime='application/octet-stream'
        if ext in ['.jpg','.jpeg','.png','.webp']:
            try:
                with warnings.catch_warnings():
                    warnings.simplefilter('error',Image.DecompressionBombWarning)
                    im=Image.open(io.BytesIO(raw))
                    if im.width*im.height>25000000:raise ValueError('Image exceeds 25 megapixels')
                    im.verify();im=Image.open(io.BytesIO(raw));im.load()
                expected={'.jpg':'JPEG','.jpeg':'JPEG','.png':'PNG','.webp':'WEBP'}
                if im.format!=expected[ext]: raise ValueError()
                metadata={str(k):str(v)[:300] for k,v in im.getexif().items() if k in [306,36867,36868]}
                im.thumbnail((600,600));stream=io.BytesIO();im.convert('RGB').save(stream,'JPEG',quality=85);thumb=stream.getvalue();mime=Image.MIME.get(expected[ext],'application/octet-stream')
            except (Exception,) as exc: raise HTTPException(422,'Invalid or oversized image.') from exc
        elif ext=='.pdf' and not raw.startswith(b'%PDF-'): raise HTTPException(422,'Invalid PDF.')
        elif ext in ['.xlsx','.docx']:
            try:
                with zipfile.ZipFile(io.BytesIO(raw)) as archive:
                    names=archive.namelist()
                    if '[Content_Types].xml' not in names or not any(n.startswith('xl/' if ext=='.xlsx' else 'word/') for n in names) or any('vbaProject' in n for n in names): raise ValueError()
            except Exception: raise HTTPException(422,'Invalid or macro-enabled Office document.')
        elif ext in ['.txt','.csv']:
            try: raw.decode('utf-8')
            except UnicodeDecodeError: raise HTTPException(422,'Text evidence must use UTF-8.')
        filename=re.sub(r'[^a-zA-Z0-9._ -]','_',Path((file.filename or 'evidence').replace('\\','/')).name)[:140]
        aid=s.uid();(s.DATA/'attachments'/aid).write_bytes(raw)
        if thumb: (s.DATA/'attachments'/(aid+'.thumb')).write_bytes(thumb)
        attachment=s.insert(db,'attachments',{'task_id':id,'filename':filename,'mime':mime,'size':len(raw),'sha256':payload['hash'],'caption':caption,'phase':phase,'work_time':work_time,'photo_metadata_unverified':metadata,'uploaded_at':s.now(),'uploaded_by':user['id'],'thumbnail':bool(thumb),'task_version':version},user['id'],id=aid)
        if thumb:task['latest_attachment']=aid
        updated=s.save(db,task,user['id'],'attach evidence',caption)
        from .intelligence import enqueue
        enqueue(db,user,updated,automatic=True)
        return attachment
    return idem(db,user,request,payload,write)
@app.get('/api/attachments/{id}')
def download(id:str,thumbnail:bool=False,user=Depends(user_dep),db=Depends(db_dep)):
    a=s.get(db,id)
    if not a or a['kind']!='attachments': raise HTTPException(404,'Attachment not found.')
    sec.task_access(user,s.get(db,a['task_id']))
    path=s.DATA/'attachments'/(id+'.thumb' if thumbnail and a['thumbnail'] else id)
    return FileResponse(path,media_type='image/jpeg' if thumbnail and a['thumbnail'] else a['mime'],filename=None if thumbnail else a['filename'],content_disposition_type='inline' if thumbnail else 'attachment')

@app.get('/api/events')
async def events(request:Request):
    with s.connect() as db: sec.authenticate(db,request)
    async def stream():
        last=-1
        while not await request.is_disconnected():
            with s.connect() as db:
                try: sec.authenticate(db,request)
                except HTTPException: break
                seq=db.execute('SELECT coalesce(max(seq),0) FROM history').fetchone()[0]
            if seq!=last:
                yield f'event: change\ndata: {seq}\n\n';last=seq
            else: yield ': heartbeat\n\n'
            await asyncio.sleep(2)
    return StreamingResponse(stream(),media_type='text/event-stream',headers={'X-Accel-Buffering':'no'})
@app.get('/api/notifications')
def notifications(user=Depends(user_dep),db=Depends(db_dep)):
    return [dict(r) for r in db.execute('SELECT * FROM notifications WHERE user_id=? ORDER BY at DESC LIMIT 200',(user['id'],))]
@app.get('/api/dashboard')
def dashboard(user=Depends(user_dep),db=Depends(db_dep)):
    settings=json.loads(db.execute('SELECT body FROM settings').fetchone()[0]);tz=ZoneInfo(settings['timezone']);instant=datetime.now(tz);upcoming=[]
    for schedule in s.listing(db,'schedules'):
        if schedule['paused'] or user['role']!='manager' and schedule['owner']!=user['id']:continue
        day=max(instant.date(),date.fromisoformat(schedule['start']))
        for _ in range(370):
            due=datetime.combine(day,day_time.fromisoformat(schedule['due_time']),tz)
            if scheduler.matches(schedule,day) and due>=instant:
                upcoming.append({'title':schedule['title'],'owner':schedule['owner'],'due':due.isoformat()});break
            day+=timedelta(days=1)
    ready=0
    for job in s.listing(db,'ai_jobs'):
        target=s.get(db,job['target_id'])
        if job['status']=='ready' and target and (user['role']=='manager' or job['requested_by']==user['id'] and target['kind']=='tasks' and sec.can_task(user,target)):ready+=1
    return {'upcoming':sorted(upcoming,key=lambda d:d['due'])[:8],'ai_awaiting_review':ready}
@app.post('/api/notifications/read')
def read_notifications(user=Depends(user_dep),db=Depends(db_dep)):
    db.execute('UPDATE notifications SET seen=1 WHERE user_id=?',(user['id'],));return {'ok':True}
@app.get('/api/settings')
def settings(user=Depends(user_dep),db=Depends(db_dep)):
    return json.loads(db.execute('SELECT body FROM settings WHERE id=1').fetchone()[0])
@app.put('/api/settings')
def put_settings(body:Record,user=Depends(user_dep),db=Depends(db_dep)):
    sec.manager(user);data=registers.validate_settings(body.data);db.execute('UPDATE settings SET body=? WHERE id=1',(s.encode(data),));s.audit(db,'settings',user['id'],'settings',data);return data
@app.get('/api/catalog')
def catalog(user=Depends(user_dep)): return registers.CATALOG
@app.get('/api/registers/{kind}')
def list_register(kind:str,archived:bool=False,user=Depends(user_dep),db=Depends(db_dep)):
    if kind not in registers.CATALOG: raise HTTPException(404,'Register not found.')
    return [d for d in s.listing(db,kind,archived) if registers.visible(user,kind,d)]
@app.post('/api/registers/{kind}')
def add_register(kind:str,body:Record,request:Request,user=Depends(user_dep),db=Depends(db_dep)):
    if kind not in registers.CATALOG: raise HTTPException(404,'Register not found.')
    def write():
        data=registers.validate(db,kind,body.data,user)
        doc=s.insert(db,kind,data,user['id'])
        if kind in ['leave','readings','backups','purchases']: s.notify(db,s.managers(db),f'New {registers.CATALOG[kind]["title"]} record: {data.get("title",data.get("reference",""))}')
        return doc
    return idem(db,user,request,body.model_dump(),write)
@app.put('/api/registers/{kind}/{id}')
def edit_register(kind:str,id:str,body:Record,request:Request,user=Depends(user_dep),db=Depends(db_dep)):
    if kind not in registers.CATALOG: raise HTTPException(404,'Register not found.')
    doc=s.get(db,id)
    if not doc or doc['kind']!=kind: raise HTTPException(404,'Record not found.')
    def write():
        tasks.version(doc,body.version);tasks.require_reason(body.reason)
        if doc['archived']: raise HTTPException(409,'Record is archived.')
        data=registers.validate(db,kind,body.data,user,doc)
        return s.save(db,{**doc,**data},user['id'],'edit register',body.reason)
    return idem(db,user,request,body.model_dump(),write)
@app.get('/api/history/{id}')
def history(id:str,user=Depends(user_dep),db=Depends(db_dep)):
    sec.manager(user)
    return [dict(r)|{'snapshot':json.loads(r['snapshot'])} for r in db.execute('SELECT * FROM history WHERE entity=? ORDER BY seq',(id,))]
@app.post('/api/archive/{id}')
def archive(id:str,body:Change,user=Depends(user_dep),db=Depends(db_dep)):
    sec.manager(user);doc=s.get(db,id)
    if not doc or doc['kind'] not in registers.CATALOG: raise HTTPException(404,'Register record not found.')
    tasks.version(doc,body.version);tasks.require_reason(body.reason);doc['archived']=True
    return s.save(db,doc,user['id'],'archive',body.reason)

def validate_schedule(db,body):
    try: date.fromisoformat(body.start);day_time.fromisoformat(body.due_time)
    except ValueError: raise HTTPException(422,'Invalid start date or due time.')
    if not db.execute('SELECT 1 FROM users WHERE id=?',(body.owner,)).fetchone(): raise HTTPException(422,'Select an existing owner. Assignments wait until this account is active.')
    if body.frequency=='weekdays' and (not body.weekdays or any(d not in range(7) for d in body.weekdays)): raise HTTPException(422,'Choose weekdays (Monday=0).')
    return body.model_dump()
@app.get('/api/schedules')
def schedules(user=Depends(user_dep),db=Depends(db_dep)): return s.listing(db,'schedules')
@app.post('/api/schedules')
def add_schedule(body:Schedule,request:Request,user=Depends(user_dep),db=Depends(db_dep)):
    sec.manager(user)
    return idem(db,user,request,body.model_dump(),lambda:s.insert(db,'schedules',validate_schedule(db,body),user['id']))
@app.put('/api/schedules/{id}')
def edit_schedule(id:str,body:Record,user=Depends(user_dep),db=Depends(db_dep)):
    sec.manager(user);doc=s.get(db,id)
    if not doc or doc['kind']!='schedules': raise HTTPException(404,'Schedule not found.')
    tasks.version(doc,body.version);tasks.require_reason(body.reason)
    try: parsed=Schedule(**body.data)
    except Exception: raise HTTPException(422,'Invalid schedule.')
    data=validate_schedule(db,parsed)
    # Re-scan from start after edits; unique occurrences protect existing history.
    return s.save(db,{**doc,**data,'next_scan':data['start']},user['id'],'edit schedule',body.reason)
@app.post('/api/schedules/run')
def run_schedule(user=Depends(user_dep),db=Depends(db_dep)):
    sec.manager(user);scheduler.tick(db);return {'ok':True}

from .reports import router as reports_router
from .ai import router as ai_router
app.include_router(reports_router)
app.include_router(ai_router)
app.mount('/',StaticFiles(directory=s.ROOT/'web',html=True),name='web')
