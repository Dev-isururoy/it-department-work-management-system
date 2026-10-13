package lk.kelun.itwork;
import android.content.*;
import android.database.Cursor;
import android.net.Uri;
import android.os.ParcelFileDescriptor;
import java.io.*;
public final class CameraProvider extends ContentProvider {
    public boolean onCreate(){return true;}
    public ParcelFileDescriptor openFile(Uri uri,String mode)throws FileNotFoundException{
        if(!"/capture.jpg".equals(uri.getPath()))throw new FileNotFoundException();
        int flags=mode.contains("w")?ParcelFileDescriptor.MODE_CREATE|ParcelFileDescriptor.MODE_READ_WRITE|ParcelFileDescriptor.MODE_TRUNCATE:ParcelFileDescriptor.MODE_READ_ONLY;
        return ParcelFileDescriptor.open(new File(getContext().getCacheDir(),"capture.jpg"),flags);
    }
    public String getType(Uri uri){return "image/jpeg";}
    public Cursor query(Uri u,String[] p,String s,String[] a,String o){return null;}
    public Uri insert(Uri u,ContentValues v){throw new UnsupportedOperationException();}
    public int update(Uri u,ContentValues v,String s,String[] a){throw new UnsupportedOperationException();}
    public int delete(Uri u,String s,String[] a){throw new UnsupportedOperationException();}
}
