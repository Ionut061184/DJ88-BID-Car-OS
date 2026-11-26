package ro.dj88bid.car;

import java.util.regex.Matcher;
import java.util.regex.Pattern;

/** Strict interpretation of the OEM's unit-bearing TEMP_STRING, not weather data. */
public final class QfOutsideTemperature {
    private static final Pattern VALUE=Pattern.compile("^([+-]?\\d{1,3}(?:[.,]\\d{1,2})?)\\s*(℃|℉|°\\s*[CF])$");
    public static Double parse(String text){
        if(text==null || text.length()>32)return null;
        Matcher m=VALUE.matcher(text.trim());
        if(!m.matches())return null;
        try{
            double v=Double.parseDouble(m.group(1).replace(',','.'));
            String unit=m.group(2);
            if(unit.equals("℉")||unit.endsWith("F"))v=(v-32.0)*5.0/9.0;
            return Double.isFinite(v)&&v>=-60&&v<=85?v:null;
        }catch(NumberFormatException e){return null;}
    }
}
