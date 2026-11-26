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
    private int seen, valid, lastSize, wrongExtra, wrongHeader, wrongLength;
    private int totalSeen, totalValid;
    private String registrationError = "";
    private String lastPacketState = "none";
    private QfVehiclePacket frame;
    private final BroadcastReceiver receiver=new BroadcastReceiver(){
        @Override public void onReceive(Context c,Intent intent){
            if(!ACTION.equals(intent.getAction()))return;
            synchronized(QfVehicleProbe.this){
                if(!listening)return;
                seen++;totalSeen++;
                byte[] p;
                try {p=intent.getByteArrayExtra("extra_DATA_SHARE");}
                catch(RuntimeException e){p=null;}
                lastSize=p==null?0:p.length;
                if(p==null){wrongExtra++;lastPacketState="missing_or_wrong_extra";return;}
                if(p.length!=79){wrongLength++;lastPacketState="wrong_length";return;}
                if((p[0]&255)!=0x2e || (p[1]&255)!=2){wrongHeader++;lastPacketState="wrong_header";return;}
                QfVehiclePacket decoded=QfVehiclePacket.decode(p);
                if(decoded!=null){valid++;totalValid++;lastPacketState="candidate";frame=decoded;last=SystemClock.elapsedRealtime();}
            }
        }
    };
    public QfVehicleProbe(Activity a){activity=a;}
    public synchronized void start(){
        if(listening)return;
        seen=0;valid=0;wrongExtra=0;wrongHeader=0;wrongLength=0;frame=null;last=0;registrationError="";lastPacketState="none";lastSize=0;
        try{
            IntentFilter filter=new IntentFilter(ACTION);
            if(Build.VERSION.SDK_INT>=33)activity.registerReceiver(receiver,filter,Context.RECEIVER_EXPORTED);
            else activity.registerReceiver(receiver,filter);
            listening=true;
        }catch(RuntimeException e){listening=false;registrationError=e.getClass().getSimpleName();}
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
             .put("wrongExtra",wrongExtra).put("wrongLength",wrongLength).put("wrongHeader",wrongHeader)
             .put("registrationError",registrationError).put("lastPacketState",lastPacketState)
             .put("totalMessages",totalSeen).put("totalCandidates",totalValid)
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
