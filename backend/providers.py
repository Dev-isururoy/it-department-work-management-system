"""Optional providers implement a small common interface. No provider acts on records."""
import os,json
from typing import Protocol
import httpx

class AIProvider(Protocol):
    def analyze(self,system:str,content:str,images:list[str])->dict: ...

class OllamaProvider:
    def __init__(self,model):self.model=model
    def analyze(self,system,content,images):
        from .intelligence import Suggestion
        schema=Suggestion.model_json_schema()
        context=json.loads(content)['context']
        schema['properties']['category']['enum']=context['allowed_categories']
        schema['properties']['priority']['enum']=['Low','Normal','High','Critical']
        schema['properties']['confidence']['enum']=['low','medium','high']
        schema['properties']['suggested_owner']['enum']=['',*[u['name'] for u in context['users']]]
        schema['required']=list(schema['properties'])
        response=httpx.post(os.getenv('AI_BASE_URL','http://127.0.0.1:11434').rstrip('/')+'/api/chat',json={'model':self.model,'stream':False,'format':schema,'options':{'temperature':0,'num_ctx':16384,'num_predict':1400},'messages':[{'role':'system','content':system+' Keep every explanation brief. Return valid JSON only.'},{'role':'user','content':content,'images':images}]},timeout=float(os.getenv('AI_TIMEOUT_SECONDS','900')))
        response.raise_for_status();return json.loads(response.json()['message']['content'])

class ExternalProvider:
    def __init__(self,model):self.model=model
    def analyze(self,system,content,images):
        if os.getenv('AI_EXTERNAL_ENABLED','false').lower()!='true':raise ValueError('External data transfer is disabled')
        url=os.getenv('AI_BASE_URL','').rstrip('/')+'/chat/completions'
        if not url.startswith('https://'):raise ValueError('External provider requires HTTPS')
        parts=[{'type':'text','text':content}]+[{'type':'image_url','image_url':{'url':'data:image/jpeg;base64,'+img}} for img in images]
        response=httpx.post(url,headers={'Authorization':'Bearer '+os.getenv('AI_API_KEY','')},json={'model':self.model,'messages':[{'role':'system','content':system},{'role':'user','content':parts}],'response_format':{'type':'json_object'}},timeout=180)
        response.raise_for_status();return json.loads(response.json()['choices'][0]['message']['content'])

def provider(name,model)->AIProvider:
    if name=='ollama':return OllamaProvider(model)
    if name=='external':return ExternalProvider(model)
    raise ValueError('AI is not configured')
