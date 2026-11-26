package ro.dj88bid.car;

/** Experimental decoder: exact 79-byte OEM getCarInfoByte output (K706 build 55446). */
public final class QfVehiclePacket {
    public final Integer speed, rpm;
    public final Double fuel, odometer, consumption;
    public final int unitFlags;
    // Experimental OEM status flags; polarity must be confirmed on the actual Škoda.
    public final Boolean parkingBrake, driverBeltUnfastened, washerFlag;
    private QfVehiclePacket(byte[] p) {
        unitFlags = p[50] & 255;
        parkingBrake = status(p[6], 0x10);
        driverBeltUnfastened = status(p[5], 0x08);
        washerFlag = status(p[6], 0x08);
        speed = (unitFlags & 0x40) == 0 ? bounded(u16(p,7),0,300) : null;
        rpm = bounded(u16(p,9),0,8500);
        fuel = scaled(u16(p,11),0,1000);
        odometer = (unitFlags & 0x80) == 0 ? scaled(u24(p,15),0,15000000) : null;
        consumption = (unitFlags & 0x30) == 0 ? scaled(u16(p,51),0,1000) : null;
    }
    public static QfVehiclePacket decode(byte[] p) {
        if(p==null || p.length!=79 || (p[0]&255)!=0x2e || (p[1]&255)!=2) return null;
        // A placeholder frame consisting only of zero and unavailable bytes has no evidence.
        boolean informative = false;
        for (int i=2; i<p.length; i++) {
            int value=p[i]&255;
            if(value!=0 && value!=255){informative=true;break;}
        }
        if(!informative)return null;
        return new QfVehiclePacket(p);
    }
    private static Boolean status(byte raw,int mask){
        int v=raw&255;
        return v==255?null:(v&mask)!=0;
    }
    private static int u16(byte[] p,int i){return ((p[i]&255)<<8)|(p[i+1]&255);}
    private static int u24(byte[] p,int i){return ((p[i]&255)<<16)|((p[i+1]&255)<<8)|(p[i+2]&255);}
    private static Integer bounded(int n,int min,int max){return n>=min&&n<=max?n:null;}
    private static Double scaled(int n,int min,int max){return n>=min&&n<=max?n/10.0:null;}
}
