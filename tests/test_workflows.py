import io,json,sqlite3,uuid,zipfile
from datetime import datetime,timedelta,timezone
import pytest
from fastapi.testclient import TestClient
from PIL import Image
from backend.main import app
from backend import store as s,scheduler

PASSWORD='Unique-local-test-passphrase-123!'
@pytest.fixture
def env(tmp_path,monkeypatch):
    monkeypatch.setattr(s,'DATA',tmp_path)
    monkeypatch.setenv('AI_PROVIDER','disabled')
    with TestClient(app,base_url="http://localhost") as c:
        assert c.get('/api/setup-status').json()['required']
        assert c.post('/api/setup',json={'username':'isuru','password':PASSWORD,'setup_key':(tmp_path/'.setup-key').read_text()}).status_code==200
        c.post('/api/login',json={'username':'isuru','password':PASSWORD},headers={'X-Kelun-Client':'android'})
        c.headers['X-Kelun-Client']='web'
        for id,name in [(2,'Pasan'),(3,'Wathsala'),(4,'Thilakshana')]:
            assert c.put('/api/users/'+str(id),json={'name':name,'username':name.lower(),'password':PASSWORD,'role':'member','active':True}).status_code==200
        yield c,tmp_path
def sign(c,name):
    c.cookies.clear();r=c.post('/api/login',json={'username':name,'password':PASSWORD},headers={'X-Kelun-Client':'android'});assert r.status_code==200;return r.json()['token']
def post(c,path,data,key=None): return c.post('/api'+path,json=data,headers={'Idempotency-Key':key or str(uuid.uuid4())})
def task(c,**kwargs):
    r=post(c,'/tasks',{'title':'Clock synchronization check','owner':2,**kwargs});assert r.status_code==200,r.text;return r.json()
def act(c,t,action,data=None,reason='Test reason',key=None):return post(c,f'/tasks/{t["id"]}/actions',{'version':t['version'],'action':action,'data':data or {},'reason':reason},key)
def picture():
    f=io.BytesIO();Image.new('RGB',(40,40),'green').save(f,'PNG');return f.getvalue()

def test_first_setup_and_accounts(env):
    c,path=env;assert len(c.get('/api/users').json())==4
    assert c.post('/api/setup',json={'username':'isuru','password':PASSWORD,'setup_key':(path/'.setup-key').read_text()}).status_code==409
    with s.connect() as db:
        users=db.execute('SELECT password FROM users').fetchall();assert all(r[0].startswith('$argon2id$') for r in users)
    assert len(c.get('/api/registers/responsibilities').json())==51

def test_assignment_evidence_review_and_permissions(env):
    c,path=env;t=task(c,required_evidence='Photograph and signed record',checklist=['Compare clock'])
    sign(c,'wathsala');assert c.get('/api/tasks').json()==[];assert act(c,t,'update',{'note':'Intrusion'}).status_code==403
    assert c.put('/api/settings',json={'data':{}}).status_code==403
    sign(c,'pasan');assert c.get('/api/tasks').json()[0]['id']==t['id'];assert any('New assignment' in n['message'] for n in c.get('/api/notifications').json())
    t=act(c,t,'acknowledge').json();assert 2 in t['acknowledged']
    t=act(c,t,'update',{'note':'Compared to company time source','status':'In Progress','checked':['Compare clock'],'completion_summary':'Clocks checked','test_results':'No difference recorded'}).json()
    assert act(c,t,'submit').status_code==422
    key=str(uuid.uuid4());args={'data':{'version':t['version'],'caption':'Clock display','phase':'After'},'files':{'file':('clock.png',picture(),'image/png')},'headers':{'Idempotency-Key':key}}
    upload=c.post('/api/tasks/'+t['id']+'/attachments',**args);assert upload.status_code==200,upload.text;a=upload.json()
    assert c.post('/api/tasks/'+t['id']+'/attachments',**args).json()['id']==a['id']
    assert c.get('/api/attachments/'+a['id']).content==picture();assert c.get('/api/attachments/'+a['id']+'?thumbnail=true').status_code==200
    t=c.get('/api/tasks/'+t['id']).json()['task'];t=act(c,t,'submit').json();assert t['status']=='Submitted for Review'
    assert act(c,t,'approve').status_code==403;assert act(c,t,'update',{'note':'silent edit'}).status_code==409
    sign(c,'isuru');t=act(c,t,'return',reason='Add recorded result').json();assert t['returned']
    sign(c,'pasan');t=act(c,t,'update',{'note':'Result documented','completion_summary':'Verified all clocks against reference'}).json();t=act(c,t,'submit').json()
    sign(c,'isuru');t=act(c,t,'approve').json();assert t['approved_at'] and t['submitted_at']
    assert act(c,t,'edit',{'description':'Overwrite'}).status_code==409
    t=act(c,t,'reopen',reason='Correction: wrong reference noted').json();t=act(c,t,'assign',{'owner':4},reason='Cover for absence').json()
    history=c.get('/api/tasks/'+t['id']).json()['history'];assert any(h['action']=='approve' and h['snapshot']['status']=='Completed' for h in history)
    sign(c,'pasan');assert c.get('/api/attachments/'+a['id']).status_code==403
    c.cookies.clear();assert c.get('/api/attachments/'+a['id']).status_code==401
    with s.connect() as db:
        with pytest.raises(sqlite3.IntegrityError):db.execute('DELETE FROM history')

def test_idempotency_and_conflicts(env):
    c,_=env;key=str(uuid.uuid4());payload={'title':'Offline work','owner':2};a=post(c,'/tasks',payload,key).json();b=post(c,'/tasks',payload,key).json();assert a['id']==b['id']
    assert post(c,'/tasks',{**payload,'title':'Different'},key).status_code==409
    sign(c,'pasan');cmd={'note':'Offline queued update','status':'In Progress'};key=str(uuid.uuid4());a2=act(c,a,'update',cmd,key=key).json();assert act(c,a,'update',cmd,key=key).json()['version']==a2['version'];assert act(c,a,'update',{'note':'Outdated'}).status_code==409

def test_schedules_restart_catchup_and_not_applicable(env):
    c,_=env;day=datetime.now(timezone.utc).date()-timedelta(days=3)
    r=post(c,'/schedules',{'title':'Daily reading','owner':4,'frequency':'daily','start':day.isoformat(),'due_time':'09:00'});assert r.status_code==200,r.text
    for _ in range(2):assert c.post('/api/schedules/run').status_code==200
    generated=c.get('/api/tasks').json();count=len(generated);assert count in [4,5];assert len({(t['schedule_id'],t['occurrence']) for t in generated})==count
    assert any(t['missed_occurrence'] for t in generated)
    t=generated[0];sign(c,'thilakshana');assert act(c,t,'not_applicable',reason='').status_code==422;t=act(c,t,'not_applicable',reason='Room inaccessible; manager informed').json();assert t['status']=='Submitted for Review'
    with s.connect() as db:scheduler.tick(db)
    assert len(c.get('/api/tasks').json())==count

def test_reports_snapshots_and_excel(env):
    c,_=env;t=task(c);sign(c,'pasan');t=act(c,t,'update',{'note':'Finished tests','completion_summary':'Completed inspection'}).json();t=act(c,t,'submit').json();sign(c,'isuru')
    today=datetime.now(timezone.utc).date().isoformat();r=post(c,'/reports',{'start':today,'end':today}).json();assert len(r['rows'])==1;assert r['rows'][0]['status']=='Submitted for Review';assert r['sections']['Awaiting manager review']==[t['id']]
    r=c.put('/api/reports/'+r['id'],json={'version':r['version'],'data':{'finalized':True}},headers={'Idempotency-Key':str(uuid.uuid4())}).json();assert r['finalized']
    assert c.put('/api/reports/'+r['id'],json={'version':r['version'],'data':{'summary':'Overwrite'}},headers={'Idempotency-Key':str(uuid.uuid4())}).status_code==409
    act(c,t,'approve');assert c.get('/api/reports').json()[0]['rows'][0]['status']=='Submitted for Review'
    export=c.get('/api/reports/'+r['id']+'/excel');assert export.status_code==200
    from openpyxl import load_workbook
    book=load_workbook(io.BytesIO(export.content));assert book.active['D5'].value=='Submitted for Review'
    assert c.get('/api/export/tasks').status_code==200

def test_ai_disabled_and_register_controls(env):
    c,_=env;t=task(c);assert not c.get('/api/ai/status').json()['available'];assert post(c,'/ai/jobs',{'target_id':t['id']}).status_code==503
    settings=c.get('/api/settings').json();settings.update(temperature_min=18,temperature_max=25,rh_min=30,rh_max=60)
    assert c.put('/api/settings',json={'data':settings}).status_code==200
    sign(c,'thilakshana');r=post(c,'/registers/readings',{'data':{'title':'Server room','work_date':'2026-10-01','temperature':28.5,'rh':66}});assert r.status_code==200,r.text;assert len(r.json()['flags'])==2
    assert post(c,'/registers/readings',{'data':{'title':'Server room','work_date':'2026-10-01','temperature':22,'rh':101}}).status_code==422
    assert post(c,'/registers/backups',{'data':{'title':'Weekly media','systems':'ERP','backup_dates':'2026-10-01','media':'Vault reference A','handed_by':4,'receipt':'Received'}}).status_code==403

def test_login_protection_revocation_origin_and_upload_validation(env):
    c,_=env;t=task(c)
    assert c.post('/api/tasks',json={'title':'CSRF','owner':2},headers={'Origin':'https://untrusted.example'}).status_code==403
    assert c.post('/api/tasks/'+t['id']+'/attachments',data={'version':t['version']},files={'file':('evil.png',b'not an image')},headers={'Idempotency-Key':str(uuid.uuid4())}).status_code==422
    token=sign(c,'pasan');c.post('/api/logout');c.cookies.clear();assert c.get('/api/me',headers={'Authorization':'Bearer '+token}).status_code==401
    for _ in range(8): assert c.post('/api/login',json={'username':'pasan','password':'wrong'}).status_code==401
    assert c.post('/api/login',json={'username':'pasan','password':PASSWORD}).status_code==429

