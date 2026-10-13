package lk.kelun.itwork;

import org.json.*;
import java.util.UUID;

/** The UI and background job serialize queue mutations on LOCK. */
public final class Queue {
    public static final Object LOCK=new Object();
    private static final Object SYNC_LOCK=new Object();
    public static volatile boolean busy=false;
    private final Vault vault;
    public Queue(Vault v){vault=v;}
    public JSONArray all()throws Exception{synchronized(LOCK){JSONObject value=vault.object("queue");return value.optJSONArray("drafts")==null?new JSONArray():value.getJSONArray("drafts");}}
    public void save(JSONArray list)throws Exception{synchronized(LOCK){vault.object("queue",new JSONObject().put("drafts",list));}}
    public void put(JSONObject draft)throws Exception{synchronized(LOCK){JSONArray list=all();boolean found=false;for(int i=0;i<list.length();i++)if(list.getJSONObject(i).getString("id").equals(draft.getString("id"))){list.put(i,draft);found=true;}if(!found)list.put(draft);save(list);}}
    public void remove(String id)throws Exception{synchronized(LOCK){JSONArray list=all();for(int i=list.length()-1;i>=0;i--)if(list.getJSONObject(i).getString("id").equals(id))list.remove(i);save(list);}}
    public static JSONObject draft(int user)throws Exception{return new JSONObject().put("id",UUID.randomUUID().toString()).put("user",user).put("title","").put("description","").put("location","").put("note","").put("task_id","").put("stage",0).put("photos",new JSONArray()).put("state","Draft").put("submit",false);}
    public void sync(JSONObject session)throws Exception{
        synchronized(SYNC_LOCK){
            busy=true;
            try {
            if(session.optString("token").isEmpty())return;
            Api api=new Api(session);JSONArray drafts=all();
            for(int i=0;i<drafts.length();i++){
                JSONObject d=drafts.getJSONObject(i);
                if(d.getInt("user")!=session.getInt("user")||d.optString("state").equals("Draft")||d.optString("state").equals("Synced")||d.optString("state").equals("Conflict"))continue;
                try{
                    d.put("state","Syncing");put(d);
                    String id=d.getString("id");
                    if(d.getInt("stage")==0){
                        if(d.optString("task_id").isEmpty()){
                            JSONObject payload=new JSONObject().put("title",d.getString("title")).put("description",d.optString("description")).put("location",d.optString("location")).put("equipment_id",d.optString("equipment_id")).put("owner",d.getInt("user"));
                            JSONObject task=api.post("/tasks",payload,id+"-create");d.put("task_id",task.getString("id"));d.put("version",task.getInt("version"));
                        }
                        d.put("stage",1);put(d);
                    }
                    if(d.getInt("stage")==1){
                        JSONObject progress=new JSONObject().put("note",d.optString("note")).put("status",d.optString("status","In Progress")).put("blocker",d.optString("blocker")).put("completion_summary",d.optString("summary")).put("test_results",d.optString("results"));
                        if(d.has("checked"))progress.put("checked",d.getJSONArray("checked"));
                        JSONObject response=api.post("/tasks/"+d.getString("task_id")+"/actions",new JSONObject().put("version",d.getInt("version")).put("action","update").put("data",progress),id+"-progress");
                        d.put("version",response.getInt("version")).put("stage",2);put(d);
                    }
                    if(d.getInt("stage")==2){
                        JSONArray photos=d.getJSONArray("photos");
                        for(int p=0;p<photos.length();p++){
                            JSONObject photo=photos.getJSONObject(p);if(photo.optString("state").equals("Uploaded"))continue;
                            if(!photo.has("version"))photo.put("version",d.getInt("version"));photo.put("state","Uploading");put(d);
                            api.upload(d.getString("task_id"),photo,photo.getInt("version"),vault.read(photo.getString("file")));
                            photo.put("state","Uploaded");d.put("version",photo.getInt("version")+1);put(d);
                        }
                        d.put("stage",3);put(d);
                    }
                    if(d.getInt("stage")==3&&d.optBoolean("submit")){
                        JSONObject response=api.post("/tasks/"+d.getString("task_id")+"/actions",new JSONObject().put("version",d.getInt("version")).put("action","submit").put("data",new JSONObject()),id+"-submit");d.put("version",response.getInt("version"));
                    }
                    d.put("stage",4).put("state","Synced").put("error","");put(d);
                }catch(Api.Failure e){d.put("state",e.status==409?"Conflict":"Failed").put("error",e.getMessage());markFailedPhotos(d);put(d);if(e.status==401)throw e;}
                catch(Exception e){d.put("state","Pending sync").put("error","Connection unavailable; retry when connected.");markFailedPhotos(d);put(d);}
            }
            } finally { busy=false; }
        }
    }
    private void markFailedPhotos(JSONObject d)throws Exception{JSONArray p=d.getJSONArray("photos");for(int i=0;i<p.length();i++)if(p.getJSONObject(i).optString("state").equals("Uploading"))p.getJSONObject(i).put("state","Failed");}
}
