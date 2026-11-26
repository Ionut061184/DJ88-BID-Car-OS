package ro.dj88bid.car;

import java.util.Arrays;

/** Synthetic fixtures exercise decoding only. No vehicle compatibility claim. */
public final class QfVehiclePacketTest {
    private static void check(boolean ok,String label){if(!ok)throw new AssertionError(label);}
    private static void word(byte[] b,int index,int value){b[index]=(byte)(value>>>8);b[index+1]=(byte)value;}
    public static void main(String[] args){
        byte[] p=new byte[79];p[0]=0x2e;p[1]=2;
        check(QfVehiclePacket.decode(p)==null,"zero placeholder");
        Arrays.fill(p,2,p.length,(byte)255);
        check(QfVehiclePacket.decode(p)==null,"all unavailable");
        Arrays.fill(p,2,p.length,(byte)0);
        word(p,9,830);word(p,11,170);
        int odo=3786830;p[15]=(byte)(odo>>>16);word(p,16,odo);
        p[6]=0x18;
        QfVehiclePacket d=QfVehiclePacket.decode(p);
        check(d!=null && d.speed==0 && d.rpm==830,"zero speed and rpm");
        check(d.fuel==17.0 && d.odometer==378683.0 && d.consumption==0.0,"scaling");
        check(Boolean.TRUE.equals(d.parkingBrake) && Boolean.FALSE.equals(d.driverBeltUnfastened) && Boolean.TRUE.equals(d.washerFlag),"status candidates");
        p[5]=(byte)255;p[6]=(byte)255;word(p,11,65535);
        d=QfVehiclePacket.decode(p);
        check(d.driverBeltUnfastened==null && d.parkingBrake==null && d.washerFlag==null && d.fuel==null,"unavailable values");
        p[50]=(byte)0xf0;d=QfVehiclePacket.decode(p);
        check(d.speed==null && d.odometer==null && d.consumption==null,"incompatible units");
        check(QfVehiclePacket.decode(Arrays.copyOf(p,78))==null,"wrong length");
        p[1]=1;check(QfVehiclePacket.decode(p)==null,"wrong type");
        System.out.println("PASS synthetic QF body decoder");
    }
}
