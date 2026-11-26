package ro.dj88bid.car

import android.app.Activity
import android.app.AlertDialog
import android.content.Intent
import android.content.SharedPreferences
import android.graphics.BitmapFactory
import android.net.Uri
import android.widget.Toast
import org.json.JSONObject
import java.io.File
import java.io.InputStream
import java.io.OutputStream
import java.security.MessageDigest
import java.util.zip.ZipEntry
import java.util.zip.ZipInputStream
import java.util.zip.ZipOutputStream

/** Cosmetic profiles only. The legacy working profile and approved artwork stay intact. */
class BidThemeProfiles(private val activity:Activity, private val editorsBusy:()->Boolean,
                       private val changed:()->Unit) {
    private val prefs=activity.getSharedPreferences("bid_theme_profiles_v1",Activity.MODE_PRIVATE)
    @Volatile private var selected=prefs.getInt("active",0).coerceIn(0,5)
    private var busy=false
    private val root=File(activity.filesDir,"bid_theme_profiles")
    private val names=listOf("bid_home_custom.png","bid_appearance_background.png",
        "bid_appearance_radio.png","bid_appearance_music.png","bid_appearance_btmusic.png",
        "bid_appearance_dsp.png","bid_appearance_maps.png","bid_appearance_waze.png",
        "bid_appearance_youtube.png","bid_appearance_files.png")
    private val limit=16L*1024*1024
    private val totalLimit=40L*1024*1024
    private val importBase=610
    private val exportCode=616
    fun current()=selected
    fun isBusy()=busy
    private fun dir(slot:Int)=if(slot==0)activity.filesDir else File(root,"slot_"+slot)
    private fun available(slot:Int)=slot==0 || File(dir(slot),"ready").isFile
    fun asset(name:String):File {
        require(name in names)
        return File(dir(selected),name)
    }
    private fun palettePrefs(slot:Int):SharedPreferences =
        activity.getSharedPreferences(if(slot==0)"bid_appearance_v1" else "bid_appearance_slot_"+slot,Activity.MODE_PRIVATE)
    fun appearancePrefs()=palettePrefs(selected)
    private fun label(slot:Int)=if(slot==0)"Profil de lucru" else "Tema "+slot
    private fun activate(slot:Int) {
        if(busy||editorsBusy()||!available(slot))return
        if(!prefs.edit().putInt("active",slot).commit()) { toast("Nu s-a putut salva selecția.");return }
        selected=slot
        changed()
        toast(label(slot)+" activă. Redeschide Funcții.")
    }
    fun show() {
        if(busy||editorsBusy()||activity.isFinishing||activity.isDestroyed)return
        val labels=(0..5).map{label(it)+(if(it==selected)" · activă" else if(available(it))" · salvată" else " · liberă")}
        AlertDialog.Builder(activity).setTitle("BID · Teme salvate")
            .setItems((labels+"Exportă tema activă").toTypedArray()){_,i->
                if(i==6)pickExport() else slotMenu(i)
            }.setNegativeButton("Închide",null).show()
    }
    private fun slotMenu(slot:Int) {
        if(slot==0||available(slot)) {
            val actions=if(slot==0||slot==selected) arrayOf("Activează")
                else arrayOf("Activează","Șterge tema salvată")
            AlertDialog.Builder(activity).setTitle(label(slot)).setItems(actions){_,i->
                if(i==0)activate(slot)
                else AlertDialog.Builder(activity).setTitle("Ștergi "+label(slot)+"?")
                    .setNegativeButton("Anulează",null).setPositiveButton("Șterge"){_,_->
                        if(!busy&&!editorsBusy()&&slot!=selected&&slot!=0) {
                            val folder=dir(slot)
                            // Hide first; never delete the active theme.
                            if(File(folder,"ready").delete()) { folder.deleteRecursively();palettePrefs(slot).edit().clear().commit() }
                            show()
                        }
                    }.show()
            }.setNegativeButton("Înapoi"){_,_->show()}.show()
        } else AlertDialog.Builder(activity).setTitle(label(slot))
            .setItems(arrayOf("Salvează o copie a temei active","Importă temă ZIP")){_,i->
                if(i==0)copyCurrent(slot) else pickImport(slot)
            }.setNegativeButton("Înapoi"){_,_->show()}.show()
    }
    private fun pickImport(slot:Int) {
        if(busy||editorsBusy()||available(slot))return
        try {
            activity.startActivityForResult(Intent(Intent.ACTION_OPEN_DOCUMENT).apply {
                addCategory(Intent.CATEGORY_OPENABLE);type="application/zip"
                addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
            },importBase+slot)
        } catch(_:Exception){toast("Selector indisponibil.")}
    }
    private fun pickExport() {
        if(busy||editorsBusy())return
        try {
            activity.startActivityForResult(Intent(Intent.ACTION_CREATE_DOCUMENT).apply {
                addCategory(Intent.CATEGORY_OPENABLE);type="application/zip"
                putExtra(Intent.EXTRA_TITLE,"DJ88-BID-tema-"+selected+".zip")
                addFlags(Intent.FLAG_GRANT_WRITE_URI_PERMISSION)
            },exportCode)
        } catch(_:Exception){toast("Selector indisponibil.")}
    }
    fun handleResult(code:Int,result:Int,data:Intent?) {
        if(result!=Activity.RESULT_OK||busy||editorsBusy())return
        val uri=data?.data?:return
        if(uri.scheme!="content")return
        if(code==exportCode)export(uri)
        else if(code in importBase+1..importBase+5 && !available(code-importBase))importTheme(code-importBase,uri)
    }
    private fun worker(action:()->Unit) {
        if(busy||editorsBusy())return
        busy=true
        Thread {
            var ok=false
            try{action();ok=true}catch(_:Exception){}
            activity.runOnUiThread {
                busy=false
                if(!activity.isFinishing&&!activity.isDestroyed) {
                    toast(if(ok)"Operațiune reușită." else "Operațiune respinsă. Tema activă rămâne intactă; un export întrerupt poate lăsa un ZIP incomplet.")
                    show()
                }
            }
        }.start()
    }
    private fun copyBounded(input:InputStream,out:OutputStream,max:Long):Long {
        var total=0L;val buf=ByteArray(65536)
        while(true) {
            val n=input.read(buf);if(n<0)break
            total+=n;require(total<=max);out.write(buf,0,n)
        }
        return total
    }
    private fun hash(file:File):String {
        val digest=MessageDigest.getInstance("SHA-256")
        file.inputStream().use { input ->
            val buf=ByteArray(65536)
            while(true){val n=input.read(buf);if(n<0)break;digest.update(buf,0,n)}
        }
        return digest.digest().joinToString(""){"%02x".format(it.toInt() and 255)}
    }
    private fun validateImage(name:String,f:File) {
        require(name in names && f.length() in 1L..limit)
        val b=BitmapFactory.Options().apply{inJustDecodeBounds=true}
        BitmapFactory.decodeFile(f.path,b)
        require(b.outMimeType=="image/png")
        if(name=="bid_home_custom.png")require(b.outWidth==1280&&b.outHeight==720)
        else {
            val max=if(name=="bid_appearance_background.png")1280 else 256
            require(b.outWidth in 1..max && b.outHeight in 1..max)
        }
        val image=BitmapFactory.decodeFile(f.path)?:error("Invalid bitmap")
        image.recycle()
    }
    private fun staging():File {
        require(root.isDirectory||root.mkdirs())
        val f=File(root,"stage_"+java.util.UUID.randomUUID().toString())
        require(f.mkdir());return f
    }
    private fun publish(slot:Int,stage:File,palette:Int) {
        require(slot in 1..5&&!available(slot)&&palette in 0..3)
        val destination=dir(slot)
        if(destination.exists())require(destination.deleteRecursively())
        require(palettePrefs(slot).edit().clear().putInt("palette",palette).commit())
        File(stage,"ready").writeText("1")
        require(stage.renameTo(destination))
    }
    private fun copyCurrent(slot:Int) {
        val from=selected
        val palette=palettePrefs(from).getInt("palette",0).coerceIn(0,3)
        worker {
            val stage=staging()
            try{
                var total=0L
                for(name in names) {
                    val src=File(dir(from),name)
                    if(!src.isFile)continue
                    val dest=File(stage,name)
                    total+=src.inputStream().use { input->dest.outputStream().use{copyBounded(input,it,limit)} }
                    require(total<=totalLimit);validateImage(name,dest)
                }
                publish(slot,stage,palette)
            }finally{stage.deleteRecursively()}
        }
    }
    private fun export(uri:Uri) {
        val from=selected
        val palette=palettePrefs(from).getInt("palette",0).coerceIn(0,3)
        worker {
            val temp=File.createTempFile("bid_theme_",".zip",activity.cacheDir)
            try{
                val files=JSONObject()
                ZipOutputStream(temp.outputStream().buffered()).use { zip ->
                    var total=0L
                    for(name in names) {
                        val f=File(dir(from),name)
                        if(!f.isFile)continue
                        validateImage(name,f);total+=f.length();require(total<=totalLimit)
                        files.put(name,hash(f))
                        zip.putNextEntry(ZipEntry(name))
                        f.inputStream().use{copyBounded(it,zip,limit)}
                        zip.closeEntry()
                    }
                    val manifest=JSONObject().put("schema",1).put("kind","BID_THEME")
                        .put("palette",palette).put("files",files)
                    zip.putNextEntry(ZipEntry("manifest.json"))
                    zip.write(manifest.toString().toByteArray(Charsets.UTF_8));zip.closeEntry()
                }
                activity.contentResolver.openOutputStream(uri,"w")?.use{out->
                    temp.inputStream().use{copyBounded(it,out,totalLimit+1048576)}
                }?:error("No output")
            }finally{temp.delete()}
        }
    }
    private fun importTheme(slot:Int,uri:Uri) {
        worker {
            val stage=staging()
            try{
                val seen=mutableSetOf<String>();var total=0L
                activity.contentResolver.openInputStream(uri)?.use{raw->
                    ZipInputStream(raw.buffered()).use{zip->
                        while(true){
                            val entry=zip.nextEntry?:break
                            val name=entry.name
                            require(!entry.isDirectory && (name=="manifest.json"||name in names) && seen.add(name))
                            val out=File(stage,name)
                            total+=out.outputStream().use{copyBounded(zip,it,if(name=="manifest.json")8192L else limit)}
                            require(total<=totalLimit+8192L)
                            if(name!="manifest.json")validateImage(name,out)
                            zip.closeEntry()
                        }
                    }
                }?:error("No input")
                require("manifest.json" in seen)
                val manifest=JSONObject(File(stage,"manifest.json").readText())
                require(manifest.getInt("schema")==1&&manifest.getString("kind")=="BID_THEME")
                val palette=manifest.getInt("palette");require(palette in 0..3)
                val files=manifest.getJSONObject("files")
                require(files.keys().asSequence().toSet()==seen-"manifest.json")
                for(name in seen-"manifest.json")require(files.getString(name)==hash(File(stage,name)))
                require(File(stage,"manifest.json").delete())
                publish(slot,stage,palette)
            }finally{stage.deleteRecursively()}
        }
    }
    private fun toast(s:String)=Toast.makeText(activity,s,Toast.LENGTH_LONG).show()
}
