import hashlib, secrets, time
from datetime import datetime,timedelta,timezone
from fastapi import HTTPException, Request
from argon2 import PasswordHasher
from argon2.exceptions import VerificationError, InvalidHashError
from . import store as s
ph=PasswordHasher(time_cost=3,memory_cost=65536,parallelism=2)
DUMMY=ph.hash(secrets.token_urlsafe(32))
def digest(value): return hashlib.sha256(value.encode()).hexdigest()
def hash_password(password):
    if len(password)<12: raise HTTPException(422,'Use at least 12 characters for passwords.')
    return ph.hash(password)
def verify(hashed,password):
    try: return ph.verify(hashed or DUMMY,password)
    except (VerificationError,InvalidHashError): return False
def token(request):
    auth=request.headers.get('authorization','')
    return auth[7:] if auth.startswith('Bearer ') else request.cookies.get('kelun_session','')
def authenticate(db,request):
    value=token(request)
    row=db.execute('SELECT u.* FROM users u JOIN sessions t ON u.id=t.user_id WHERE t.hash=? AND t.expires>? AND u.active=1',(digest(value),s.now())).fetchone()
    if not row: raise HTTPException(401,'Please sign in.')
    return {k:row[k] for k in ['id','name','username','role','active']}
def manager(user):
    if user['role']!='manager': raise HTTPException(403,'Manager access required.')
def can_task(user,task): return user['role']=='manager' or user['id']==task['owner'] or user['id'] in task.get('supporters',[])
def task_access(user,task):
    if not task or task['kind']!='tasks': raise HTTPException(404,'Task not found.')
    if not can_task(user,task): raise HTTPException(403,'This task is not assigned or shared with you.')
def issue(db,user):
    value=secrets.token_urlsafe(48)
    db.execute('INSERT INTO sessions VALUES(?,?,?)',(digest(value),user['id'],(datetime.now(timezone.utc)+timedelta(hours=12)).isoformat()))
    return value
