package lk.kelun.itwork;

import java.io.*;
import java.net.*;
import java.nio.charset.StandardCharsets;
import org.json.*;

/** No redirects: never forwards a session to a different host. */
public final class Api {
    public static final class Failure extends IOException {
        public final int status;
        public Failure(int code,String text){super(text);status=code;}
    }
    private final String base,token;
    public Api(JSONObject session){base=session.optString("server").replaceAll("/+$","");token=session.optString("token");}
    private HttpURLConnection open(String path,String method,String key) throws Exception {
        URL url=new URL(base+"/api"+path);
        HttpURLConnection c=(HttpURLConnection)url.openConnection();c.setRequestMethod(method);c.setConnectTimeout(15000);c.setReadTimeout(45000);c.setInstanceFollowRedirects(false);
        c.setRequestProperty("X-Kelun-Client","android");
        if(!token.isEmpty())c.setRequestProperty("Authorization","Bearer "+token);
        if(key!=null)c.setRequestProperty("Idempotency-Key",key);
        return c;
    }
    private String response(HttpURLConnection c)throws Exception{
        try{int code=c.getResponseCode();InputStream stream=code>=200&&code<300?c.getInputStream():c.getErrorStream();String text=stream==null?"HTTP "+code:new String(readAll(stream,4*1024*1024),StandardCharsets.UTF_8);if(code<200||code>=300)throw new Failure(code,text);return text;}finally{c.disconnect();}
    }
    public String request(String method,String path,JSONObject data,String key)throws Exception{
        HttpURLConnection c=open(path,method,key);
        if(data!=null){c.setDoOutput(true);c.setRequestProperty("Content-Type","application/json");byte[] raw=data.toString().getBytes(StandardCharsets.UTF_8);c.setFixedLengthStreamingMode(raw.length);try(OutputStream out=c.getOutputStream()){out.write(raw);}}
        return response(c);
    }
    public JSONObject get(String path)throws Exception{return new JSONObject(request("GET",path,null,null));}
    public JSONArray list(String path)throws Exception{return new JSONArray(request("GET",path,null,null));}
    public JSONObject post(String path,JSONObject data,String key)throws Exception{return new JSONObject(request("POST",path,data,key));}
    public JSONObject upload(String task,JSONObject photo,int version,byte[] bytes)throws Exception{
        String boundary="Kelun"+photo.getString("key");ByteArrayOutputStream buffer=new ByteArrayOutputStream();
        String[][] fields={{"version",String.valueOf(version)},{"caption",photo.optString("caption")},{"phase",photo.optString("phase","Evidence")},{"work_time",photo.optString("work_time")}};
        for(String[] field:fields)buffer.write(("--"+boundary+"\r\nContent-Disposition: form-data; name=\""+field[0]+"\"\r\n\r\n"+field[1]+"\r\n").getBytes(StandardCharsets.UTF_8));
        String filename=photo.optString("filename","photo.jpg").replaceAll("[^a-zA-Z0-9._-]","_");
        buffer.write(("--"+boundary+"\r\nContent-Disposition: form-data; name=\"file\"; filename=\""+filename+"\"\r\nContent-Type: application/octet-stream\r\n\r\n").getBytes(StandardCharsets.UTF_8));buffer.write(bytes);buffer.write(("\r\n--"+boundary+"--\r\n").getBytes(StandardCharsets.UTF_8));
        HttpURLConnection c=open("/tasks/"+task+"/attachments","POST",photo.getString("key"));c.setDoOutput(true);c.setRequestProperty("Content-Type","multipart/form-data; boundary="+boundary);c.setFixedLengthStreamingMode(buffer.size());try(OutputStream out=c.getOutputStream()){buffer.writeTo(out);}return new JSONObject(response(c));
    }
    public static byte[] readAll(InputStream stream,int max)throws IOException{
        try(InputStream in=stream;ByteArrayOutputStream out=new ByteArrayOutputStream()){byte[] block=new byte[8192];int n;while((n=in.read(block))!=-1){if(out.size()+n>max)throw new IOException("File exceeds local limit");out.write(block,0,n);}return out.toByteArray();}
    }
}
