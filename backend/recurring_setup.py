"""Explicit, idempotent setup of the user's weekly/monthly department work."""
from datetime import date,timedelta
from . import store as s
from .models import Schedule

def install(db,actor,today):
    knowledge=s.get(db,'department-knowledge')
    users={r['name']:r['id'] for r in db.execute('SELECT id,name FROM users')}
    existing=s.listing(db,'schedules');created=[]
    for row in knowledge['work']:
        frequency=row['frequency'].lower()
        if frequency=='weekly':
            cadence='weekly';start=today+timedelta(days=7-today.weekday())
        elif frequency.startswith('monthly'):
            cadence='monthly';start=date(today.year+(today.month==12),today.month%12+1,1)
        else:continue
        if any(r.get('responsibility_id')==row['id'] or (r['title']==row['work_area'] and r['owner']==users[row['owner']] and r['frequency']==cadence) for r in existing):continue
        description=row['responsibility']
        if row['id']=='work-22':description='Record monthly printer count readings and check rented black-and-white printer rental bills. Coordinate discrepancies with the rental vendor.'
        if row['review_or_handover']:description+='\nReview / handover: '+row['review_or_handover']
        category='Backups' if 'Backup' in row['work_area'] else 'Documentation' if row['id'] in ['work-15','work-20','work-22','work-40'] else 'Routine check'
        data=Schedule(title=row['work_area'],owner=users[row['owner']],frequency=cadence,start=start.isoformat(),due_at_period_end=True,description=description,category=category,responsibility_id=row['id']).model_dump()
        created.append(s.insert(db,'schedules',data,actor,'enable requested automatic weekly/monthly work'))
    return created
