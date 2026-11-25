package ro.dj88bid.car;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.Intent;
import android.content.pm.ActivityInfo;
import android.content.pm.PackageManager;
import android.widget.Toast;

/** Exact OEM destinations from the K706 build 55446 manifest inventory.
 * Only explicit user taps launch exported, enabled activities. No service calls,
 * CAN writes, factory settings writes, or additional permissions. */
final class QfOemMenu {
    private static final String SETTINGS="com.qf.carsettings";
    private static final String[][] ENTRIES={
        {"Cameră față","com.qf.backcar","com.qf.backcar.FrontVdoActivity","MAIN"},
        {"Cameră 360°","com.st.carkit360camera","com.st.carkit360camera.MainActivity","MAIN"},
        {"DVR","com.fvsm.camera","com.fvsm.camera.view.activity.GuideActivity","MAIN"},
        {"TPMS","com.syt.tmps","com.tpms.view.TpmsMainActivity","MAIN"},
        {"Torque / OBD2","org.prowl.torque","","MAIN"},
        {"Ventilator navigație","com.qf.fancontrol","com.qf.fancontrol.FanControlActivity","MAIN"},
        {"Microfon",SETTINGS,SETTINGS+".activity.MicSetActivity","VIEW"},
        {"Pornire navigație",SETTINGS,SETTINGS+".activity.NavigationStartupActivity","VIEW"},
        {"Pornire DVR",SETTINGS,SETTINGS+".activity.DvrStartupActivity","VIEW"},
        {"Pornire OBD",SETTINGS,SETTINGS+".activity.ObdStartupActivity","VIEW"},
        {"Pornire TPMS",SETTINGS,SETTINGS+".activity.TpmsStartupActivity","VIEW"},
        {"Pornire aplicație",SETTINGS,SETTINGS+".activity.CustomAppStartupActivity","VIEW"},
        {"Comenzi volan","com.qf.keystudy","com.qf.keystudy.ui.KeyStudyActivity","MAIN"},
        {"Butoane panou","com.qf.panelkeystudy","com.qf.panelkeystudy.ui.PanelKeyStudyActivity","VIEW"},
        {"GPS / Sateliți","com.qf.beidougps","com.qf.beidougps.BeidouGpsActivity","VIEW"},
        {"Muzică Bluetooth","com.qf.bluetooth","com.qf.bluetooth.MusicActivity","MAIN"},
        {"Vreme originală","com.qf.weather2","com.qf.weather.MainActivityV2","MAIN"},
        {"CarPlay","com.zjinnova.zlink","com.zjinnova.android.zlink.features.launcher.CarPlayActivity","MAIN"},
        {"Android Auto","com.zjinnova.zlink","com.zjinnova.android.zlink.features.launcher.AutoActivity","MAIN"},
        {"Setări auto originale",SETTINGS,SETTINGS+".activity.CommonSettingsActivity","MAIN"}
    };
    private static Intent resolve(Activity a,String[] row){
        try {
            PackageManager pm=a.getPackageManager();
            Intent i=row[2].isEmpty()?pm.getLaunchIntentForPackage(row[1]):
                new Intent("VIEW".equals(row[3])?Intent.ACTION_VIEW:Intent.ACTION_MAIN).setClassName(row[1],row[2]);
            if(i==null || i.getComponent()==null || !row[1].equals(i.getComponent().getPackageName()))return null;
            ActivityInfo info=pm.getActivityInfo(i.getComponent(),0);
            if(!info.enabled || !info.exported || !info.applicationInfo.enabled)return null;
            if(info.permission!=null && a.checkSelfPermission(info.permission)!=PackageManager.PERMISSION_GRANTED)return null;
            return i;
        } catch(Exception e){return null;}
    }
    static void show(Activity a){
        String[] rows=new String[ENTRIES.length];
        for(int j=0;j<rows.length;j++)rows[j]=ENTRIES[j][0]+(resolve(a,ENTRIES[j])!=null?" · acces detectat":" · indisponibil");
        new AlertDialog.Builder(a).setTitle("BID · Funcții OEM extinse (staționar)")
          .setItems(rows,(dialog,index)->{
              Intent i=resolve(a,ENTRIES[index]);
              if(i==null){Toast.makeText(a,"Funcția nu este accesibilă pe acest dispozitiv.",Toast.LENGTH_LONG).show();return;}
              new AlertDialog.Builder(a).setTitle(ENTRIES[index][0])
                .setMessage("Se deschide aplicația originală. Folosiți numai cu mașina staționată. BID nu modifică setările automat.")
                .setPositiveButton("Deschide OEM",(d,w)->{
                    try{a.startActivity(i);}catch(RuntimeException e){Toast.makeText(a,"Aplicația OEM nu a putut fi deschisă.",Toast.LENGTH_LONG).show();}
                }).setNegativeButton("Renunță",null).show();
          }).setNegativeButton("Închide",null).show();
    }
}
