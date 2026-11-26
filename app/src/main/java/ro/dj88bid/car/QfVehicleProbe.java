package ro.dj88bid.car;

import android.app.Activity;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.content.IntentFilter;
import android.os.Build;
import android.os.SystemClock;
import android.provider.Settings;
import org.json.JSONObject;

/** Foreground-only listener. Does not request CAN frames, write settings or send commands. */
public final class QfVehicleProbe {
    private static final String ACTION="com.qf.vehicle.action.DATA_SHARE";
    private static final String TEMP_ACTION="com.qf.vehicle.action.TEMP_STRING";
    private Double outsideTemperature;
    private long outsideAt;
    private int temperatureMessages;
    private final Activity activity;
    private boolean listening;
    private long last;
    private int seen, valid, lastSize, wrongExtra, wrongHeader, wrongLength, emptyBody;
    private int totalSeen, totalValid;
    private String registrationError = "";
    private String lastPacketState = "none";
    private QfVehiclePacket frame;
    private final BroadcastReceiver receiver=new BroadcastReceiver(){
        @Override public void onReceive(Context c,Intent intent){
            if(TEMP_ACTION.equals(intent.getAction())){
                synchronized(QfVehicleProbe.this){
                    if(!listening)return;
                    temperatureMessages++;
                    try {outsideTemperature=QfOutsideTemperature.parse(intent.getStringExtra("extra_string"));}
                    catch(RuntimeException e){outsideTemperature=null;}
                    outsideAt=outsideTemperature==null?0:SystemClock.elapsedRealtime();
                }
                return;
            }
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
                else {emptyBody++;lastPacketState="empty_body";frame=null;last=0;}
            }
        }
    };
    public QfVehicleProbe(Activity a){activity=a;}
    public synchronized void start(){
        if(listening)return;
        seen=0;valid=0;wrongExtra=0;wrongHeader=0;wrongLength=0;emptyBody=0;frame=null;last=0;registrationError="";lastPacketState="none";lastSize=0;
        try{
            outsideTemperature=null;outsideAt=0;temperatureMessages=0;
            IntentFilter filter=new IntentFilter(ACTION);
            filter.addAction(TEMP_ACTION);
            if(Build.VERSION.SDK_INT>=33)activity.registerReceiver(receiver,filter,Context.RECEIVER_EXPORTED);
            else activity.registerReceiver(receiver,filter);
            listening=true;
        }catch(RuntimeException e){listening=false;registrationError=e.getClass().getSimpleName();}
    }
    public synchronized void stop(){
        if(listening)try{activity.unregisterReceiver(receiver);}catch(RuntimeException ignored){}
        listening=false;frame=null;last=0;outsideTemperature=null;outsideAt=0;
    }
    // The OEM may require per-package opt-in before emitting body data.
    // Observe only: this is not proof of delivery and does not change system settings.
    private String readBodyShareState(){
        try {
            String value=Settings.Global.getString(activity.getContentResolver(),
                activity.getPackageName()+"KeyShareCarbodyState");
            if(value==null)return "absent";
            if("1".equals(value))return "enabled";
            if("0".equals(value))return "disabled";
            return "unknown";
        } catch(RuntimeException e){return "unreadable";}
    }
    private String readClientRegistryState(){
        try {
            String value=Settings.Global.getString(activity.getContentResolver(),"KeyAllPackages");
            if(value==null || value.isEmpty())return "absent";
            for(String client:value.split(",")){
                if(activity.getPackageName().equals(client))return "listed";
            }
            return "not_listed";
        } catch(RuntimeException e){return "unreadable";}
    }
    public synchronized String snapshot(){
        JSONObject o=new JSONObject();
        try{
            long age=last==0?-1:SystemClock.elapsedRealtime()-last;
            boolean fresh=listening&&frame!=null&&age>=0&&age<=5000;
            o.put("listening",listening).put("messages",seen).put("candidateFrames",valid)
             .put("lastSize",lastSize).put("ageMs",age).put("fresh",fresh)
             .put("wrongExtra",wrongExtra).put("wrongLength",wrongLength).put("wrongHeader",wrongHeader).put("emptyBody",emptyBody)
             .put("registrationError",registrationError).put("lastPacketState",lastPacketState)
             .put("totalMessages",totalSeen).put("totalCandidates",totalValid)
             .put("verified",false).put("source","OEM broadcast; sender not authenticated")
             .put("bodyShareState",readBodyShareState())
             .put("bodyRegistryState",readClientRegistryState())
             .put("bodySharePackage",activity.getPackageName());
            long tempAge=outsideAt==0?-1:SystemClock.elapsedRealtime()-outsideAt;
            boolean tempFresh=listening&&outsideTemperature!=null&&tempAge>=0&&tempAge<=120000;
            o.put("outsideTemperatureCandidate",tempFresh?outsideTemperature:JSONObject.NULL)
             .put("outsideTemperatureAgeMs",tempAge).put("outsideTemperatureFresh",tempFresh)
             .put("temperatureMessages",temperatureMessages);
            if(fresh){
                o.put("speedCandidate",frame.speed==null?JSONObject.NULL:frame.speed);
                o.put("rpmCandidate",frame.rpm==null?JSONObject.NULL:frame.rpm);
                o.put("fuelCandidate",frame.fuel==null?JSONObject.NULL:frame.fuel);
                o.put("odometerCandidate",frame.odometer==null?JSONObject.NULL:frame.odometer);
                o.put("consumptionCandidate",frame.consumption==null?JSONObject.NULL:frame.consumption);
                o.put("parkingBrakeCandidate",frame.parkingBrake==null?JSONObject.NULL:frame.parkingBrake);
                o.put("driverBeltUnfastenedCandidate",frame.driverBeltUnfastened==null?JSONObject.NULL:frame.driverBeltUnfastened);
                o.put("washerFlagCandidate",frame.washerFlag==null?JSONObject.NULL:frame.washerFlag);
            }
        }catch(Exception ignored){}
        return o.toString();
    }
}
