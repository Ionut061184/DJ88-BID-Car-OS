package ro.dj88bid.car;
/** OEM build 55446 type 4. Raw level values only; distance scaling not assumed. */
public final class QfRadarPacket {
    public static Integer[] levels(byte[] p){
        if(p==null||p.length!=42||(p[0]&255)!=46||(p[1]&255)!=4)return null;
        Integer[] result=new Integer[20];
        int[] offsets={2,3,4,5,6,7,8,9,10,11,12,13,26,27,28,29,34,35,36,37};
        for(int i=0;i<offsets.length;i++){
            int v=p[offsets[i]]&255;
            result[i]=v==255?null:v;
        }
        return result;
    }
}
