package ro.dj88bid.car

import android.app.Activity
import android.content.Intent
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.graphics.ImageDecoder
import android.os.Build
import android.net.Uri
import android.util.Base64
import android.webkit.JavascriptInterface
import android.webkit.WebView
import org.json.JSONObject
import java.io.ByteArrayOutputStream
import java.util.concurrent.Executors
import kotlin.math.max
import kotlin.math.roundToInt

/** Local image picker for user-created themes. No storage permission or network. */
class BidThemeImage(private val activity: Activity, private val web: WebView) {
    companion object { const val REQUEST = 736 }
    private val worker = Executors.newSingleThreadExecutor()
    private var pending = false
    private var closed = false
    private val trusted = "file:///android_asset/index.html"
    private fun reply(data: String?, message: String) {
        activity.runOnUiThread {
            pending = false
            if (closed || activity.isFinishing || web.url != trusted) return@runOnUiThread
            val json = JSONObject().put("image",data ?: JSONObject.NULL).put("message",message)
            web.evaluateJavascript("if(window.bidThemeImageResult)window.bidThemeImageResult($json);",null)
        }
    }
    @JavascriptInterface fun pick() {
        activity.runOnUiThread {
            if (closed || pending || activity.isFinishing || web.url != trusted) return@runOnUiThread
            pending = true
            val intent = Intent(Intent.ACTION_OPEN_DOCUMENT).apply {
                addCategory(Intent.CATEGORY_OPENABLE)
                type = "image/*"
                putExtra(Intent.EXTRA_MIME_TYPES,arrayOf("image/jpeg","image/png","image/webp","image/gif"))
                addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
            }
            try { activity.startActivityForResult(intent,REQUEST) }
            catch (_:Exception) {
                try { activity.startActivityForResult(Intent(Intent.ACTION_GET_CONTENT).apply {
                    addCategory(Intent.CATEGORY_OPENABLE);type="image/*"
                    addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
                },REQUEST) }
                catch (_:Exception) { reply(null,"Selectorul Android de imagini este indisponibil.") }
            }
        }
    }
    fun result(request:Int,code:Int,data:Intent?):Boolean {
        if(request!=REQUEST)return false
        if(closed || !pending)return true
        val uri=data?.data
        if(code!=Activity.RESULT_OK || uri==null) { reply(null,"Alegerea imaginii a fost anulată.");return true }
        if(uri.scheme!="content"){reply(null,"Imaginea nu a fost oferită prin selectorul Android.");return true}
        worker.execute {
            try {
                val type=activity.contentResolver.getType(uri)
                if(type!=null && type !in listOf("image/jpeg","image/png","image/webp","image/gif"))error("Format neacceptat. Alege JPG, PNG sau WebP.")
                if(type=="image/gif"){
                    val cr=activity.contentResolver
                    val b=cr.openInputStream(uri)?.use { input ->
                        val out=ByteArrayOutputStream(); val buf=ByteArray(8192)
                        while(true){val n=input.read(buf);if(n<0)break;if(out.size()+n>400000)error("GIF maxim 400 KB.");out.write(buf,0,n)}
                        out.toByteArray()
                    } ?: error("GIF indisponibil.")
                    require(b.size>=13 && (String(b,0,6,Charsets.US_ASCII)=="GIF87a" || String(b,0,6,Charsets.US_ASCII)=="GIF89a")){"GIF invalid."}
                    val w=(b[6].toInt() and 255)+256*(b[7].toInt() and 255)
                    val h=(b[8].toInt() and 255)+256*(b[9].toInt() and 255)
                    require(w in 1..1280 && h in 1..720){"GIF maxim 1280 × 720."}
                    reply("data:image/gif;base64,"+Base64.encodeToString(b,Base64.NO_WRAP),"GIF selectat. Salvează tema.")
                    return@execute
                }
                val bitmap=decode(uri)
                try {
                    if(bitmap.hasAlpha() && type!="image/jpeg"){
                        var current=bitmap
                        try {
                            while(true){
                                val out=ByteArrayOutputStream()
                                if(!current.compress(Bitmap.CompressFormat.PNG,100,out))error("PNG invalid.")
                                if(out.size()<=400000){
                                    reply("data:image/png;base64,"+Base64.encodeToString(out.toByteArray(),Base64.NO_WRAP),"Imagine cu transparență păstrată.")
                                    return@execute
                                }
                                if(max(current.width,current.height)<=160)error("PNG prea mare.")
                                val scaled=Bitmap.createScaledBitmap(current,(current.width*0.75).roundToInt().coerceAtLeast(1),(current.height*0.75).roundToInt().coerceAtLeast(1),true)
                                if(current!==bitmap)current.recycle()
                                current=scaled
                            }
                        } finally { if(current!==bitmap)current.recycle() }
                    }
                    var bytes:ByteArray?=null
                    for(q in listOf(82,68,52,36)){
                        val stream=ByteArrayOutputStream()
                        if(!bitmap.compress(Bitmap.CompressFormat.JPEG,q,stream))error("Imaginea nu poate fi comprimată.")
                        val b=stream.toByteArray()
                        if(b.size<=400000){bytes=b;break}
                    }
                    val result=bytes?:error("Imaginea este prea mare după redimensionare.")
                    reply("data:image/jpeg;base64,"+Base64.encodeToString(result,Base64.NO_WRAP),"Imagine selectată. Salvează tema.")
                }finally{bitmap.recycle()}
            }catch(e:Exception){reply(null,e.message?.take(160)?:"Imaginea nu a putut fi citită.")}
            catch(_:OutOfMemoryError){reply(null,"Imaginea depășește memoria disponibilă.")}
        }
        return true
    }
    private fun decode(uri:Uri):Bitmap {
        val cr=activity.contentResolver
        if(Build.VERSION.SDK_INT>=28){
            return ImageDecoder.decodeBitmap(ImageDecoder.createSource(cr,uri)){ decoder,info,_->
                val w=info.size.width;val h=info.size.height
                require(w>0 && h>0)
                val scale=minOf(1.0,1280.0/max(w,h))
                decoder.setTargetSize((w*scale).roundToInt().coerceAtLeast(1),(h*scale).roundToInt().coerceAtLeast(1))
                decoder.allocator=ImageDecoder.ALLOCATOR_SOFTWARE
            }
        }
        val bounds=BitmapFactory.Options().apply{inJustDecodeBounds=true}
        cr.openInputStream(uri)?.use{BitmapFactory.decodeStream(it,null,bounds)}
        require(bounds.outWidth>0 && bounds.outHeight>0){"Imagine invalidă."}
        var sample=1
        while(max(bounds.outWidth,bounds.outHeight)/sample>1280)sample*=2
        val options=BitmapFactory.Options().apply{inSampleSize=sample;inPreferredConfig=Bitmap.Config.ARGB_8888}
        return cr.openInputStream(uri)?.use{BitmapFactory.decodeStream(it,null,options)}?:error("Imaginea nu poate fi citită.")
    }
    fun close(){closed=true;pending=false;worker.shutdownNow()}
}
