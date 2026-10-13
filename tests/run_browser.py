import os,sys,time,subprocess,socket,uuid
from pathlib import Path
import httpx
from PIL import Image
root=Path(__file__).resolve().parents[1];os.chdir(root)
data=root/'test-results'/('browser-'+str(uuid.uuid4()));data.mkdir(parents=True)
Image.new('RGB',(320,240),'#173f43').save(root/'test-results/evidence.png')
with socket.socket() as probe:probe.bind(('127.0.0.1',0));port=probe.getsockname()[1]
env={**os.environ,'DATA_DIR':str(data),'TEST_DATA':str(data),'PORT':str(port),'TEST_URL':f'http://127.0.0.1:{port}','AI_PROVIDER':'disabled'}
log=(root/'test-results/browser-server.log').open('w')
server=subprocess.Popen([sys.executable,'-m','backend.run'],env=env,stdout=log,stderr=log,creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
try:
    for _ in range(60):
        try:
            if httpx.get(env['TEST_URL']+'/api/health').is_success:break
        except httpx.HTTPError:pass
        time.sleep(.2)
    result=subprocess.run(['node','tests/browser.cjs'],env=env)
    sys.exit(result.returncode)
finally:server.terminate();server.wait(timeout=15);log.close()
