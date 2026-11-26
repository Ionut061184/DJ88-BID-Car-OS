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
import org.json.JSONArray;

/** Foreground-only listener. Does not request CAN frames, write settings or send commands. */
public final class QfVehicleProbe {
    private static final String ACTION="com.qf.vehicle.action.DATA_SHARE";
    private static final String TEMP_ACTION="com.qf.vehicle.action.TEMP_STRING";
    private static final String SWA_ACTION="com.qf.vehicle.action.swa";
    private static final String REVERSE_ON="com.qf.action.BACKCAR_START";
    private static final String REVERSE_OFF="com.qf.action.BACKCAR_STOP";
    private Integer[] radarLevels;
    private Integer steeringRaw;
    private Float steeringRate;
    private Boolean reverseEvent;
    private long radarAt,steeringAt,reverseAt;
    private int radarMessages,steeringMessages,reverseMessages;
    private Double outsideTemperature;
    private long outsideAt;
    private int temperatureMessages, climateMessages, doorMessages;
    private QfCabinPacket.Climate climate;
    private Integer doors;
    private long climateAt,doorsAt;
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
            String action=intent.getAction();
            if(SWA_ACTION.equals(action)||REVERSE_ON.equals(action)||REVERSE_OFF.equals(action)){
                synchronized(QfVehicleProbe.this){
                    if(!listening)return;
                    long now=SystemClock.elapsedRealtime();
                    if(SWA_ACTION.equals(action)){
                        steeringMessages++;
                        try {
                            steeringRaw=intent.hasExtra("extra_angle")?intent.getIntExtra("extra_angle",Integer.MIN_VALUE):null;
                            steeringRate=intent.hasExtra("extra_rate")?intent.getFloatExtra("extra_rate",Float.NaN):null;
                            if(steeringRaw!=null&&(steeringRaw==Integer.MIN_VALUE||Math.abs((long)steeringRaw)>1000000))steeringRaw=null;
                            if(steeringRate!=null&&!Float.isFinite(steeringRate))steeringRate=null;
                        }catch(RuntimeException e){steeringRaw=null;steeringRate=null;}
                        steeringAt=steeringRaw==null?0:now;
                    }else{
                        reverseMessages++;reverseEvent=REVERSE_ON.equals(action);reverseAt=now;
                    }
                }
                return;
            }
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
                // Route different OEM message types independently; do not contaminate body counters.
                if(p.length>=2&&(p[0]&255)==46){
                    int type=p[1]&255;
                    if(type==1){
                        climateMessages++;
                        climate=QfCabinPacket.climate(p);
                        climateAt=climate==null?0:SystemClock.elapsedRealtime();
                        return;
                    }
                    if(type==4){
                        radarMessages++;
                        radarLevels=QfRadarPacket.levels(p);
                        radarAt=radarLevels==null?0:SystemClock.elapsedRealtime();
                        return;
                    }
                    if(type==3){
                        doorMessages++;
                        doors=QfCabinPacket.doors(p);
                        doorsAt=doors==null?0:SystemClock.elapsedRealtime();
                        return;
                    }
                }
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
            climate=null;doors=null;climateAt=doorsAt=0;climateMessages=doorMessages=0;
            IntentFilter filter=new IntentFilter(ACTION);
            radarLevels=null;steeringRaw=null;steeringRate=null;reverseEvent=null;
            radarAt=steeringAt=reverseAt=0;radarMessages=steeringMessages=reverseMessages=0;
            filter.addAction(TEMP_ACTION);
            filter.addAction(SWA_ACTION);
            filter.addAction(REVERSE_ON);
            filter.addAction(REVERSE_OFF);
            if(Build.VERSION.SDK_INT>=33)activity.registerReceiver(receiver,filter,Context.RECEIVER_EXPORTED);
            else activity.registerReceiver(receiver,filter);
            listening=true;
        }catch(RuntimeException e){listening=false;registrationError=e.getClass().getSimpleName();}
    }
    public synchronized void stop(){
        if(listening)try{activity.unregisterReceiver(receiver);}catch(RuntimeException ignored){}
        listening=false;frame=null;last=0;outsideTemperature=null;outsideAt=0;
        climate=null;doors=null;climateAt=doorsAt=0;
        radarLevels=null;steeringRaw=null;steeringRate=null;reverseEvent=null;
        radarAt=steeringAt=reverseAt=0;
    }
    // The OEM may require per-package opt-in before emitting body data.
    // Observe only: this is not proof of delivery and does not change system settings.
    private String readShareState(String suffix){
        try {
            String value=Settings.Global.getString(activity.getContentResolver(),
                activity.getPackageName()+suffix);
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
    // Read-only diagnosis of OEM registration; no writes to Settings.Global.
    private String oemCanbusVersion(){
        try {
            String version=activity.getPackageManager().getPackageInfo("com.qf.vehicle",0).versionName;
            return version==null?"unknown":version;
        }catch(Exception e){return "unavailable";}
    }
    private String bodyDeliveryState(String registry,String share){
        if(!listening)return "receiver_unavailable";
        if(valid>0)return "candidate_received";
        if(seen>0)return "frames_without_valid_body";
        if("unreadable".equals(registry)||"unreadable".equals(share))return "registration_unreadable";
        if("absent".equals(registry)||"not_listed".equals(registry))return "client_not_registered";
        if("absent".equals(share)||"disabled".equals(share))return "body_sharing_not_enabled";
        return "no_body_messages";
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
             .put("bodyShareState",readShareState("KeyShareCarbodyState"))
             .put("climateShareState",readShareState("KeyShareAcState"))
             .put("doorShareState",readShareState("KeyShareDoorWindow"))
             .put("radarShareState",readShareState("KeyShareRadarState"))
             .put("bodyRegistryState",readClientRegistryState())
             .put("bodySharePackage",activity.getPackageName());
            o.put("oemCanbusVersion",oemCanbusVersion())
             .put("bodyDeliveryState",bodyDeliveryState(o.optString("bodyRegistryState"),o.optString("bodyShareState")))
             .put("globalSettingsWriteGranted",activity.checkSelfPermission("android.permission.WRITE_SECURE_SETTINGS")==android.content.pm.PackageManager.PERMISSION_GRANTED);
            long tempAge=outsideAt==0?-1:SystemClock.elapsedRealtime()-outsideAt;
            boolean tempFresh=listening&&outsideTemperature!=null&&tempAge>=0&&tempAge<=120000;
            o.put("outsideTemperatureCandidate",tempFresh?outsideTemperature:JSONObject.NULL)
             .put("outsideTemperatureAgeMs",tempAge).put("outsideTemperatureFresh",tempFresh)
             .put("temperatureMessages",temperatureMessages);
            long now=SystemClock.elapsedRealtime();
            long ca=climateAt==0?-1:now-climateAt,da=doorsAt==0?-1:now-doorsAt;
            boolean cf=listening&&climate!=null&&ca>=0&&ca<=30000;
            boolean df=listening&&doors!=null&&da>=0&&da<=30000;
            o.put("climateFresh",cf).put("climateAgeMs",ca).put("climateMessages",climateMessages)
             .put("doorFresh",df).put("doorAgeMs",da).put("doorMessages",doorMessages);
            if(cf){
                o.put("climateLeft",climate.left==null?JSONObject.NULL:climate.left)
                 .put("climateRight",climate.right==null?JSONObject.NULL:climate.right)
                 .put("climatePower",climate.power).put("climateAc",climate.ac)
                 .put("climateAuto",climate.auto).put("climateDual",climate.dual);
            }
            if(df)o.put("doorMaskCandidate",doors);
            long ra=radarAt==0?-1:now-radarAt,sa=steeringAt==0?-1:now-steeringAt,rev=reverseAt==0?-1:now-reverseAt;
            boolean rf=listening&&radarLevels!=null&&ra>=0&&ra<=5000;
            boolean sf=listening&&steeringRaw!=null&&sa>=0&&sa<=5000;
            boolean vf=listening&&reverseEvent!=null&&rev>=0&&rev<=5000;
            o.put("radarAgeMs",ra).put("radarFresh",rf).put("radarMessages",radarMessages)
             .put("steeringAgeMs",sa).put("steeringFresh",sf).put("steeringMessages",steeringMessages)
             .put("reverseAgeMs",rev).put("reverseFresh",vf).put("reverseMessages",reverseMessages);
            if(rf){
                JSONArray levels=new JSONArray();
                for(Integer v:radarLevels)levels.put(v==null?JSONObject.NULL:v);
                o.put("radarLevelsCandidate",levels);
            }
            if(sf)o.put("steeringRawCandidate",steeringRaw).put("steeringRateCandidate",steeringRate==null?JSONObject.NULL:steeringRate);
            if(vf)o.put("reverseEventCandidate",reverseEvent);
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
