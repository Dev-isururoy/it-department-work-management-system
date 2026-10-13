"""Stop the server first. Produce a consistent database + attachment backup."""
import sys,sqlite3,zipfile,json,hashlib,argparse,tempfile,shutil
from pathlib import Path
from datetime import datetime,timezone
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from backend import store as s

def backup(destination):
    destination=Path(destination).resolve()
    if destination.exists(): raise ValueError('Backup destination exists; choose a new filename.')
    destination.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory() as work:
        dbpath=Path(work)/'kelun.sqlite3'
        with s.connect() as source,sqlite3.connect(dbpath,factory=s.Connection) as target: source.backup(target)
        with sqlite3.connect(dbpath,factory=s.Connection) as db:
            if db.execute('PRAGMA integrity_check').fetchone()[0]!='ok': raise ValueError('Database integrity check failed.')
            refs=[(r[0],json.loads(r[1])) for r in db.execute("SELECT id,body FROM documents WHERE kind='attachments'")]
        files=[(dbpath,'kelun.sqlite3')]
        for aid,record in refs:
            path=s.DATA/'attachments'/aid
            if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest()!=record['sha256']: raise ValueError('Missing or damaged attachment: '+aid)
            files.append((path,'attachments/'+aid))
            if record['thumbnail']: files.append((s.DATA/'attachments'/(aid+'.thumb'),'attachments/'+aid+'.thumb'))
        manifest={'created':datetime.now(timezone.utc).isoformat(),'files':{name:hashlib.sha256(path.read_bytes()).hexdigest() for path,name in files}}
        with zipfile.ZipFile(destination,'w',zipfile.ZIP_DEFLATED) as archive:
            for path,name in files: archive.write(path,name)
            archive.writestr('manifest.json',json.dumps(manifest,indent=2))
    return manifest

def restore(source,destination):
    target=Path(destination).resolve()
    if target.exists() and any(target.iterdir()): raise ValueError('Restore destination must be empty. Existing data will not be overwritten.')
    with zipfile.ZipFile(source) as archive:
        manifest=json.loads(archive.read('manifest.json'))
        for name,digest in manifest['files'].items():
            resolved=(target/name).resolve()
            if not resolved.is_relative_to(target) or name.startswith(('/', '\\')): raise ValueError('Unsafe backup path.')
            raw=archive.read(name)
            if hashlib.sha256(raw).hexdigest()!=digest: raise ValueError('Backup checksum mismatch: '+name)
        target.mkdir(parents=True,exist_ok=True)
        for name in manifest['files']:
            path=target/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(archive.read(name))
    with sqlite3.connect(target/'kelun.sqlite3',factory=s.Connection) as db:
        if db.execute('PRAGMA integrity_check').fetchone()[0]!='ok': raise ValueError('Restored database integrity check failed.')
        # Revoke all pre-backup sessions on restore.
        db.execute('DELETE FROM sessions');db.commit()
    return manifest
if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='command',required=True)
    b=sub.add_parser('create');b.add_argument('destination');b.add_argument('--server-stopped',action='store_true',required=True)
    r=sub.add_parser('restore');r.add_argument('source');r.add_argument('destination')
    args=parser.parse_args()
    print(json.dumps(backup(args.destination) if args.command=='create' else restore(args.source,args.destination),indent=2))
