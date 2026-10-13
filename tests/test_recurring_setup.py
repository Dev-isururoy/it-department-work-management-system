from datetime import date,datetime
from zoneinfo import ZoneInfo
from tests.test_workflows import env
from backend import store as s,scheduler
from backend.recurring_setup import install

def test_requested_schedules_period_start_end_and_duplicates(env):
    c,_=env
    with s.connect() as db:
        rows=install(db,1,date(2026,10,13))
        assert len(rows)==10
        assert len([r for r in rows if r['frequency']=='weekly'])==6
        assert install(db,1,date(2026,10,13))==[]
        scheduler.tick(db,datetime(2026,10,19,0,1,tzinfo=ZoneInfo('Asia/Colombo')))
        tasks=s.listing(db,'tasks');assert len(tasks)==6
        assert all(t['due'].startswith('2026-10-25T17:00') for t in tasks)
        scheduler.tick(db,datetime(2026,10,19,0,2,tzinfo=ZoneInfo('Asia/Colombo')))
        assert len(s.listing(db,'tasks'))==6
        scheduler.tick(db,datetime(2026,11,1,0,1,tzinfo=ZoneInfo('Asia/Colombo')))
        monthly=[t for t in s.listing(db,'tasks') if t['occurrence']=='2026-11-01']
        assert len(monthly)==4 and all(t['due'].startswith('2026-11-30T17:00') for t in monthly)
        assert {t['owner'] for t in monthly}=={3,4}

def test_inactive_owners_wait_and_resume_without_duplicates(env):
    c,_=env
    with s.connect() as db:
        install(db,1,date(2026,10,13));db.execute('UPDATE users SET active=0 WHERE id=4')
        when=datetime(2026,10,19,0,1,tzinfo=ZoneInfo('Asia/Colombo'))
        scheduler.tick(db,when)
        assert len(s.listing(db,'tasks'))==5
        db.execute('UPDATE users SET active=1 WHERE id=4');scheduler.tick(db,when)
        assert len(s.listing(db,'tasks'))==6
