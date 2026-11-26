package ro.dj88bid.car;

/** Read-only interpretation of OEM 55446 DATA_SHARE types 1 and 3. */
public final class QfCabinPacket {
    public static boolean matches(byte[] p,int type,int length){
        return p!=null&&p.length==length&&(p[0]&255)==46&&(p[1]&255)==type;
    }
    public static Integer doors(byte[] p){
        if(!matches(p,3,3)||(p[2]&3)!=0)return null;
        return p[2]&255;
    }
    public static Climate climate(byte[] p){
        if(!matches(p,1,21))return null;
        return new Climate(p);
    }
    public static String temperature(int raw){
        if(raw==0)return "LO";
        if(raw==255)return "HI";
        if(raw==254)return null;
        // OEM encodes numeric Celsius or Fahrenheit times 2 without a unit in this field.
        return (raw/2)+"."+((raw&1)==0?"0":"5");
    }
    public static final class Climate {
        public final String left,right;
        public final boolean power,ac,auto,recirculation,dual;
        Climate(byte[] p){
            int a=p[2]&255;
            power=(a&128)!=0;ac=(a&64)!=0;auto=(a&32)!=0||(a&4)!=0;
            recirculation=(a&16)!=0;dual=(a&1)!=0;
            left=temperature(p[7]&255);right=temperature(p[8]&255);
        }
    }
}
