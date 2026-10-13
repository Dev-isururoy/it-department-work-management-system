import os, json, sqlite3, secrets, uuid
from pathlib import Path
from datetime import datetime, timezone
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / '.env')
DATA = Path(os.getenv('DATA_DIR', str(ROOT / 'data'))).resolve()
def now(): return datetime.now(timezone.utc).isoformat()
def uid(): return str(uuid.uuid4())
def encode(value): return json.dumps(value, ensure_ascii=False, separators=(',', ':'))
class Connection(sqlite3.Connection):
    def __exit__(self,*args):
        try: return super().__exit__(*args)
        finally: self.close()
def connect():
    db = sqlite3.connect(DATA / 'kelun.sqlite3', timeout=30, check_same_thread=False,factory=Connection)
    db.row_factory = sqlite3.Row
    db.execute('PRAGMA foreign_keys=ON')
    db.execute('PRAGMA busy_timeout=30000')
    return db
def initialize():
    DATA.mkdir(parents=True, exist_ok=True)
    if os.name!='nt':DATA.chmod(0o700)
    (DATA / 'attachments').mkdir(exist_ok=True)
    with connect() as db:
        db.execute('PRAGMA journal_mode=WAL')
        db.execute('CREATE TABLE IF NOT EXISTS schema_migrations(version TEXT PRIMARY KEY, applied TEXT NOT NULL)')
        for path in sorted((ROOT / 'backend/migrations').glob('*.sql')):
            if db.execute('SELECT 1 FROM schema_migrations WHERE version=?',(path.stem,)).fetchone(): continue
            db.executescript(path.read_text())
            db.execute('INSERT OR IGNORE INTO schema_migrations VALUES(?,?)',(path.stem,now()))
        db.execute('INSERT OR IGNORE INTO settings VALUES(1,?)', (encode({'timezone':'Asia/Colombo','temperature_min':None,'temperature_max':None,'rh_min':None,'rh_max':None,'retention_days':None,'categories':['Infrastructure','Access management','Documentation','Backups','Support','Routine check']}),))
        if not get(db,'department-knowledge'):
            insert(db,'department_knowledge',json.loads((ROOT/'backend/seeds/department_knowledge.json').read_text(encoding='utf-8')),None,'import department reference',id='department-knowledge')
        if not db.execute('SELECT 1 FROM users').fetchone():
            for name in ['Isuru','Pasan','Wathsala','Thilakshana']:
                db.execute('INSERT INTO users(name,username,role) VALUES(?,?,?)',(name,name.lower(),'manager' if name=='Isuru' else 'member'))
            for item in json.loads((ROOT/'backend/seeds/responsibilities.json').read_text(encoding='utf-8')):
                insert(db,'responsibilities',item,None,'seed')
    if not (DATA/'.setup-key').exists():
        (DATA/'.setup-key').write_text(secrets.token_urlsafe(32))
        if os.name!='nt':(DATA/'.setup-key').chmod(0o600)
def rowdoc(row):
    if row is None: return None
    return {**json.loads(row['body']), 'id':row['id'],'kind':row['kind'],'version':row['version'],'created':row['created'],'updated':row['updated'],'archived':bool(row['archived'])}
def get(db, id): return rowdoc(db.execute('SELECT * FROM documents WHERE id=?',(id,)).fetchone())
def listing(db,kind,archived=False):
    return [rowdoc(r) for r in db.execute('SELECT * FROM documents WHERE kind=? AND archived=? ORDER BY created DESC',(kind,int(archived)))]
def audit(db,entity,actor,action,snapshot,reason=''):
    db.execute('INSERT INTO history(entity,actor,action,at,snapshot,reason) VALUES(?,?,?,?,?,?)',(entity,actor,action,now(),encode(snapshot),reason))
def insert(db,kind,body,actor,action='create',id=None):
    id=id or uid(); at=now()
    db.execute('INSERT INTO documents(id,kind,body,created,updated) VALUES(?,?,?,?,?)',(id,kind,encode(body),at,at))
    result=get(db,id); audit(db,id,actor,action,result); return result
def save(db,doc,actor,action,reason=''):
    body={k:v for k,v in doc.items() if k not in ['id','kind','version','created','updated','archived']}
    db.execute('UPDATE documents SET body=?,version=version+1,updated=?,archived=? WHERE id=?',(encode(body),now(),int(doc.get('archived',False)),doc['id']))
    result=get(db,doc['id']); audit(db,doc['id'],actor,action,result,reason); return result
def notify(db,users,message,task=None,dedupe=None):
    for user in set(users):
        if user:
            db.execute('INSERT OR IGNORE INTO notifications VALUES(?,?,?,?,?,0,?)',(uid(),user,message,task,now(),f'{dedupe}:{user}' if dedupe else None))
def managers(db): return [r[0] for r in db.execute("SELECT id FROM users WHERE active=1 AND role='manager'")]
