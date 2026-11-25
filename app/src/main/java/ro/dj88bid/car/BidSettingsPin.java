package ro.dj88bid.car;

import android.content.Context;
import android.content.SharedPreferences;
import android.os.SystemClock;
import android.util.Base64;
import java.security.MessageDigest;
import java.security.SecureRandom;
import javax.crypto.SecretKeyFactory;
import javax.crypto.spec.PBEKeySpec;

/** Optional local settings lock, not a device lock. No PIN stored in WebView. */
final class BidSettingsPin {
    private final SharedPreferences prefs;
    private int failures=0;
    private long blockedUntil=0;
    BidSettingsPin(Context c){prefs=c.getSharedPreferences("bid_settings_pin",Context.MODE_PRIVATE);}
    synchronized boolean enabled(){return prefs.contains("verifier");}
    private boolean valid(String p){return p!=null&&p.matches("[0-9]{6,12}");}
    private byte[] derive(String p,byte[] salt)throws Exception{
        PBEKeySpec spec=new PBEKeySpec(p.toCharArray(),salt,120000,256);
        try{return SecretKeyFactory.getInstance("PBKDF2WithHmacSHA256").generateSecret(spec).getEncoded();}
        finally{spec.clearPassword();}
    }
    synchronized String verify(String pin){
        if(!enabled())return "ok";
        if(SystemClock.elapsedRealtime()<blockedUntil)return "wait";
        try{
            if(valid(pin)&&MessageDigest.isEqual(derive(pin,Base64.decode(prefs.getString("salt",""),Base64.NO_WRAP)),Base64.decode(prefs.getString("verifier",""),Base64.NO_WRAP))){
                failures=0;blockedUntil=0;return "ok";
            }
        }catch(Exception e){return "error";}
        if(++failures>=5){failures=0;blockedUntil=SystemClock.elapsedRealtime()+30000;return "wait";}
        return "wrong";
    }
    synchronized String change(String oldPin,String newPin){
        if(enabled()){String r=verify(oldPin);if(!"ok".equals(r))return r;}
        if(newPin==null)return "invalid";
        if(newPin.isEmpty())return prefs.edit().remove("salt").remove("verifier").commit()?"ok":"error";
        if(!valid(newPin))return "invalid";
        try{
            byte[] salt=new byte[24];new SecureRandom().nextBytes(salt);
            return prefs.edit().putString("salt",Base64.encodeToString(salt,Base64.NO_WRAP))
                .putString("verifier",Base64.encodeToString(derive(newPin,salt),Base64.NO_WRAP)).commit()?"ok":"error";
        }catch(Exception e){return "error";}
    }
}
