import json,uuid
import pytest
from tests.test_workflows import env,sign,task,post,act
from backend import store as s,intelligence as ai

def enable(monkeypatch):
    monkeypatch.setenv('AI_PROVIDER','ollama')
    monkeypatch.setenv('AI_MODEL','test-fixture-only')

def finish(monkeypatch):
    captured=[]
    class Fixture:
        def analyze(self,system,content,images):
            context=json.loads(content)['context'];captured.append(context)
            return {'category':context['allowed_categories'][1],'category_reason':'Controlled test explanation',
                    'suggested_owner':'Pasan','owner_reason':'Reference responsibility',
                    'matched_responsibility_ids':['work-1'],'priority':'Normal','confidence':'medium'}
    monkeypatch.setattr(ai,'provider',lambda *args:Fixture())
    with s.connect() as db:
        for j in s.listing(db,'ai_jobs'):
            if j['status']=='queued':
                j['not_before']='';s.save(db,j,None,'test due')
    ai.process_one()
    return captured

def test_reference_is_background_and_disabled_is_honest(env):
    c,_=env;k=c.get('/api/ai/knowledge').json()
    assert len(k['work'])==43 and len(k['reviews'])==6
    assert c.get('/api/tasks').json()==[]
    assert c.get('/api/schedules').json()==[]
    t=task(c);detail=c.get('/api/tasks/'+t['id']).json()
    assert t['category']=='Uncategorized'
    assert detail['analysis']['status']=='not_configured'
    assert c.get('/api/ai/jobs').json()==[]

def test_auto_analysis_member_confirmation_and_preserved_notes(env,monkeypatch):
    c,_=env;private=task(c,owner=3,title='Private unrelated work')
    enable(monkeypatch);sign(c,'pasan')
    t=task(c,description='Actual original clock check notes')
    jobs=c.get('/api/ai/jobs').json();assert len(jobs)==1 and jobs[0]['automatic']
    assert 'context' not in jobs[0]
    assert post(c,'/ai/jobs',{'target_id':t['id']}).json()['id']==jobs[0]['id']
    payload=finish(monkeypatch)[0]
    assert len(payload['department_knowledge']['work'])==43
    assert private['id'] not in [v['id'] for v in payload['related_authorized_records']]
    detail=c.get('/api/tasks/'+t['id']).json();j=detail['analysis']['job']
    assert detail['analysis']['status']=='ready'
    assert detail['task']['category']=='Uncategorized'
    assert post(c,'/ai/jobs/'+j['id']+'/accept',{'version':t['version'],'data':{'owner':2}}).status_code==403
    result=post(c,'/ai/jobs/'+j['id']+'/accept',{'version':t['version'],'data':{'category':j['result']['category']}})
    assert result.status_code==200,result.text
    assert result.json()['description']==t['description'] and result.json()['owner']==2
    assert c.get('/api/tasks/'+t['id']).json()['analysis']['status']=='accepted'

def test_new_notes_supersede_analysis_and_knowledge_edit_permissions(env,monkeypatch):
    c,_=env;enable(monkeypatch);sign(c,'pasan');t=task(c)
    first=c.get('/api/ai/jobs').json()[0]
    t=act(c,t,'update',{'note':'Further details','status':'In Progress'}).json()
    jobs=c.get('/api/ai/jobs').json()
    assert next(j for j in jobs if j['id']==first['id'])['status']=='superseded'
    assert len([j for j in jobs if j['status']=='queued'])==1
    finish(monkeypatch)
    k=c.get('/api/ai/knowledge').json();data={'version':k['version'],'data':{'work':k['work'],'reviews':k['reviews']},'reason':'Clarify reference'}
    assert c.put('/api/ai/knowledge',json=data,headers={'Idempotency-Key':str(uuid.uuid4())}).status_code==403
    sign(c,'isuru');data['data']['work'][0]['responsibility']='Compare clocks with approved reference'
    assert c.put('/api/ai/knowledge',json=data,headers={'Idempotency-Key':str(uuid.uuid4())}).status_code==200
    other=task(c)
    with s.connect() as db:
        job=next(j for j in s.listing(db,'ai_jobs') if j['target_id']==other['id'])
        assert job['context']['department_knowledge']['work'][0]['responsibility']=='Compare clocks with approved reference'

@pytest.mark.parametrize('invalid',[{'category':'Invented'}, {'suggested_owner':'Unknown person'}, {'matched_responsibility_ids':['invented']}, {'related_task_ids':['private-id']}, {'confidence':'certain'}])
def test_unrecognized_model_results_rejected(invalid):
    with pytest.raises(ValueError):
        ai.validate_result(invalid,{'allowed_categories':['Uncategorized'],'users':[],'department_knowledge':{'work':[]},'related_authorized_records':[]})

