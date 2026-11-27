from pathlib import Path
import sys
root=Path(sys.argv[1])
p=root/"app/src/main/AndroidManifest.xml"
s=p.read_text()
assert s.count("<application")==1
s=s.replace("<application",'<uses-permission android:name="net.dinglisch.android.tasker.PERMISSION_RUN_TASKS" />\n    <application',1)
p.write_text(s)
p=root/"app/src/main/java/ro/dj88bid/car/MainActivity.kt"
s=p.read_text()
anchor="    inner class Bridge {"
assert s.count(anchor)==1
s=s.replace(anchor,'''    inner class Bridge {
        @JavascriptInterface
        fun runNamedTaskerTask(raw: String) = runOnUiThread {
            if (webView.url != "file:///android_asset/index.html" || !hasWindowFocus() || isFinishing) return@runOnUiThread
            val name = raw.trim()
            if (name.isEmpty() || name.length > 100 || name.any { it.isISOControl() }) return@runOnUiThread
            val perm = "net.dinglisch.android.tasker.PERMISSION_RUN_TASKS"
            val pkg = "net.dinglisch.android.taskerm"
            if (packageManager.getLaunchIntentForPackage(pkg) == null) {
                android.widget.Toast.makeText(this@MainActivity,"Tasker nu este instalat",android.widget.Toast.LENGTH_SHORT).show()
                return@runOnUiThread
            }
            if (checkSelfPermission(perm) != android.content.pm.PackageManager.PERMISSION_GRANTED) {
                requestPermissions(arrayOf(perm), 9122)
                android.widget.Toast.makeText(this@MainActivity,"După acordarea permisiunii, apăsați din nou Execută.",android.widget.Toast.LENGTH_LONG).show()
                return@runOnUiThread
            }
            android.app.AlertDialog.Builder(this@MainActivity)
                .setTitle("Executare Tasker")
                .setMessage("Cu mașina staționată, confirmați executarea sarcinii: "+name)
                .setNegativeButton("Anulează",null)
                .setPositiveButton("Execută") { _,_ ->
                    try {
                        val intent = Intent("net.dinglisch.android.tasker.ACTION_TASK")
                            .setPackage(pkg).putExtra("task_name",name)
                        sendBroadcast(intent)
                        android.widget.Toast.makeText(this@MainActivity,"Cerere transmisă; verificați jurnalul Tasker.",android.widget.Toast.LENGTH_LONG).show()
                    } catch (_: SecurityException) {
                        android.widget.Toast.makeText(this@MainActivity,"Tasker: acces extern refuzat",android.widget.Toast.LENGTH_SHORT).show()
                    }
                }.show()
        }
''',1)
p.write_text(s)
p=root/"app/src/main/assets/bid_general.js"
s=p.read_text()
anchor="button('Închide',"
assert s.count(anchor)==1
s=s.replace(anchor,"""const taskerPanel=document.createElement('fieldset');
const taskerLegend=document.createElement('legend');taskerLegend.textContent='Executare sarcină Tasker';taskerPanel.append(taskerLegend);
const taskerName=document.createElement('input');taskerName.type='text';taskerName.maxLength=100;taskerName.placeholder='Numele exact al sarcinii';taskerPanel.append(taskerName);
const taskerRun=document.createElement('button');taskerRun.textContent='Execută sarcina';taskerRun.onclick=()=>{const name=taskerName.value.trim();if(!name||name.length>100)return;try{native().runNamedTaskerTask(name);}catch(_){alert('Tasker indisponibil');}};taskerPanel.append(taskerRun);
const taskerHelp=document.createElement('p');taskerHelp.textContent='Necesită Tasker instalat, Allow External Access și permisiunea Android. Cererea transmisă nu confirmă executarea.';taskerPanel.append(taskerHelp);modal.append(taskerPanel);
"""+anchor,1)
p.write_text(s)
