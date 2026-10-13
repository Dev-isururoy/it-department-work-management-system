import argparse,sys,json
from pathlib import Path
from datetime import datetime,timedelta,timezone
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from backend import store as s
parser=argparse.ArgumentParser();parser.add_argument('command',choices=['setup-key','retention-review','check']);args=parser.parse_args();s.initialize()
if args.command=='setup-key':
    with s.connect() as db:
        if db.execute("SELECT 1 FROM users WHERE role='manager' AND password IS NOT NULL").fetchone(): print('Setup already completed. Manage accounts in the application.')
        else: print('First-run setup key (keep private):\n'+(s.DATA/'.setup-key').read_text())
elif args.command=='check':
    with s.connect() as db: print('Database:',db.execute('PRAGMA integrity_check').fetchone()[0]);print('Migrations:',[r[0] for r in db.execute('SELECT version FROM schema_migrations')])
else:
    with s.connect() as db:
        settings=json.loads(db.execute('SELECT body FROM settings').fetchone()[0]);days=settings.get('retention_days')
        if not days: print('Retention review age is not configured.')
        else:
            cutoff=(datetime.now(timezone.utc)-timedelta(days=days)).isoformat()
            for task in s.listing(db,'tasks'):
                if task['updated']<cutoff and task['status'] in ['Completed','Cancelled']: print(task['number'],task['title'],'— candidate for manager archival review')
            print('No data was changed or deleted.')
