package lk.kelun.itwork;

import android.Manifest;
import android.app.*;
import android.content.*;
import android.graphics.*;
import android.net.*;
import android.os.*;
import android.provider.MediaStore;
import android.text.InputType;
import android.view.*;
import android.widget.*;
import java.io.*;
import java.net.URL;
import java.util.*;
import java.util.concurrent.*;
import org.json.*;

/** Native Android screens. The web UI is not used as a replacement client. */
public final class MainActivity extends Activity {
    private Vault vault; private Queue queue; private JSONObject session=new JSONObject(),draft;
    private LinearLayout body; private TextView banner;
    private final ExecutorService io=Executors.newSingleThreadExecutor();
    private final Handler handler=new Handler(Looper.getMainLooper());
    private final Map<String,EditText> edits=new LinkedHashMap<>();
    private Spinner status; private CheckBox submit; private JSONArray cached=new JSONArray(),equipment=new JSONArray();
    private String screen="home",businessTimezone="Asia/Colombo"; private volatile boolean refreshing=false;
    private final Runnable poll=new Runnable(){public void run(){if(!session.optString("token").isEmpty()&&screen.equals("home"))sync();handler.postDelayed(this,30000);}};
    @Override public void onCreate(Bundle saved){super.onCreate(saved);vault=new Vault(this);queue=new Queue(vault);try{session=vault.object("session");}catch(Exception e){message("Local storage could not be opened. Contact IT before clearing app data.");}if(Build.VERSION.SDK_INT>=33)requestPermissions(new String[]{Manifest.permission.POST_NOTIFICATIONS},10);SyncService.schedule(this);if(session.optString("token").isEmpty())login();else{home();sync();}handler.postDelayed(poll,30000);}
    @Override protected void onDestroy(){handler.removeCallbacks(poll);io.shutdown();super.onDestroy();}
    @Override protected void onPause(){if(draft!=null&&screen.equals("editor"))try{capture();synchronized(Queue.LOCK){queue.put(draft);}}catch(Exception e){message("Draft could not be saved: "+e.getMessage());}super.onPause();}
    @Override public void onBackPressed(){if(screen.equals("editor")){saveDraft(false);return;}super.onBackPressed();}
    private void layout(String title){
        ScrollView scroll=new ScrollView(this);body=new LinearLayout(this);body.setOrientation(LinearLayout.VERTICAL);body.setPadding(24,32,24,32);body.setBackgroundColor(Color.rgb(244,247,245));scroll.addView(body);setContentView(scroll);
        TextView brand=text("KELUN  /  IT WORK MANAGER",13);brand.setTextColor(Color.rgb(23,63,67));TextView heading=text(title,26);heading.setTypeface(null,Typeface.BOLD);banner=text("",14);banner.setTextColor(Color.rgb(128,72,24));
    }
    private TextView text(String value,int size){TextView v=new TextView(this);v.setText(value);v.setTextSize(size);v.setPadding(0,8,0,10);body.addView(v);return v;}
    private Button button(String label,Runnable fn){Button b=new Button(this);b.setText(label);b.setMinHeight(56);body.addView(b,new LinearLayout.LayoutParams(-1,-2));b.setOnClickListener(v->{try{fn.run();}catch(Exception e){message(e.getMessage());}});return b;}
    private EditText input(String label,String value,int type){text(label,13);EditText v=new EditText(this);v.setText(value);v.setInputType(type);v.setMinHeight(56);v.setSingleLine((type&InputType.TYPE_TEXT_FLAG_MULTI_LINE)==0);body.addView(v,new LinearLayout.LayoutParams(-1,-2));return v;}
    private void message(String m){runOnUiThread(()->Toast.makeText(this,m,Toast.LENGTH_LONG).show());}
    private interface Work{void run()throws Exception;}
    private void background(Work work){io.execute(()->{try{work.run();}catch(Exception e){runOnUiThread(()->{if(banner!=null)banner.setText(e instanceof Api.Failure&&((Api.Failure)e).status==401?"Session expired. Sign in again with the same account to keep queued work.":"Could not connect / save: "+e.getMessage());});}});}
    private void login(){
        if(Queue.busy){message("Synchronization is running. Wait before changing account settings.");return;}
        screen="login";draft=null;layout("Sign in");text("Use your individual account. Your manager creates and activates accounts.",14);
        EditText server=input("Server URL",session.optString("server","https://kelun-it.local"),InputType.TYPE_CLASS_TEXT|InputType.TYPE_TEXT_VARIATION_URI);
        EditText username=input("Username",session.optString("username"),InputType.TYPE_CLASS_TEXT);
        EditText password=input("Password","",InputType.TYPE_CLASS_TEXT|InputType.TYPE_TEXT_VARIATION_PASSWORD);
        button("Sign in",()->{String url=server.getText().toString().trim().replaceAll("/+$","");background(()->{
            URL parsed=new URL(url);if(parsed.getUserInfo()!=null||parsed.getQuery()!=null||parsed.getRef()!=null||!parsed.getPath().isEmpty())throw new IOException("Enter a server origin without a path, credentials, or query.");
            if(!parsed.getProtocol().equals("https")&&!BuildConfig.DEBUG)throw new IOException("HTTPS is required in release builds.");
            JSONObject current=vault.object("session");JSONObject result=new Api(new JSONObject().put("server",url)).post("/login",new JSONObject().put("username",username.getText().toString().trim()).put("password",password.getText().toString()),null);JSONObject user=result.getJSONObject("user");
            synchronized(Queue.LOCK){JSONArray pending=queue.all();if(pending.length()>0&&(current.optInt("user")!=user.getInt("id")||!current.optString("server").equals(url)))throw new IOException("Saved work belongs to another account/server. Sign in with that account and resolve drafts first.");
                session=new JSONObject().put("server",url).put("username",username.getText().toString().trim()).put("token",result.getString("token")).put("user",user.getInt("id")).put("name",user.getString("name"));vault.object("session",session);}
            runOnUiThread(()->{home();sync();});
        });});
        text("Debug builds allow HTTP only for testing on a trusted local network. Install the company’s local CA certificate for HTTPS.",13);
    }
    private void home(){
        screen="home";draft=null;layout("Hello, "+session.optString("name"));
        try{JSONObject cache=vault.object("cache");cached=cache.optJSONArray("tasks")==null?new JSONArray():cache.getJSONArray("tasks");equipment=cache.optJSONArray("equipment")==null?new JSONArray():cache.getJSONArray("equipment");businessTimezone=cache.optJSONObject("settings")==null?"Asia/Colombo":cache.getJSONObject("settings").optString("timezone","Asia/Colombo");
            banner.setText("Cached assignments · dashboard updates after sync");
            button("＋ Record work",()->{try{draft=Queue.draft(session.getInt("user"));editor();}catch(Exception e){message(e.getMessage());}});
            button("Sync now",this::sync);button("Server settings / sign in again",this::login);button("Sign out",this::logout);
            JSONArray queued; synchronized(Queue.LOCK){queued=queue.all();}
            text("Drafts & pending synchronization ("+queued.length()+")",20);
            for(int i=0;i<queued.length();i++){
                JSONObject d=queued.getJSONObject(i);String label=d.optString("title","Untitled")+" · "+d.optString("state");
                button(label,()->openDraft(d));if(!d.optString("error").isEmpty())text(d.optString("error"),12);
            }
            int today=0,overdue=0,newAssignments=0,returned=0;
            for(int i=0;i<cached.length();i++){
                JSONObject t=cached.getJSONObject(i);boolean active=!Arrays.asList("Completed","Cancelled").contains(t.optString("status"));
                if(t.optBoolean("returned"))returned++;
                JSONArray ack=t.optJSONArray("acknowledged");boolean seen=false;if(ack!=null)for(int a=0;a<ack.length();a++)if(ack.optInt(a)==session.optInt("user"))seen=true;if(active&&!seen)newAssignments++;
                if(active&&!t.optString("due").isEmpty())try{java.time.OffsetDateTime due=java.time.OffsetDateTime.parse(t.getString("due"));if(due.toInstant().isBefore(java.time.Instant.now()))overdue++;if(due.atZoneSameInstant(java.time.ZoneId.of(businessTimezone)).toLocalDate().equals(java.time.LocalDate.now(java.time.ZoneId.of(businessTimezone))))today++;}catch(Exception ignored){}
            }
            text("Today: "+today+"  ·  Overdue: "+overdue+"\nNew assignments: "+newAssignments+"  ·  Returned: "+returned,16);
            text("My assignments",20);
            for(int i=0;i<cached.length();i++){
                JSONObject t=cached.getJSONObject(i);String due=t.optString("due");String label=t.optString("number")+" · "+t.optString("title")+"\n"+t.optString("status")+" · "+t.optString("priority")+(t.optBoolean("returned")?" · Returned for correction":"")+(!due.isEmpty()?"\nDue "+due:"");
                button(label,()->taskDetail(t));
            }
            if(cached.length()==0)text("No cached assignments yet. Connect to your company network and synchronize.",14);
        }catch(Exception e){message(e.getMessage());}
    }
    private void taskDetail(JSONObject task){
        screen="task";layout(task.optString("number"));text(task.optString("title"),23);text(task.optString("description"),16);text("Status: "+task.optString("status")+"\nLocation: "+task.optString("location")+"\nRequired evidence: "+task.optString("required_evidence"),14);
        button("AI organisation (online)",()->showOrganisation(task));
        button("Acknowledge assignment",()->background(()->{new Api(session).post("/tasks/"+task.getString("id")+"/actions",new JSONObject().put("version",task.getInt("version")).put("action","acknowledge"),UUID.randomUUID().toString());runOnUiThread(()->{home();sync();});}));
        button("Record update / photos (offline available)",()->{try{draft=Queue.draft(session.getInt("user")).put("task_id",task.getString("id")).put("version",task.getInt("version")).put("title",task.optString("title")).put("description",task.optString("description")).put("location",task.optString("location")).put("equipment_id",task.optString("equipment_id")).put("checklist",task.optJSONArray("checklist")).put("checked",task.optJSONArray("checked"));editor();}catch(Exception e){message(e.getMessage());}});
        button("Back",this::home);
    }
    private void showOrganisation(JSONObject task){
        background(()->{
            JSONObject detail=new Api(session).get("/tasks/"+task.getString("id"));
            JSONObject analysis=detail.optJSONObject("analysis");
            if(analysis==null){runOnUiThread(()->message("Analysis is unavailable."));return;}
            String state=analysis.optString("status");JSONObject job=analysis.optJSONObject("job");
            if(!state.equals("ready")||job==null){runOnUiThread(()->message(state.equals("not_configured")?"AI is not connected yet. Your work is saved.":"AI organisation: "+state+". Check again after synchronization."));return;}
            JSONObject result=job.getJSONObject("result");String category=result.optString("category");
            String explanation=category+"\n"+result.optString("category_reason")+"\n\nLikely responsibility: "+result.optString("suggested_owner")+"\n"+result.optString("owner_reason")+"\n\nPriority: "+result.optString("priority")+"\n"+result.optString("priority_reason");
            runOnUiThread(()->new AlertDialog.Builder(this).setTitle("Suggested organisation").setMessage(explanation).setNegativeButton("Keep current",null).setPositiveButton("Confirm category",(d,w)->background(()->{
                JSONObject updated=new Api(session).post("/ai/jobs/"+job.getString("id")+"/accept",new JSONObject().put("version",job.getInt("source_version")).put("data",new JSONObject().put("category",category)),UUID.randomUUID().toString());
                runOnUiThread(()->taskDetail(updated));
            })).show());
        });
    }
    private void editor(){
        screen="editor";layout(draft.optString("task_id").isEmpty()?"Record work":"Update assignment");edits.clear();banner.setText("Drafts and photos stay on this phone until synchronized.");
        for(String[] field:new String[][]{{"title","Title"},{"location","Location"},{"equipment_id","Equipment ID (optional)"},{"description","Issue / original notes"},{"note","Action taken / progress"},{"blocker","Blocker / help needed"},{"summary","Completion summary"},{"results","Actual test / result details"}}){EditText e=input(field[1],draft.optString(field[0]),InputType.TYPE_CLASS_TEXT|InputType.TYPE_TEXT_FLAG_MULTI_LINE);edits.put(field[0],e);}
        if(equipment.length()>0){text("Available equipment",13);for(int i=0;i<equipment.length();i++){JSONObject asset=equipment.optJSONObject(i);button(asset.optString("asset_id")+" · "+asset.optString("name"),()->edits.get("equipment_id").setText(asset.optString("id")));}}
        text("Work status",13);status=new Spinner(this);String[] options={"In Progress","Waiting","Open","Assigned"};status.setAdapter(new ArrayAdapter<>(this,android.R.layout.simple_spinner_dropdown_item,options));status.setSelection(Math.max(0,Arrays.asList(options).indexOf(draft.optString("status","In Progress"))));body.addView(status);
        JSONArray checklist=draft.optJSONArray("checklist"),checked=draft.optJSONArray("checked");
        if(checklist!=null)for(int i=0;i<checklist.length();i++){String item=checklist.optString(i);CheckBox check=new CheckBox(this);check.setText(item);boolean done=false;if(checked!=null)for(int j=0;j<checked.length();j++)if(checked.optString(j).equals(item))done=true;check.setChecked(done);check.setTag("checklist");body.addView(check);}
        submit=new CheckBox(this);submit.setText("Submit for manager review after sync");submit.setChecked(draft.optBoolean("submit"));body.addView(submit);
        button("Take photo",()->{try{capture();synchronized(Queue.LOCK){queue.put(draft);}vault.object("capture-draft",new JSONObject().put("id",draft.getString("id")));Intent intent=new Intent(MediaStore.ACTION_IMAGE_CAPTURE);Uri uri=Uri.parse("content://lk.kelun.itwork.camera/capture.jpg");intent.putExtra(MediaStore.EXTRA_OUTPUT,uri);intent.setClipData(ClipData.newRawUri("photo",uri));intent.addFlags(Intent.FLAG_GRANT_WRITE_URI_PERMISSION|Intent.FLAG_GRANT_READ_URI_PERMISSION);startActivityForResult(intent,20);}catch(Exception e){message("No camera app available: "+e.getMessage());}});
        button("Choose photos / documents",()->{try{capture();synchronized(Queue.LOCK){queue.put(draft);}vault.object("capture-draft",new JSONObject().put("id",draft.getString("id")));Intent intent=new Intent(Intent.ACTION_OPEN_DOCUMENT).setType("*/*").addCategory(Intent.CATEGORY_OPENABLE).putExtra(Intent.EXTRA_ALLOW_MULTIPLE,true).putExtra(Intent.EXTRA_MIME_TYPES,new String[]{"image/*","application/pdf","application/vnd.openxmlformats-officedocument.spreadsheetml.sheet","application/vnd.openxmlformats-officedocument.wordprocessingml.document","text/plain","text/csv"});startActivityForResult(intent,21);}catch(Exception e){message(e.getMessage());}});
        JSONArray photos=draft.optJSONArray("photos");
        for(int i=0;photos!=null&&i<photos.length();i++){
            JSONObject p=photos.optJSONObject(i);int index=i;text(p.optString("filename")+" · "+p.optString("state","Pending"),14);
            try{byte[] raw=vault.read(p.getString("file"));BitmapFactory.Options opts=new BitmapFactory.Options();opts.inSampleSize=8;Bitmap bitmap=BitmapFactory.decodeByteArray(raw,0,raw.length,opts);if(bitmap!=null){ImageView image=new ImageView(this);image.setImageBitmap(bitmap);image.setAdjustViewBounds(true);image.setMaxHeight(240);body.addView(image);}}catch(Exception e){text("Preview unavailable",12);}
            button("Caption / Before / After",()->photoCaption(p));button("Remove local photo",()->{try{capture();vault.delete(p.getString("file"));draft.getJSONArray("photos").remove(index);synchronized(Queue.LOCK){queue.put(draft);}editor();}catch(Exception e){message(e.getMessage());}});
        }
        button("Save draft",()->saveDraft(false));button("Save & queue synchronization",()->saveDraft(true));button("Discard draft",()->new AlertDialog.Builder(this).setTitle("Discard this local draft?").setMessage("Its unsynced notes and photos will be removed from this phone.").setNegativeButton("Keep",null).setPositiveButton("Discard",(d,w)->{try{synchronized(Queue.LOCK){deleteDraftFiles(draft);queue.remove(draft.getString("id"));}draft=null;home();}catch(Exception e){message(e.getMessage());}}).show());
    }
    private void capture()throws Exception{
        if(draft==null)return;for(Map.Entry<String,EditText> entry:edits.entrySet())draft.put(entry.getKey(),entry.getValue().getText().toString());draft.put("status",status.getSelectedItem().toString()).put("submit",submit.isChecked());
        JSONArray checked=new JSONArray();for(int i=0;i<body.getChildCount();i++){View v=body.getChildAt(i);if(v instanceof CheckBox&&"checklist".equals(v.getTag())&&((CheckBox)v).isChecked())checked.put(((CheckBox)v).getText().toString());}draft.put("checked",checked);
    }
    private void saveDraft(boolean ready){try{capture();if(ready&&(draft.optString("title").trim().isEmpty()||draft.optString("note").trim().isEmpty())){message("Add a title and action taken before synchronization.");return;}draft.put("state",ready?"Pending sync":"Draft");synchronized(Queue.LOCK){queue.put(draft);}draft=null;home();if(ready)sync();}catch(Exception e){message("Could not save draft: "+e.getMessage());}}
    private void photoCaption(JSONObject photo){
        LinearLayout box=new LinearLayout(this);box.setOrientation(1);EditText caption=new EditText(this);caption.setHint("Caption");caption.setText(photo.optString("caption"));box.addView(caption);Spinner phase=new Spinner(this);String[] values={"Before","After","Evidence"};phase.setAdapter(new ArrayAdapter<>(this,android.R.layout.simple_spinner_dropdown_item,values));phase.setSelection(Math.max(0,Arrays.asList(values).indexOf(photo.optString("phase","Evidence"))));box.addView(phase);
        new AlertDialog.Builder(this).setTitle("Photo details").setView(box).setPositiveButton("Save",(d,w)->{try{capture();photo.put("caption",caption.getText().toString()).put("phase",phase.getSelectedItem().toString());synchronized(Queue.LOCK){queue.put(draft);}editor();}catch(Exception e){message(e.getMessage());}}).setNegativeButton("Cancel",null).show();
    }
    @Override protected void onActivityResult(int request,int result,Intent data){super.onActivityResult(request,result,data);if(result!=RESULT_OK)return;
        try{if(draft==null){String id=vault.object("capture-draft").getString("id");JSONArray list=queue.all();for(int i=0;i<list.length();i++)if(list.getJSONObject(i).getString("id").equals(id))draft=list.getJSONObject(i);}
            if(draft==null)throw new IOException("Draft missing; captured media was not attached.");
            if(request==20){File file=new File(getCacheDir(),"capture.jpg");attach(Api.readAll(new FileInputStream(file),20*1024*1024),"camera.jpg");file.delete();}
            if(request==21&&data!=null){if(data.getClipData()!=null)for(int i=0;i<data.getClipData().getItemCount();i++)attachUri(data.getClipData().getItemAt(i).getUri());else if(data.getData()!=null)attachUri(data.getData());}
            synchronized(Queue.LOCK){queue.put(draft);}editor();
        }catch(Exception e){message("Could not attach media: "+e.getMessage());}
    }
    private void attachUri(Uri uri)throws Exception{String name="document";try(android.database.Cursor c=getContentResolver().query(uri,new String[]{android.provider.OpenableColumns.DISPLAY_NAME},null,null,null)){if(c!=null&&c.moveToFirst())name=c.getString(0);}attach(Api.readAll(getContentResolver().openInputStream(uri),20*1024*1024),name);}
    private void attach(byte[] raw,String name)throws Exception{String id=UUID.randomUUID().toString();vault.write("photo-"+id,raw);draft.getJSONArray("photos").put(new JSONObject().put("file","photo-"+id).put("filename",name).put("key",id).put("caption","").put("phase","Evidence").put("state","Pending"));}
    private void sync(){if(refreshing||session.optString("token").isEmpty())return;refreshing=true;if(banner!=null)banner.setText("Synchronizing…");background(()->{try{queue.sync(session);Api api=new Api(session);JSONArray tasks=api.list("/tasks"),assets=api.list("/registers/equipment");vault.object("cache",new JSONObject().put("tasks",tasks).put("equipment",assets).put("settings",api.get("/settings")));SyncService.pollNotifications(this,vault,session);runOnUiThread(()->{if(screen.equals("home")){home();banner.setText("Connected · assignments refreshed. Pending conflicts need review.");}});}finally{refreshing=false;}});}
    private void openDraft(JSONObject d){
        if(Queue.busy&&!d.optString("state").equals("Draft")){message("Synchronization is running. You can review this item when it finishes.");return;}
        String status=d.optString("state");
        if(status.equals("Draft")&&d.optInt("stage")==0){draft=d;editor();return;}
        layout(d.optString("title"));screen="queue";text(status,20);text(d.optString("note"),16);text(d.optString("error"),13);
        if(status.equals("Conflict")){
            text("The server has a newer record. Your local notes and photos remain saved. Compare before making a new update; do not overwrite the server blindly.",14);
            button("Load current server record",()->background(()->{JSONObject current=new Api(session).get("/tasks/"+d.getString("task_id")).getJSONObject("task");runOnUiThread(()->new AlertDialog.Builder(this).setTitle("Current server version "+current.optInt("version")).setMessage("Status: "+current.optString("status")+"\nLatest note: "+current.optString("latest_note")+"\nSummary: "+current.optString("completion_summary")+"\n\nYour note: "+d.optString("note")).setNegativeButton("Keep conflict",null).setPositiveButton("Prepare reviewed correction",(dialog,which)->{try{if(Arrays.asList("Completed","Cancelled","Submitted for Review").contains(current.optString("status"))){message("Manager must return or reopen this record first.");return;}JSONObject correction=new JSONObject(d.toString());correction.put("id",UUID.randomUUID().toString()).put("version",current.getInt("version")).put("stage",0).put("state","Draft").put("error","");JSONArray photos=correction.getJSONArray("photos");for(int i=photos.length()-1;i>=0;i--){JSONObject p=photos.getJSONObject(i);if(p.optString("state").equals("Uploaded")){photos.remove(i);}else{p.put("key",UUID.randomUUID().toString()).put("state","Pending");p.remove("version");}}synchronized(Queue.LOCK){queue.remove(d.getString("id"));queue.put(correction);}draft=correction;editor();}catch(Exception e){message(e.getMessage());}}).show());}));
        }else if(!status.equals("Synced"))button("Retry sync",()->{try{synchronized(Queue.LOCK){d.put("state","Pending sync");queue.put(d);}home();sync();}catch(Exception e){message(e.getMessage());}});
        button(status.equals("Synced")?"Remove synced local copy":"Discard local copy",()->new AlertDialog.Builder(this).setTitle("Remove local copy?").setMessage("This removes this phone’s copy only. Unsynced changes will be lost.").setNegativeButton("Keep",null).setPositiveButton("Remove",(a,b)->{try{synchronized(Queue.LOCK){deleteDraftFiles(d);queue.remove(d.getString("id"));}home();}catch(Exception e){message(e.getMessage());}}).show());button("Back",this::home);
    }
    private void deleteDraftFiles(JSONObject d)throws Exception{JSONArray p=d.getJSONArray("photos");for(int i=0;i<p.length();i++)vault.delete(p.getJSONObject(i).getString("file"));}
    private void logout(){
        if(Queue.busy){message("Wait for synchronization before signing out.");return;}
        try{JSONArray drafts=queue.all();boolean pending=false;for(int i=0;i<drafts.length();i++)if(!drafts.getJSONObject(i).optString("state").equals("Synced"))pending=true;
            new AlertDialog.Builder(this).setTitle(pending?"Unsynced work remains":"Sign out?").setMessage(pending?"Synchronize or keep this account signed in to preserve pending work. Discard & sign out removes all local drafts and photos.":"Local cached records and session data will be cleared.").setNegativeButton("Keep signed in",null).setPositiveButton(pending?"Discard & sign out":"Sign out",(d,w)->background(()->{try{new Api(session).post("/logout",new JSONObject(),null);}catch(Exception e){throw new IOException("Connect to revoke your session before signing out. Local work was kept.");}synchronized(Queue.LOCK){vault.clear();session=new JSONObject();}runOnUiThread(this::login);})).show();
        }catch(Exception e){message(e.getMessage());}
    }
}
