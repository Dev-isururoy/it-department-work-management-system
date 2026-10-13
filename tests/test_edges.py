from datetime import datetime,timedelta,timezone,date
from tests.test_workflows import env,task,post,act,sign
from backend import scheduler

def test_month_end_and_selected_weekdays():
    schedule={'start':'2026-01-01','frequency':'monthly','month_day':31}
    assert scheduler.matches(schedule,date(2026,2,28))
    assert not scheduler.matches(schedule,date(2026,2,27))
    schedule.update(frequency='weekdays',weekdays=[1,4]);assert scheduler.matches(schedule,date(2026,10,2));assert not scheduler.matches(schedule,date(2026,10,1))

def test_backfilled_routine_in_historical_report(env):
    c,_=env;day=(datetime.now(timezone.utc).date()-timedelta(days=3)).isoformat()
    assert post(c,'/schedules',{'title':'Backfilled routine','owner':2,'frequency':'daily','start':day}).status_code==200
    c.post('/api/schedules/run');report=post(c,'/reports',{'start':day,'end':day}).json()
    assert len(report['rows'])==1;assert report['rows'][0]['status']=='Missed occurrence — created after period end'

def test_purchase_review_cannot_be_silently_revised(env):
    c,_=env;sign(c,'pasan');data={'reference':'TEST-PR','description':'Test purchase','requester':2,'items':'One test item','owner':2,'status':'Manager Review'}
    r=post(c,'/registers/purchases',{'data':data});assert r.status_code==200;p=r.json()
    import uuid
    assert c.put('/api/registers/purchases/'+p['id'],json={'version':p['version'],'data':{**data,'status':'Draft'},'reason':'Change'},headers={'Idempotency-Key':str(uuid.uuid4())}).status_code==409
