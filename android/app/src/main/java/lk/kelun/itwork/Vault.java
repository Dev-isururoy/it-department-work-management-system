package lk.kelun.itwork;

import android.content.Context;
import android.security.keystore.KeyGenParameterSpec;
import android.security.keystore.KeyProperties;
import android.util.AtomicFile;
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.security.KeyStore;
import javax.crypto.*;
import javax.crypto.spec.GCMParameterSpec;
import org.json.*;

/** Private storage encrypted with an Android Keystore AES-GCM key. */
public final class Vault {
    private final Context context;
    public Vault(Context c) { context=c.getApplicationContext(); }
    private SecretKey key() throws Exception {
        KeyStore store=KeyStore.getInstance("AndroidKeyStore"); store.load(null);
        if (!store.containsAlias("kelun-local")) {
            KeyGenerator generator=KeyGenerator.getInstance(KeyProperties.KEY_ALGORITHM_AES,"AndroidKeyStore");
            generator.init(new KeyGenParameterSpec.Builder("kelun-local",KeyProperties.PURPOSE_ENCRYPT|KeyProperties.PURPOSE_DECRYPT).setBlockModes(KeyProperties.BLOCK_MODE_GCM).setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE).build());
            generator.generateKey();
        }
        return (SecretKey)store.getKey("kelun-local",null);
    }
    private File path(String name) { if(!name.matches("[a-zA-Z0-9._-]+"))throw new IllegalArgumentException("Invalid local name");return new File(context.getFilesDir(),name); }
    public synchronized void write(String name,byte[] plain) throws Exception {
        Cipher cipher=Cipher.getInstance("AES/GCM/NoPadding");cipher.init(Cipher.ENCRYPT_MODE,key());
        ByteArrayOutputStream bytes=new ByteArrayOutputStream();bytes.write(cipher.getIV().length);bytes.write(cipher.getIV());bytes.write(cipher.doFinal(plain));
        AtomicFile file=new AtomicFile(path(name));FileOutputStream out=null;
        try{out=file.startWrite();out.write(bytes.toByteArray());file.finishWrite(out);}catch(Exception e){if(out!=null)file.failWrite(out);throw e;}
    }
    public synchronized byte[] read(String name) throws Exception {
        byte[] raw=new AtomicFile(path(name)).readFully();int length=raw[0]&255;
        Cipher cipher=Cipher.getInstance("AES/GCM/NoPadding");cipher.init(Cipher.DECRYPT_MODE,key(),new GCMParameterSpec(128,raw,1,length));
        return cipher.doFinal(raw,1+length,raw.length-1-length);
    }
    public JSONObject object(String name) throws Exception {if(!path(name).exists())return new JSONObject();return new JSONObject(new String(read(name),StandardCharsets.UTF_8));}
    public void object(String name,JSONObject value) throws Exception {write(name,value.toString().getBytes(StandardCharsets.UTF_8));}
    public void delete(String name){new AtomicFile(path(name)).delete();}
    public void clear(){for(File f:context.getFilesDir().listFiles())if(f.isFile())new AtomicFile(f).delete();}
}
