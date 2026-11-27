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
 private TextView log; private final EditText[] fields=new EditText[4];
 private void append(String s){log.append("\n"+s);}
 @Override public void onCreate(Bundle b){super.onCreate(b);ScrollView scroll=new ScrollView(this);LinearLayout col=new LinearLayout(this);col.setOrientation(1);col.setPadding(18,18,18,18);scroll.addView(col);setContentView(scroll);
 TextView title=new TextView(this);title.setText("BID QF001 • Freeform diagnostic\nTestați exclusiv cu mașina staționată. Nicio setare de sistem nu este modificată.");title.setTextSize(20);col.addView(title);
 String[] labels={"X (%)","Y (%)","Lățime (%)","Înălțime (%)"};String[] values={"55","15","40","70"};LinearLayout row=new LinearLayout(this);col.addView(row);
 for(int i=0;i<4;i++){LinearLayout cell=new LinearLayout(this);cell.setOrientation(1);TextView t=new TextView(this);t.setText(labels[i]);cell.addView(t);fields[i]=new EditText(this);fields[i].setSingleLine(true);fields[i].setInputType(2);fields[i].setText(values[i]);cell.addView(fields[i]);row.addView(cell,new LinearLayout.LayoutParams(0,-2,1));}
 add(col,"Google Maps – cerere fereastră",()->confirmLaunch("com.google.android.apps.maps"));add(col,"Waze – cerere fereastră",()->confirmLaunch("com.waze"));add(col,"Copiază jurnalul",()->{ClipboardManager c=(ClipboardManager)getSystemService(CLIPBOARD_SERVICE);c.setPrimaryClip(ClipData.newPlainText("BID diagnostic",log.getText()));});
 log=new TextView(this);log.setTextIsSelectable(true);col.addView(log);append("Android SDK: "+Build.VERSION.SDK_INT+" / "+Build.DISPLAY);append("Freeform declarat: "+getPackageManager().hasSystemFeature("android.software.freeform_window_management"));append("Maps detectat: "+(getPackageManager().getLaunchIntentForPackage("com.google.android.apps.maps")!=null));append("Waze detectat: "+(getPackageManager().getLaunchIntentForPackage("com.waze")!=null));append("Android poate ignora coordonatele. Confirmarea este exclusiv vizuală."); }
 private void add(LinearLayout col,String text,Runnable r){Button b=new Button(this);b.setText(text);b.setOnClickListener(v->r.run());col.addView(b);}
 private void confirmLaunch(String pkg){new AlertDialog.Builder(this).setTitle("Test la staționare").setMessage("Confirmați că mașina este staționată. Aplicația poate porni pe tot ecranul.").setNegativeButton("Anulează",null).setPositiveButton("Testează",(d,w)->launch(pkg)).show();}
 private void launch(String pkg){try{Intent i=getPackageManager().getLaunchIntentForPackage(pkg);if(i==null){append("Aplicație indisponibilă: "+pkg);return;}int[] v=new int[4];for(int k=0;k<4;k++)v[k]=Integer.parseInt(fields[k].getText().toString());Rect screen;if(Build.VERSION.SDK_INT>=30){screen=getWindowManager().getMaximumWindowMetrics().getBounds();}else{android.util.DisplayMetrics m=new android.util.DisplayMetrics();getWindowManager().getDefaultDisplay().getRealMetrics(m);screen=new Rect(0,0,m.widthPixels,m.heightPixels);}int[] a=Bounds.of(screen.left,screen.top,screen.width(),screen.height(),v[0],v[1],v[2],v[3]);Rect r=new Rect(a[0],a[1],a[2],a[3]);ActivityOptions options=ActivityOptions.makeBasic();options.setLaunchBounds(r);i.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);append("Cerere "+pkg+" bounds="+r);startActivity(i,options.toBundle());append("Cerere transmisă; NU confirmă Freeform.");}catch(Exception e){append("Eroare: "+e.getClass().getSimpleName()+": "+e.getMessage());}}
 @Override protected void onResume(){super.onResume();if(log!=null)append("Diagnostic reluat; multi-window propriu="+isInMultiWindowMode());}
}