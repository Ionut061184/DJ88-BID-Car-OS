package ro.dj88bid.car;
public final class QfCabinPacketTest {
    static void check(boolean x){if(!x)throw new AssertionError();}
    public static void main(String[] args){
        byte[] d={46,3,(byte)132};
        check(QfCabinPacket.doors(d)==132);
        d[2]=0;check(QfCabinPacket.doors(d)==0);
        d[2]=1;check(QfCabinPacket.doors(d)==null);
        check(QfCabinPacket.doors(new byte[]{46,3})==null);
        byte[] c=new byte[21];c[0]=46;c[1]=1;c[2]=(byte)0xe1;c[7]=0;c[8]=43;
        QfCabinPacket.Climate x=QfCabinPacket.climate(c);
        check(x.power&&x.ac&&x.auto&&x.dual&&!x.recirculation);
        check("LO".equals(x.left)&&"21.5".equals(x.right));
        c[7]=(byte)255;c[8]=(byte)254;x=QfCabinPacket.climate(c);
        check("HI".equals(x.left)&&x.right==null);
        c[1]=2;check(QfCabinPacket.climate(c)==null);
        System.out.println("PASS synthetic OEM climate and door decoding");
    }
}
