from pathlib import Path
import sys
root=Path(sys.argv[1])
p=root/"app/src/main/java/ro/dj88bid/car/MainActivity.kt"
s=p.read_text()
anchor="    inner class Bridge {"
assert s.count(anchor)==1
s=s.replace(anchor,'''    inner class Bridge {
        @JavascriptInterface
        fun launchFreeformMap(provider: String, x: Int, y: Int, w: Int, h: Int) = runOnUiThread {
            if (webView.url != "file:///android_asset/index.html" || !hasWindowFocus() || isFinishing) return@runOnUiThread
            val pkg = when(provider) {
                "maps" -> "com.google.android.apps.maps"
                "waze" -> "com.waze"
                "yandex" -> "ru.yandex.yandexmaps"
                "baidu" -> "com.baidu.BaiduMap"
                else -> return@runOnUiThread
            }
            if (x !in 0..100 || y !in 0..100 || w !in 20..100 || h !in 20..100 || x+w>100 || y+h>100) return@runOnUiThread
            android.app.AlertDialog.Builder(this@MainActivity)
                .setTitle("Test Freeform")
                .setMessage("Confirmați că mașina este staționată. Firmware-ul poate ignora dimensiunile și deschide harta pe tot ecranul.")
                .setNegativeButton("Anulează",null)
                .setPositiveButton("Testează") { _,_ ->
                    try {
                        val intent = packageManager.getLaunchIntentForPackage(pkg)
                            ?: throw android.content.ActivityNotFoundException()
                        val metrics = android.util.DisplayMetrics()
                        windowManager.defaultDisplay.getRealMetrics(metrics)
                        val bounds = android.graphics.Rect(metrics.widthPixels*x/100,metrics.heightPixels*y/100,metrics.widthPixels*(x+w)/100,metrics.heightPixels*(y+h)/100)
                        val options = android.app.ActivityOptions.makeBasic().setLaunchBounds(bounds)
                        intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
                        startActivity(intent,options.toBundle())
                        android.widget.Toast.makeText(this@MainActivity,"Cerere transmisă; verificați fereastra vizual",android.widget.Toast.LENGTH_LONG).show()
                    } catch (_: Exception) {
                        android.widget.Toast.makeText(this@MainActivity,"Hartă sau mod fereastră indisponibil",android.widget.Toast.LENGTH_SHORT).show()
                    }
                }.show()
        }
''',1)
p.write_text(s)
p=root/"app/src/main/assets/bid_general.js"
s=p.read_text()
anchor="button('Închide',"
assert s.count(anchor)==1
s=s.replace(anchor,"""const freeform=document.createElement('fieldset');
const legend=document.createElement('legend');legend.textContent='Ferestre hărți — test QF001';freeform.append(legend);
const fields=[['X',55],['Y',15],['Lățime',40],['Înălțime',70]].map(([label,value])=>{const row=document.createElement('label');row.textContent=label+' (%) ';const input=document.createElement('input');input.type='number';input.min='0';input.max='100';input.value=String(value);input.style.width='65px';row.append(input);freeform.append(row);return input;});
for(const [id,label] of [['maps','Google Maps'],['waze','Waze'],['yandex','Yandex Maps'],['baidu','Baidu Maps']]){const b=document.createElement('button');b.textContent=label+' Freeform';b.onclick=()=>{const v=fields.map(f=>Number(f.value));if(v.some(n=>!Number.isInteger(n)||n<0||n>100)||v[2]<20||v[3]<20||v[0]+v[2]>100||v[1]+v[3]>100){alert('Coordonate invalide');return;}try{native().launchFreeformMap(id,...v);}catch(_){alert('Funcție indisponibilă');}};freeform.append(b);}
modal.append(freeform);
"""+anchor,1)
p.write_text(s)
