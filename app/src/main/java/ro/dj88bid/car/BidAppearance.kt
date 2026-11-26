package ro.dj88bid.car

import android.app.Activity
import android.app.AlertDialog
import android.content.Intent
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.graphics.drawable.BitmapDrawable
import android.graphics.drawable.ColorDrawable
import android.graphics.drawable.Drawable
import android.graphics.drawable.GradientDrawable
import android.graphics.drawable.LayerDrawable
import android.util.AtomicFile
import android.widget.Toast
import java.io.File

/** Optional private appearance for the native Functions drawer only. */
class BidAppearance(private val activity: Activity) {
    data class Palette(val colors: IntArray, val heading: Int, val accent: Int,
                       val activeDot: Int, val inactiveDot: Int)
    private val prefs = activity.getSharedPreferences("bid_appearance_v1", Activity.MODE_PRIVATE)
    private val names = arrayOf("BID original · Bordeaux / Champagne", "Obsidian / Champagne",
        "Racing Green / Champagne", "Dark Graphite / Platinum")
    private val palettes = arrayOf(
        Palette(intArrayOf(0xFF180B12.toInt(),0xFF4D192B.toInt(),0xFF110A10.toInt()),
            0xFFFFDEAE.toInt(),0xFFEAC189.toInt(),0xFFE7BA82.toInt(),0xFF8B7180.toInt()),
        Palette(intArrayOf(0xFF0C0B0D.toInt(),0xFF242126.toInt(),0xFF08080A.toInt()),
            0xFFFFDEAE.toInt(),0xFFEAC189.toInt(),0xFFE7BA82.toInt(),0xFF999199.toInt()),
        Palette(intArrayOf(0xFF0B1712.toInt(),0xFF14382B.toInt(),0xFF08130F.toInt()),
            0xFFFFDEAE.toInt(),0xFFEAC189.toInt(),0xFFE7BA82.toInt(),0xFF879E94.toInt()),
        Palette(intArrayOf(0xFF17181C.toInt(),0xFF34363C.toInt(),0xFF0D0E11.toInt()),
            0xFFF1F0EB.toInt(),0xFFD4D0C8.toInt(),0xFFE5E1D8.toInt(),0xFF999BA4.toInt())
    )
    // Only cosmetic assets for non-safety-critical shortcuts.
    private val keys = arrayOf("background","radio","music","btmusic","dsp","maps","waze","youtube","files")
    private val labels = arrayOf("Fundal sertar Funcții","Radio","Player muzical","Muzică Bluetooth",
        "DSP","Hărți","Waze","YouTube","Fișiere USB")
    private val requestBase = 560
    private var busy = false
    private fun file(key: String) = File(activity.filesDir,"bid_appearance_${key}.png")
    fun palette(): Palette = palettes[prefs.getInt("palette",0).coerceIn(palettes.indices)]
    fun background(p: Palette): Drawable {
        val base = GradientDrawable(GradientDrawable.Orientation.TOP_BOTTOM,p.colors)
        val img = decode("background") ?: return base
        // Dark scrim keeps labels legible. Default remains exactly the original gradient.
        return LayerDrawable(arrayOf<Drawable>(base,img,ColorDrawable(0xB8000000.toInt())))
    }
    fun icon(key: String): Drawable? = if (key != "background" && key in keys) decode(key) else null
    private fun decode(key: String): BitmapDrawable? = try {
        BitmapFactory.decodeFile(file(key).path)?.let { BitmapDrawable(activity.resources,it) }
    } catch (_: Exception) { null }
    fun show() {
        if (activity.isFinishing || activity.isDestroyed || busy) return
        AlertDialog.Builder(activity).setTitle("BID · Aspect personalizat")
            .setItems(arrayOf("Paletă de culori","Fundal și pictograme","Revino la aspectul original")) { _, pos ->
                when(pos) {
                    0 -> AlertDialog.Builder(activity).setTitle("Paleta sertarului Funcții")
                        .setSingleChoiceItems(names,prefs.getInt("palette",0).coerceIn(palettes.indices)) { dialog,i ->
                            prefs.edit().putInt("palette",i).apply()
                            dialog.dismiss(); toast("Paletă salvată. Redeschide Funcții.")
                        }.setNegativeButton("Anulează",null).show()
                    1 -> chooseAsset()
                    2 -> AlertDialog.Builder(activity).setTitle("Restabilești aspectul BID original?")
                        .setMessage("Se elimină doar personalizările sertarului Funcții. Imaginile mașinii și ecranul principal rămân intacte.")
                        .setNegativeButton("Anulează",null)
                        .setPositiveButton("Restabilește") { _,_ ->
                            keys.forEach { AtomicFile(file(it)).delete() }
                            prefs.edit().clear().apply()
                            toast("Aspect original restabilit.")
                        }.show()
                }
            }.setNegativeButton("Închide",null).show()
    }
    private fun chooseAsset() {
        val choices=labels.mapIndexed { i,s -> s + if(file(keys[i]).isFile) " · personalizat" else " · original" }.toTypedArray()
        AlertDialog.Builder(activity).setTitle("Fundal și pictograme")
            .setItems(choices) { _,i ->
                AlertDialog.Builder(activity).setTitle(labels[i])
                    .setItems(arrayOf("Importă / înlocuiește","Restabilește originalul")) { _,action ->
                        if(action==0) pick(i)
                        else { AtomicFile(file(keys[i])).delete(); toast("Original restabilit.") }
                    }.setNegativeButton("Anulează",null).show()
            }.setNegativeButton("Înapoi") { _,_ -> show() }.show()
    }
    private fun pick(i:Int) {
        if(busy)return
        try {
            activity.startActivityForResult(Intent(Intent.ACTION_OPEN_DOCUMENT).apply {
                addCategory(Intent.CATEGORY_OPENABLE)
                type="image/*"
                addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
            },requestBase+i)
        } catch (_:Exception) { toast("Selector indisponibil.") }
    }
    fun handleResult(code:Int,result:Int,data:Intent?) {
        val i=code-requestBase
        if(i !in keys.indices || result!=Activity.RESULT_OK || busy)return
        val uri=data?.data ?:return
        if(uri.scheme!="content")return
        busy=true
        Thread {
            var temp:File?=null
            var bitmap:Bitmap?=null
            var scaled:Bitmap?=null
            var ok=false
            try {
                val staging=File.createTempFile("bid_appearance_",".tmp",activity.cacheDir)
                temp=staging
                activity.contentResolver.openInputStream(uri)?.use { input ->
                    staging.outputStream().use { out ->
                        val buf=ByteArray(65536);var total=0L
                        while(true){
                            val n=input.read(buf)
                            if(n<0)break
                            total+=n;require(total<=16L*1024*1024)
                            out.write(buf,0,n)
                        }
                    }
                } ?: error("No stream")
                val bounds=BitmapFactory.Options().apply { inJustDecodeBounds=true }
                BitmapFactory.decodeFile(staging.path,bounds)
                require(bounds.outMimeType in setOf("image/png","image/jpeg","image/webp"))
                require(bounds.outWidth in 1..8192 && bounds.outHeight in 1..8192 &&
                    bounds.outWidth.toLong()*bounds.outHeight<=40000000L)
                val limit=if(i==0)1280 else 256
                var sample=1
                while(maxOf(bounds.outWidth,bounds.outHeight)/sample>limit*2)sample*=2
                val image=BitmapFactory.decodeFile(staging.path,BitmapFactory.Options().apply{inSampleSize=sample})
                    ?:error("Invalid image")
                bitmap=image
                val ratio=minOf(1f,limit.toFloat()/maxOf(image.width,image.height))
                val resultImage=if(ratio<1f)Bitmap.createScaledBitmap(image,
                    maxOf(1,(image.width*ratio).toInt()),maxOf(1,(image.height*ratio).toInt()),true) else image
                scaled=resultImage
                val target=AtomicFile(file(keys[i]))
                val out=target.startWrite()
                try {
                    require(resultImage.compress(Bitmap.CompressFormat.PNG,100,out))
                    target.finishWrite(out)
                } catch(e:Exception){target.failWrite(out);throw e}
                ok=true
            } catch (_:Exception) {
                // Preserve last valid customization.
            } finally {
                if(scaled!==bitmap)scaled?.recycle()
                bitmap?.recycle()
                temp?.delete()
            }
            activity.runOnUiThread {
                busy=false
                if(!activity.isFinishing && !activity.isDestroyed)
                    toast(if(ok)"Imagine salvată. Redeschide Funcții." else "Imagine respinsă; personalizarea anterioară a fost păstrată.")
            }
        }.start()
    }
    private fun toast(s:String)=Toast.makeText(activity,s,Toast.LENGTH_LONG).show()
}
