import os
from . import store
import uvicorn
if __name__=='__main__':
    uvicorn.run('backend.main:app',host=os.getenv('HOST','127.0.0.1'),port=int(os.getenv('PORT','8000')),workers=1,access_log=False,proxy_headers=True,forwarded_allow_ips=os.getenv('PROXY_IPS','127.0.0.1'))
