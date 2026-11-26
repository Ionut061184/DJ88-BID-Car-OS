package ro.dj88bid.car;

import android.content.ComponentName;
import android.content.Context;
import android.content.Intent;
import android.content.ServiceConnection;
import android.os.Binder;
import android.os.IBinder;
import android.os.Parcel;
import android.os.RemoteException;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.atomic.AtomicInteger;
import org.json.JSONObject;

/** Explicit 120-second audit only. No SDK credentials, initialization, CAN commands,
 * global settings writes, or decoding of unverified SDK packet layouts.
 * ABI inspected in OEM V1.11-260615.1900 (add=11, remove=12, packed callback=2). */
final class QfSdkBodyAudit {
    private static final String OEM="com.qf.vehicle";
    private static final String SERVICE="com.qf.vehicle.service.VehicleService";
    private static final String FEATURE="com.qf.vehicle.service.ICanBusServiceFeature";
    private static final String CALLBACK="com.qf.vehicle.service.ICanBusServiceCallback";
    private final Context context;
    private volatile Session session;
    private volatile String state="not_started";
    QfSdkBodyAudit(Context c){context=c.getApplicationContext();}
    // Main thread only. Bind to an already running service; do not start OEM components.
    void start(String version){
        stop();
        session=null;
        if(!"V1.11-260615.1900".equals(version)){state="unsupported_version";return;}
        try{
            int uid=context.getPackageManager().getApplicationInfo(OEM,0).uid;
            Session s=new Session(uid);
            session=s;state="binding";
            Intent intent=new Intent("com.qf.vehicle.service.ACTION_CAN_SERVICE");
            intent.setComponent(new ComponentName(OEM,SERVICE));
            s.bound=context.bindService(intent,s,0);
            if(!s.bound){state="bind_rejected";s.active=false;s.worker.shutdown();}
        }catch(Exception e){state="bind_error_"+e.getClass().getSimpleName();stop();}
    }
    void stop(){
        Session s=session;
        if(s==null||!s.active)return;
        s.active=false;
        state="audit_ended_"+state;
        // Queue removal behind any in-flight registration. No IPC on UI thread.
        s.worker.execute(()->{
            IBinder b=s.remote;
            if(s.registerAttempted&&b!=null){
                try{call(b,12,s.callback);}catch(Exception ignored){}
            }
        });
        s.worker.shutdown();
        if(s.bound){s.bound=false;try{context.unbindService(s);}catch(RuntimeException ignored){}}
    }
    void snapshot(JSONObject o)throws org.json.JSONException{
        Session s=session;
        o.put("sdkBodyAuditState",state)
         .put("sdkBodyPackedCount",s==null?0:s.packed.get())
         .put("sdkBodyRawCount",s==null?0:s.raw.get())
         .put("sdkBodyLastBytes",s==null?0:s.lastBytes.get());
    }
    private static boolean call(IBinder b,int operation,IBinder callback)throws RemoteException{
        if(operation!=11&&operation!=12)throw new IllegalArgumentException("read-only subscription only");
        Parcel data=Parcel.obtain(),reply=Parcel.obtain();
        try{
            data.writeInterfaceToken(FEATURE);data.writeStrongBinder(callback);
            if(!b.transact(operation,data,reply,0))return false;
            reply.readException();return true;
        }finally{reply.recycle();data.recycle();}
    }
    private final class Session implements ServiceConnection{
        final int uid;
        final ExecutorService worker=Executors.newSingleThreadExecutor();
        final AtomicInteger packed=new AtomicInteger(),raw=new AtomicInteger(),lastBytes=new AtomicInteger();
        volatile boolean active=true,registerAttempted;
        boolean bound;
        volatile IBinder remote;
        Session(int uid){this.uid=uid;}
        final Binder callback=new Binder(){
            @Override protected boolean onTransact(int code,Parcel data,Parcel reply,int flags)throws RemoteException{
                if(code==INTERFACE_TRANSACTION){if(reply!=null)reply.writeString(CALLBACK);return true;}
                if(code!=1&&code!=2)return super.onTransact(code,data,reply,flags);
                data.enforceInterface(CALLBACK);
                if(Binder.getCallingUid()!=uid)throw new SecurityException("Unexpected callback UID");
                byte[] payload=data.createByteArray();
                if(active&&payload!=null&&payload.length>0&&payload.length<=65536){
                    if(code==2){packed.incrementAndGet();lastBytes.set(payload.length);}
                    else raw.incrementAndGet();
                }
                if(reply!=null)reply.writeNoException();
                return true;
            }
        };
        @Override public void onServiceConnected(ComponentName name,IBinder b){
            if(!active||session!=this)return;
            remote=b;
            worker.execute(()->{
                if(!active)return;
                try{
                    if(!FEATURE.equals(b.getInterfaceDescriptor())){report("descriptor_mismatch");return;}
                    registerAttempted=true;
                    report(call(b,11,callback)?"subscribed_unverified":"subscription_rejected");
                }catch(Exception e){report("subscription_error_"+e.getClass().getSimpleName());}
            });
        }
        void report(String value){if(active&&session==this)state=value;}
        @Override public void onServiceDisconnected(ComponentName name){report("disconnected");}
        @Override public void onNullBinding(ComponentName name){report("null_binding");}
        @Override public void onBindingDied(ComponentName name){report("binding_died");}
    }
}
