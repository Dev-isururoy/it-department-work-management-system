import json,uuid,threading,time,io
from datetime import datetime,timedelta,timezone
from tests.test_workflows import env,task,post,act,sign,picture
from backend import store as s,ai
from scripts.backup import backup,restore

def test_backup_restores_records_and_attachment_files(env,tmp_path):
    c,data=env;t=task(c)
    r=c.post('/api/tasks/'+t['id']+'/attachments',data={'version':t['version']},files={'file':('evidence.png',picture(),'image/png')},headers={'Idempotency-Key':str(uuid.uuid4())});assert r.status_code==200
    a=r.json();path=data/'backup.zip';manifest=backup(path);target=data/'restored';restore(path,target)
    import sqlite3
    with sqlite3.connect(target/'kelun.sqlite3') as db:
        assert db.execute('SELECT count(*) FROM documents WHERE id=?',(t['id'],)).fetchone()[0]==1
        assert db.execute('SELECT count(*) FROM sessions').fetchone()[0]==0
    assert (target/'attachments'/a['id']).read_bytes()==picture()
    assert (target/'attachments'/(a['id']+'.thumb')).is_file()
    import pytest
    with pytest.raises(ValueError):restore(path,target)

def test_report_prior_work_recent_progress_and_future_exclusion(env):
    c,_=env;t=task(c);now=datetime.now(timezone.utc);old=(now-timedelta(days=20)).isoformat()
    # Fixture preparation is allowed to rebuild history; production SQL prevents updates.
    with s.connect() as db:
        db.execute('DROP TRIGGER history_no_update');db.execute('UPDATE history SET at=? WHERE entity=?',(old,t['id']));db.execute("CREATE TRIGGER history_no_update BEFORE UPDATE ON history BEGIN SELECT RAISE(ABORT,'History is append-only'); END;")
    sign(c,'pasan');t=act(c,t,'update',{'note':'Meaningful work today'}).json();sign(c,'isuru');day=now.date().isoformat();report=post(c,'/reports',{'start':day,'end':day}).json();assert len(report['rows'])==1;assert report['rows'][0]['activity']=='Meaningful work today'
    older=(now-timedelta(days=10)).date().isoformat();prior=post(c,'/reports',{'start':older,'end':older}).json();assert prior['rows'][0]['status']=='Assigned';assert prior['rows'][0]['activity']!='Meaningful work today'

def test_ai_provider_adapter_suggestions_separate_until_accept(env,monkeypatch):
    c,_=env;t=task(c);monkeypatch.setenv('AI_PROVIDER','ollama');monkeypatch.setenv('AI_MODEL','test-fixture')
    class Response:
        def raise_for_status(self):pass
        def json(self):return {'message':{'content':json.dumps({'title':'Suggested title','description':'Suggested description','priority':'High','priority_reason':'Recorded production impact','observations':['Fixture only'],'assumptions':[]})}}
    monkeypatch.setattr(ai.httpx,'post',lambda *a,**kw:Response())
    job=post(c,'/ai/jobs',{'target_id':t['id']});assert job.status_code==200;job=job.json()
    ai.process_one();assert c.get('/api/tasks/'+t['id']).json()['task']['title']==t['title']
    j=c.get('/api/ai/jobs').json()[0];assert j['status']=='ready' and j['provider']=='ollama' and j['processing_seconds']>=0
    sign(c,'pasan');assert post(c,'/ai/jobs/'+job['id']+'/accept',{'version':t['version'],'data':{'title':'Suggested title'}}).status_code==403
    sign(c,'isuru');result=post(c,'/ai/jobs/'+job['id']+'/accept',{'version':t['version'],'data':{'title':'Suggested title'}});assert result.status_code==200,result.text
    history=c.get('/api/tasks/'+t['id']).json()['history'];assert history[0]['snapshot']['title']==t['title'];assert history[-1]['snapshot']['title']=='Suggested title'

def test_member_support_and_private_leave(env):
    c,_=env;t=task(c,supporters=[3]);sign(c,'wathsala');assert c.get('/api/tasks').json()[0]['id']==t['id'];assert act(c,t,'update',{'note':'Supporting the inspection'}).status_code==200
    req=post(c,'/registers/leave',{'data':{'title':'Leave','member':3,'start':'2026-10-05','end':'2026-10-05','reason':'Personal','decision':'Pending'}});assert req.status_code==200,req.text
    sign(c,'pasan');assert c.get('/api/registers/leave').json()==[]
    sign(c,'isuru');assert len(c.get('/api/registers/leave').json())==1

def test_unplanned_invalid_progress_and_database_restart(env):
    c,path=env;sign(c,'pasan');t=task(c,title='Unplanned network repair',review_required=False);assert t['review_required']
    assert act(c,t,'update',{'note':{'bad':'type'}}).status_code==422
    assert act(c,t,'update',{'effort_minutes':-1}).status_code==422
    s.initialize()
    assert c.get('/api/tasks/'+t['id']).json()['task']['title']=='Unplanned network repair'
