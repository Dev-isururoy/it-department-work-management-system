"""Create a portable source archive, excluding all secrets, databases, and fixtures."""
from pathlib import Path
import zipfile,hashlib,json
root=Path(__file__).resolve().parents[1]
out=root/'delivery';out.mkdir(exist_ok=True)
allowed_dirs={'backend','web','android','deployment','docs','scripts','tests'}
allowed_files={'README.md','requirements.txt','requirements-dev.txt','requirements-lock.txt','.env.example','.gitignore','.dockerignore','Dockerfile','compose.yaml','start.ps1','start-local.ps1','stop-local.ps1','start.sh'}
excluded={'__pycache__','.pytest_cache','.gradle','build','node_modules','local.properties','distribution.sha256'}
destination=out/'Kelun-IT-Work-Manager-source.zip'
manifest={}
with zipfile.ZipFile(destination,'w',zipfile.ZIP_DEFLATED) as archive:
    for path in sorted(root.rglob('*')):
        if not path.is_file():continue
        rel=path.relative_to(root)
        if rel.parts[0] not in allowed_dirs and str(rel) not in allowed_files:continue
        if any(part in excluded for part in rel.parts):continue
        archive.write(path,'Kelun-IT-Work-Manager/'+rel.as_posix())
        manifest[rel.as_posix()]=hashlib.sha256(path.read_bytes()).hexdigest()
(out/'source-manifest.json').write_text(json.dumps(manifest,indent=2))
print(f'Created {destination.name}: {len(manifest)} source files, {destination.stat().st_size} bytes')
