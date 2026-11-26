package ro.dj88bid.car;
public final class QfOutsideTemperatureTest {
    private static void eq(String text,double expected){
        Double v=QfOutsideTemperature.parse(text);
        if(v==null||Math.abs(v-expected)>0.00001)throw new AssertionError(text);
    }
    public static void main(String[] args){
        eq("2℃",2);eq("-7.5°C",-7.5);eq("35,6 ℉",2);eq("32 °F",0);eq("0℃",0);
        for(String bad:new String[]{null,"","--℃","NaN°C","2","999℃","14.2 V","2K","∞℃","2℃ text"})
            if(QfOutsideTemperature.parse(bad)!=null)throw new AssertionError(String.valueOf(bad));
        System.out.println("PASS OEM temperature parser");
    }
}
