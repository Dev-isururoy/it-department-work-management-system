import json, calendar
from datetime import datetime,date,timedelta,time
from zoneinfo import ZoneInfo
from . import store as s
from .tasks import create

def matches(schedule,day):
    start=date.fromisoformat(schedule['start'])
    if day<start: return False
    f=schedule['frequency']
    return f=='daily' or (f=='weekly' and day.weekday()==start.weekday()) or (f=='weekdays' and day.weekday() in schedule['weekdays']) or (f=='monthly' and day.day==min(schedule['month_day'],calendar.monthrange(day.year,day.month)[1]))
def tick(db,instant=None):
    settings=json.loads(db.execute('SELECT body FROM settings WHERE id=1').fetchone()[0]);tz=ZoneInfo(settings['timezone'])
    instant=instant or datetime.now(tz);today=instant.astimezone(tz).date()
    manager=db.execute("SELECT id,role FROM users WHERE active=1 AND role='manager' ORDER BY id LIMIT 1").fetchone()
    if not manager: return
    for schedule in s.listing(db,'schedules'):
        if schedule['paused']: continue
        if not db.execute('SELECT 1 FROM users WHERE id=? AND active=1',(schedule['owner'],)).fetchone(): continue
        day=date.fromisoformat(schedule.get('next_scan',schedule['start']))
        scanned=0
        while day<=today and scanned<400:
            if matches(schedule,day) and not db.execute('SELECT 1 FROM occurrences WHERE schedule_id=? AND day=?',(schedule['id'],day.isoformat())).fetchone():
                due_day=day
                if schedule.get('due_at_period_end'):
                    if schedule['frequency']=='weekly':due_day=day+timedelta(days=6)
                    elif schedule['frequency']=='monthly':due_day=day.replace(day=calendar.monthrange(day.year,day.month)[1])
                due=datetime.combine(due_day,time.fromisoformat(schedule['due_time']),tz).isoformat()
                task=create(db,dict(manager),dict(title=schedule['title'],description=schedule['description'],category=schedule['category'],owner=schedule['owner'],due=due,required_evidence=schedule['required_evidence'],review_required=schedule['review_required']))
                task.update(schedule_id=schedule['id'],occurrence=day.isoformat(),missed_occurrence=day<today)
                task=s.save(db,task,None,'schedule occurrence')
                from .intelligence import enqueue
                enqueue(db,dict(manager),task,automatic=True)
                db.execute('INSERT INTO occurrences VALUES(?,?,?)',(schedule['id'],day.isoformat(),task['id']))
            day+=timedelta(days=1);scanned+=1
        if scanned:
            schedule['next_scan']=day.isoformat();s.save(db,schedule,None,'scheduler cursor')
    for task in s.listing(db,'tasks'):
        if task['status'] in ['Completed','Cancelled'] or not task['due']: continue
        due=datetime.fromisoformat(task['due'])
        if due<=instant+timedelta(hours=24):
            label='Overdue' if due<instant else 'Due within 24 hours'
            s.notify(db,[task['owner'],*s.managers(db)],f"{label}: {task['number']} — {task['title']}",task['id'],f"{label}:{task['id']}:{task['due']}")
