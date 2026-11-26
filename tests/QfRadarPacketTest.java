package ro.dj88bid.car;
import java.util.Arrays;
public final class QfRadarPacketTest {
    public static void main(String[] args){
        byte[] p=new byte[42];Arrays.fill(p,(byte)255);p[0]=46;p[1]=4;
        p[3]=3;p[13]=0;p[26]=4;p[37]=8;p[14]=99;
        Integer[] v=QfRadarPacket.levels(p);
        if(v.length!=20||v[0]!=null||v[1]!=3||v[11]!=0||v[12]!=4||v[19]!=8)throw new AssertionError();
        if(QfRadarPacket.levels(Arrays.copyOf(p,41))!=null)throw new AssertionError();
        p[1]=3;if(QfRadarPacket.levels(p)!=null)throw new AssertionError();
        System.out.println("PASS synthetic radar mapping");
    }
}
