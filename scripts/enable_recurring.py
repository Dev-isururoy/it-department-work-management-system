"""Run once after manager authorization; safe to repeat without duplicating schedules."""
import sys,argparse
from pathlib import Path
from datetime import date
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from backend import store as s
from backend.recurring_setup import install
parser=argparse.ArgumentParser();parser.add_argument('--as-of',required=True);args=parser.parse_args()
with s.connect() as db:
    db.execute('BEGIN IMMEDIATE')
    manager=db.execute("SELECT id FROM users WHERE role='manager' AND active=1 ORDER BY id LIMIT 1").fetchone()
    if not manager:raise RuntimeError('An active manager account is required.')
    for schedule in install(db,manager[0],date.fromisoformat(args.as_of)):
        print(schedule['title'],schedule['frequency'],schedule['start'],'owner',schedule['owner'])
