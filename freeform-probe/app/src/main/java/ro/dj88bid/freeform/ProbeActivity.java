package ro.dj88bid.freeform;
import android.app.Activity;
import android.app.ActivityOptions;
import android.app.AlertDialog;
import android.content.ClipData;
import android.content.ClipboardManager;
import android.content.Intent;
import android.graphics.Rect;
import android.os.Build;
import android.os.Bundle;
import android.widget.*;
public class ProbeActivity extends Activity {
 private static final String[] EVENTS={
 "com.qf.action.ACC_ON","com.qf.action.ACC_OFF","com.qf.action.READY_GO_SLEEP",
 "com.unisound.intent.action.ACC_ON","com.unisound.intent.action.ACC_OFF",
 "com.acloud.intent.android.XY.ANDROID.CANBUSDISPINFO1","com.acloud.intent.android.XY.ANDROID.CANBUSDISPINFO3",
 Intent.ACTION_POWER_CONNECTED,Intent.ACTION_POWER_DISCONNECTED,Intent.ACTION_SCREEN_ON,Intent.ACTION_SCREEN_OFF,
 android.bluetooth.BluetoothDevice.ACTION_ACL_CONNECTED,android.bluetooth.BluetoothDevice.ACTION_ACL_DISCONNECTED};
 private static boolean listening=false;
 private static final android.content.BroadcastReceiver accReceiver=new android.content.BroadcastReceiver(){
  @Override public void onReceive(android.content.Context c,Intent i){
   persist(c,"Eveniment nevalidat: "+i.getAction());
  }
 };
 private static void persist(android.content.Context context,String event){
  String stamp=new java.text.SimpleDateFormat("yyyy-MM-dd HH:mm:ss.SSS",java.util.Locale.ROOT).format(new java.util.Date());
  android.content.SharedPreferences p=context.getSharedPreferences("acc_probe",MODE_PRIVATE);
  String previous=p.getString("journal","");
  String next=previous+stamp+" elapsed="+android.os.SystemClock.elapsedRealtime()+" "+event+"\n";
  if(next.length()>48000)next=next.substring(next.length()-48000);
  p.edit().putString("journal",next).commit();
  }
 private void record(String event){persist(this,event);if(log!=null)append(event);
 }
 private void listen(){
  if(listening)return;
  android.content.IntentFilter filter=new android.content.IntentFilter();
  for(String action:EVENTS)filter.addAction(action);
  try{
   if(Build.VERSION.SDK_INT>=33)getApplicationContext().registerReceiver(accReceiver,filter,android.content.Context.RECEIVER_EXPORTED);
   else getApplicationContext().registerReceiver(accReceiver,filter);
   listening=true;getSharedPreferences("acc_probe",MODE_PRIVATE).edit().putBoolean("enabled",true).commit();record("Receptor activ; semnalele OEM nu sunt autentificate.");
  }catch(Exception e){record("Înregistrare eșuată: "+e.getClass().getSimpleName());}
 }
 @Override protected void onPause(){record("Activity onPause (nu confirmă ACC)");super.onPause();}
 @Override protected void onStop(){record("Activity onStop (nu confirmă ACC)");super.onStop();}
 @Override protected void onDestroy(){record("Activity onDestroy");super.onDestroy();}
 private TextView log; private final EditText[] fields=new EditText[4];
 private void append(String s){log.append("\n"+s);}
 @Override public void onCreate(Bundle b){super.onCreate(b);ScrollView scroll=new ScrollView(this);LinearLayout col=new LinearLayout(this);col.setOrientation(1);col.setPadding(18,18,18,18);scroll.addView(col);setContentView(scroll);
 TextView title=new TextView(this);title.setText("BID QF001 • Freeform diagnostic\nTestați exclusiv cu mașina staționată. Nicio setare de sistem nu este modificată.");title.setTextSize(20);col.addView(title);
 String[] labels={"X (%)","Y (%)","Lățime (%)","Înălțime (%)"};String[] values={"55","15","40","70"};LinearLayout row=new LinearLayout(this);col.addView(row);
 for(int i=0;i<4;i++){LinearLayout cell=new LinearLayout(this);cell.setOrientation(1);TextView t=new TextView(this);t.setText(labels[i]);cell.addView(t);fields[i]=new EditText(this);fields[i].setSingleLine(true);fields[i].setInputType(2);fields[i].setText(values[i]);cell.addView(fields[i]);row.addView(cell,new LinearLayout.LayoutParams(0,-2,1));}
 add(col,"Google Maps – cerere fereastră",()->confirmLaunch("com.google.android.apps.maps"));add(col,"Waze – cerere fereastră",()->confirmLaunch("com.waze"));add(col,"Copiază jurnalul",()->{ClipboardManager c=(ClipboardManager)getSystemService(CLIPBOARD_SERVICE);c.setPrimaryClip(ClipData.newPlainText("BID diagnostic",log.getText()));});
 log=new TextView(this);log.setTextIsSelectable(true);col.addView(log);append("Android SDK: "+Build.VERSION.SDK_INT+" / "+Build.DISPLAY);append("Freeform declarat: "+getPackageManager().hasSystemFeature("android.software.freeform_window_management"));append("Maps detectat: "+(getPackageManager().getLaunchIntentForPackage("com.google.android.apps.maps")!=null));append("Waze detectat: "+(getPackageManager().getLaunchIntentForPackage("com.waze")!=null));append("Android poate ignora coordonatele. Confirmarea este exclusiv vizuală.");
 add(col,"Pornește diagnostic ACC",()->listen());
 add(col,"Marcaj manual: contact pus",()->record("UTILIZATOR: contact pus"));
 add(col,"Marcaj manual: contact scos",()->record("UTILIZATOR: contact scos"));
 add(col,"Copiază jurnal ACC persistent",()->{ClipboardManager c=(ClipboardManager)getSystemService(CLIPBOARD_SERVICE);c.setPrimaryClip(ClipData.newPlainText("ACC diagnostic",getSharedPreferences("acc_probe",MODE_PRIVATE).getString("journal","")));});
 add(col,"Șterge jurnal ACC",()->new AlertDialog.Builder(this).setMessage("Ștergi jurnalul local?").setNegativeButton("Nu",null).setPositiveButton("Da",(d,w)->{getSharedPreferences("acc_probe",MODE_PRIVATE).edit().remove("journal").commit();append("Jurnal șters");}).show());
 append("ACC V2: receptor în contextul aplicației, fără wake lock; procesul poate fi oprit de sistem.");
 if(getSharedPreferences("acc_probe",MODE_PRIVATE).getBoolean("enabled",false))listen();
 add(col,"Oprește diagnostic ACC",()->{if(listening){getApplicationContext().unregisterReceiver(accReceiver);listening=false;}getSharedPreferences("acc_probe",MODE_PRIVATE).edit().putBoolean("enabled",false).commit();record("Diagnostic oprit");});
 }
 private void add(LinearLayout col,String text,Runnable r){Button b=new Button(this);b.setText(text);b.setOnClickListener(v->r.run());col.addView(b);}
 private void confirmLaunch(String pkg){new AlertDialog.Builder(this).setTitle("Test la staționare").setMessage("Confirmați că mașina este staționată. Aplicația poate porni pe tot ecranul.").setNegativeButton("Anulează",null).setPositiveButton("Testează",(d,w)->launch(pkg)).show();}
 private void launch(String pkg){try{Intent i=getPackageManager().getLaunchIntentForPackage(pkg);if(i==null){append("Aplicație indisponibilă: "+pkg);return;}int[] v=new int[4];for(int k=0;k<4;k++)v[k]=Integer.parseInt(fields[k].getText().toString());Rect screen;if(Build.VERSION.SDK_INT>=30){screen=getWindowManager().getMaximumWindowMetrics().getBounds();}else{android.util.DisplayMetrics m=new android.util.DisplayMetrics();getWindowManager().getDefaultDisplay().getRealMetrics(m);screen=new Rect(0,0,m.widthPixels,m.heightPixels);}int[] a=Bounds.of(screen.left,screen.top,screen.width(),screen.height(),v[0],v[1],v[2],v[3]);Rect r=new Rect(a[0],a[1],a[2],a[3]);ActivityOptions options=ActivityOptions.makeBasic();options.setLaunchBounds(r);i.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);append("Cerere "+pkg+" bounds="+r);startActivity(i,options.toBundle());append("Cerere transmisă; NU confirmă Freeform.");}catch(Exception e){append("Eroare: "+e.getClass().getSimpleName()+": "+e.getMessage());}}
 @Override protected void onResume(){super.onResume();if(log!=null){append("Diagnostic reluat; multi-window propriu="+isInMultiWindowMode());record("Activity onResume (nu confirmă ACC)");append(getSharedPreferences("acc_probe",MODE_PRIVATE).getString("journal",""));}}
}