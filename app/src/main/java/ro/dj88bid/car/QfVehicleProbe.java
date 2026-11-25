package ro.dj88bid.car;

import android.app.Activity;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.content.IntentFilter;
import android.os.Build;
import android.os.SystemClock;
import org.json.JSONObject;

/** Foreground-only listener. Does not request CAN frames, write settings or send commands. */
public final class QfVehicleProbe {
    private static final String ACTION="com.qf.vehicle.action.DATA_SHARE";
    private final Activity activity;
    private boolean listening;
    private long last;
    private int seen, valid, lastSize;
    private QfVehiclePacket frame;
    private final BroadcastReceiver receiver=new BroadcastReceiver(){
        @Override public void onReceive(Context c,Intent intent){
            if(!ACTION.equals(intent.getAction()))return;
            byte[] p;
            try {p=intent.getByteArrayExtra("extra_DATA_SHARE");}catch(RuntimeException e){return;}
            synchronized(QfVehicleProbe.this){
                if(!listening)return;
                seen++;lastSize=p==null?0:p.length;
                QfVehiclePacket decoded=QfVehiclePacket.decode(p);
                if(decoded!=null){valid++;frame=decoded;last=SystemClock.elapsedRealtime();}
            }
        }
    };
    public QfVehicleProbe(Activity a){activity=a;}
    public synchronized void start(){
        if(listening)return;
        seen=0;valid=0;lastSize=0;frame=null;last=0;
        try{
            IntentFilter filter=new IntentFilter(ACTION);
            if(Build.VERSION.SDK_INT>=33)activity.registerReceiver(receiver,filter,Context.RECEIVER_EXPORTED);
            else activity.registerReceiver(receiver,filter);
            listening=true;
        }catch(RuntimeException e){listening=false;}
    }
    public synchronized void stop(){
        if(listening)try{activity.unregisterReceiver(receiver);}catch(RuntimeException ignored){}
        listening=false;frame=null;last=0;
    }
    public synchronized String snapshot(){
        JSONObject o=new JSONObject();
        try{
            long age=last==0?-1:SystemClock.elapsedRealtime()-last;
            boolean fresh=listening&&frame!=null&&age>=0&&age<=5000;
            o.put("listening",listening).put("messages",seen).put("candidateFrames",valid)
             .put("lastSize",lastSize).put("ageMs",age).put("fresh",fresh)
             .put("verified",false).put("source","OEM broadcast; sender not authenticated");
            if(fresh){
                o.put("speedCandidate",frame.speed==null?JSONObject.NULL:frame.speed);
                o.put("rpmCandidate",frame.rpm==null?JSONObject.NULL:frame.rpm);
                o.put("fuelCandidate",frame.fuel==null?JSONObject.NULL:frame.fuel);
                o.put("odometerCandidate",frame.odometer==null?JSONObject.NULL:frame.odometer);
                o.put("consumptionCandidate",frame.consumption==null?JSONObject.NULL:frame.consumption);
            }
        }catch(Exception ignored){}
        return o.toString();
    }
}
