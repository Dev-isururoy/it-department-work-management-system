package lk.kelun.itwork;
import android.app.*;
import android.app.job.*;
import android.content.*;
import android.os.Build;
import org.json.*;

/** Connectivity-constrained periodic polling; not closed-app push. */
public final class SyncService extends JobService {
    public static void schedule(Context c){JobScheduler scheduler=(JobScheduler)c.getSystemService(JOB_SCHEDULER_SERVICE);scheduler.schedule(new JobInfo.Builder(731,new ComponentName(c,SyncService.class)).setRequiredNetworkType(JobInfo.NETWORK_TYPE_ANY).setPeriodic(15*60*1000).build());}
    public boolean onStartJob(JobParameters params){new Thread(()->{try{Vault vault=new Vault(this);JSONObject session=vault.object("session");if(!session.optString("token").isEmpty()){new Queue(vault).sync(session);Api api=new Api(session);JSONArray tasks=api.list("/tasks");vault.object("cache",new JSONObject().put("tasks",tasks).put("equipment",api.list("/registers/equipment")).put("settings",api.get("/settings")));pollNotifications(this,vault,session);}}catch(Exception ignored){}finally{jobFinished(params,false);}}).start();return true;}
    public boolean onStopJob(JobParameters params){return true;}
    public static void pollNotifications(Context c,Vault vault,JSONObject session)throws Exception{
        JSONArray notices=new Api(session).list("/notifications");NotificationManager nm=(NotificationManager)c.getSystemService(Context.NOTIFICATION_SERVICE);nm.createNotificationChannel(new NotificationChannel("work","Work updates",NotificationManager.IMPORTANCE_DEFAULT));
        JSONObject delivered=vault.object("notices");
        for(int i=0;i<notices.length();i++){
            JSONObject n=notices.getJSONObject(i);String id=n.getString("id");
            if(n.optInt("seen")==0&&!delivered.optBoolean(id)){
                PendingIntent pi=PendingIntent.getActivity(c,0,new Intent(c,MainActivity.class),PendingIntent.FLAG_IMMUTABLE|PendingIntent.FLAG_UPDATE_CURRENT);
                try{nm.notify(id.hashCode(),new Notification.Builder(c,"work").setSmallIcon(android.R.drawable.ic_dialog_info).setContentTitle("Kelun IT Work Manager").setContentText(n.getString("message")).setStyle(new Notification.BigTextStyle().bigText(n.getString("message"))).setContentIntent(pi).setAutoCancel(true).build());delivered.put(id,true);}catch(SecurityException ignored){}
            }
        }
        vault.object("notices",delivered);
    }
}
