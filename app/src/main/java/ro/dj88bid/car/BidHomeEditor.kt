package ro.dj88bid.car

import android.app.Activity
import android.app.AlertDialog
import android.content.Intent
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Paint
import android.graphics.RectF
import android.net.Uri
import android.util.AtomicFile
import android.view.View
import android.webkit.WebResourceResponse
import android.widget.Toast
import java.io.ByteArrayInputStream
import java.io.File

/** Exact-size replacement artwork; fixed and unchanged touch targets. */
class BidHomeEditor(private val activity: Activity, private val changed: () -> Unit) {
    companion object {
        const val HOST = "bid-home.invalid"
        const val REQUEST = 580
        const val WIDTH = 1280
        const val HEIGHT = 720
    }
    private val active = File(activity.filesDir,"bid_home_custom.png")
    private var busy = false
    @Volatile private var revision = System.nanoTime()
    fun activeUrl(): String? =
        if(active.isFile) "https://"+HOST+"/home.png?v="+revision else null

    // The sole virtual resource is an image from app-private storage. No network fallback.
    fun serve(uri: Uri, method: String): WebResourceResponse {
        if(uri.scheme=="https" && uri.host==HOST && uri.path=="/home.png" && method=="GET") {
            try {
                return WebResourceResponse("image/png",null,200,"OK",
                    mapOf("Cache-Control" to "no-store","X-Content-Type-Options" to "nosniff"),
                    AtomicFile(active).openRead())
            } catch (_:Exception) {}
        }
        return WebResourceResponse("text/plain","UTF-8",404,"Not Found",
            mapOf("Cache-Control" to "no-store"), ByteArrayInputStream(ByteArray(0)))
    }

    fun show() {
        if(busy || activity.isFinishing || activity.isDestroyed)return
        AlertDialog.Builder(activity).setTitle("BID · Editor ecran principal")
            .setItems(arrayOf("Importă imagine completă 1280 × 720","Previzualizează ecranul actual",
                "Restabilește designul original")) { _,i ->
                when(i) {
                    0 -> pick()
                    1 -> {
                        val bmp = try {
                            if(active.isFile) AtomicFile(active).openRead().use { BitmapFactory.decodeStream(it) }
                            else activity.assets.open("bid_fullbleed.png").use { BitmapFactory.decodeStream(it) }
                        } catch (_:Exception) { null }
                        if(bmp!=null) preview(bmp,false) else toast("Previzualizare indisponibilă.")
                    }
                    2 -> AlertDialog.Builder(activity).setTitle("Restabilești designul original BID?")
                        .setNegativeButton("Anulează",null).setPositiveButton("Restabilește") { _,_ ->
                            AtomicFile(active).delete()
                            revision=System.nanoTime()
                            changed()
                            toast("Designul original a fost restabilit.")
                        }.show()
                }
            }.setNegativeButton("Închide",null).show()
    }
    private fun pick() {
        try {
            activity.startActivityForResult(Intent(Intent.ACTION_OPEN_DOCUMENT).apply {
                addCategory(Intent.CATEGORY_OPENABLE)
                type="image/*"
                addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
            },REQUEST)
        } catch (_:Exception) { toast("Selectorul de imagini nu este disponibil.") }
    }

    fun handleResult(code:Int,result:Int,data:Intent?) {
        if(code!=REQUEST || result!=Activity.RESULT_OK || busy)return
        val uri=data?.data ?:return
        if(uri.scheme!="content")return
        busy=true
        Thread {
            var bmp:Bitmap?=null
            var staging:File?=null
            try {
                val tmp=File.createTempFile("bid_home_",".tmp",activity.cacheDir)
                staging=tmp
                activity.contentResolver.openInputStream(uri)?.use { input ->
                    tmp.outputStream().use { out ->
                        val buf=ByteArray(65536)
                        var total=0L
                        while(true){
                            val n=input.read(buf)
                            if(n<0)break
                            total+=n
                            require(total<=16L*1024*1024)
                            out.write(buf,0,n)
                        }
                    }
                } ?: error("No stream")
                val bounds=BitmapFactory.Options().apply{inJustDecodeBounds=true}
                BitmapFactory.decodeFile(tmp.path,bounds)
                require(bounds.outWidth==WIDTH && bounds.outHeight==HEIGHT)
                require(bounds.outMimeType in setOf("image/png","image/jpeg","image/webp"))
                bmp=BitmapFactory.decodeFile(tmp.path)
            } catch (_:Exception) {} finally { staging?.delete() }
            val image=bmp
            activity.runOnUiThread {
                busy=false
                if(activity.isFinishing || activity.isDestroyed) { image?.recycle(); return@runOnUiThread }
                if(image==null) toast("Imagine respinsă: PNG/JPEG/WebP, exact 1280 × 720, max. 16 MiB.")
                else preview(image,true)
            }
        }.start()
    }

    // Coordinates audited from the approved index.html. All boxes are preview-only.
    private data class Zone(val name:String,val x:Int,val y:Int,val w:Int,val h:Int)
    private val zones = listOf(
        Zone("Acasă",25,12,90,70),Zone("Dată",283,8,275,59),Zone("BID",555,9,173,165),
        Zone("Vreme",786,13,202,62),Zone("BT",989,13,44,62),Zone("Wi-Fi",1035,13,51,62),
        Zone("Rețea",1088,13,45,62),Zone("Baterie",1140,13,124,62),
        Zone("Radio",20,84,158,105),Zone("Muzică",20,191,158,92),Zone("Telefon",20,286,158,95),
        Zone("GPS",20,383,158,95),Zone("Aplicații",20,481,158,124),
        Zone("Mașină",1108,84,154,105),Zone("Setări",1108,191,154,92),Zone("Sunet",1108,286,154,95),
        Zone("CarPlay",1108,383,154,95),Zone("Android Auto",1108,481,154,124),
        Zone("Funcții",174,622,187,72),Zone("YouTube",362,622,170,72),Zone("Waze",533,622,148,72),
        Zone("Play Store",680,622,181,72),Zone("Chrome",861,622,244,72))

    private fun preview(image:Bitmap,canApply:Boolean) {
        val view=object:View(activity) {
            private val paint=Paint(Paint.ANTI_ALIAS_FLAG)
            override fun onMeasure(w:Int,h:Int) {
                val width=MeasureSpec.getSize(w)
                val maxH=MeasureSpec.getSize(h)
                val wanted=(width*HEIGHT.toFloat()/WIDTH).toInt()
                setMeasuredDimension(width,if(maxH>0)minOf(wanted,maxH) else wanted)
            }
            override fun onDraw(c:Canvas) {
                super.onDraw(c)
                val scale=minOf(width.toFloat()/WIDTH,height.toFloat()/HEIGHT)
                c.save()
                c.translate((width-WIDTH*scale)/2f,(height-HEIGHT*scale)/2f)
                c.scale(scale,scale)
                paint.style=Paint.Style.FILL
                c.drawBitmap(image,null,RectF(0f,0f,WIDTH.toFloat(),HEIGHT.toFloat()),paint)
                for(z in zones) {
                    paint.style=Paint.Style.STROKE;paint.strokeWidth=2f;paint.color=Color.CYAN
                    c.drawRect(z.x.toFloat(),z.y.toFloat(),(z.x+z.w).toFloat(),(z.y+z.h).toFloat(),paint)
                    paint.style=Paint.Style.FILL;paint.color=Color.CYAN
                    paint.textSize=14f
                    c.drawText(z.name,z.x+4f,z.y+17f,paint)
                }
                c.restore()
            }
        }
        val builder=AlertDialog.Builder(activity).setTitle("Verifică zonele tactile")
            .setMessage("Contururile sunt doar pentru verificare. Nu mută comenzile. Verifică toate pictogramele înainte de aplicare.")
            .setView(view).setNegativeButton("Închide",null)
        if(canApply) builder.setPositiveButton("Aplică") { _,_ ->
            // Keep an independent bitmap until the worker finishes; original is never replaced.
            val copy=image.copy(Bitmap.Config.ARGB_8888,false)
            if(copy==null) { toast("Memorie insuficientă pentru salvare."); return@setPositiveButton }
            busy=true
            Thread {
                var ok=false
                try {
                    val target=AtomicFile(active)
                    val out=target.startWrite()
                    try {
                        require(copy.compress(Bitmap.CompressFormat.PNG,100,out))
                        target.finishWrite(out);ok=true
                    } catch(e:Exception) { target.failWrite(out);throw e }
                } catch (_:Exception) {} finally { copy.recycle() }
                activity.runOnUiThread {
                    busy=false
                    if(ok)revision=System.nanoTime()
                    if(!activity.isFinishing && !activity.isDestroyed) {
                        if(ok)changed()
                        toast(if(ok)"Ecran personalizat salvat." else "Salvare nereușită; ecranul anterior a fost păstrat.")
                    }
                }
            }.start()
        }
        val dialog=builder.create()
        dialog.setOnDismissListener { image.recycle() }
        dialog.show()
    }
    private fun toast(s:String)=Toast.makeText(activity,s,Toast.LENGTH_LONG).show()
}
