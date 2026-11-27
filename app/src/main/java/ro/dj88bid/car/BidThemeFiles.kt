package ro.dj88bid.car

import android.app.Activity
import android.content.Intent
import android.webkit.JavascriptInterface
import android.webkit.WebView
import org.json.JSONObject
import java.io.ByteArrayOutputStream
import java.util.concurrent.Executors

/** Explicit Storage Access Framework documents, no broad filesystem permission. */
class BidThemeFiles(private val activity:Activity,private val web:WebView) {
    companion object { const val WRITE=746; const val READ=747; const val MAX=6_000_000 }
    private val worker=Executors.newSingleThreadExecutor()
    private var pending=0
    private var payload:String?=null
    private var closed=false
    private val trusted="file:///android_asset/index.html"
    private fun reply(kind:String,ok:Boolean,message:String,data:String?=null){
        activity.runOnUiThread{
            pending=0;payload=null
            if(closed||activity.isFinishing||web.url!=trusted)return@runOnUiThread
            val result=JSONObject().put("kind",kind).put("ok",ok).put("message",message).put("data",data?:JSONObject.NULL)
            web.evaluateJavascript("if(window.bidThemeFileResult)window.bidThemeFileResult($result);",null)
        }
    }
    @JavascriptInterface fun exportDocument(name:String,json:String)=activity.runOnUiThread{
        if(closed||pending!=0||web.url!=trusted)return@runOnUiThread
        if(json.length>MAX||json.toByteArray(Charsets.UTF_8).size>MAX){reply("export",false,"Fișier prea mare.");return@runOnUiThread}
        val safe=name.replace(Regex("[^a-zA-Z0-9._-]"),"_").take(80).ifBlank{"BID-theme"}
        payload=json;pending=WRITE
        try{
            activity.startActivityForResult(Intent(Intent.ACTION_CREATE_DOCUMENT).addCategory(Intent.CATEGORY_OPENABLE)
                .setType("application/json").putExtra(Intent.EXTRA_TITLE,safe.removeSuffix(".json")+".json"),WRITE)
        }catch(_:Exception){reply("export",false,"Selectorul Android de fișiere este indisponibil.")}
    }
    @JavascriptInterface fun importDocument()=activity.runOnUiThread{
        if(closed||pending!=0||web.url!=trusted)return@runOnUiThread
        pending=READ
        try{activity.startActivityForResult(Intent(Intent.ACTION_OPEN_DOCUMENT).addCategory(Intent.CATEGORY_OPENABLE).setType("*/*")
            .putExtra(Intent.EXTRA_MIME_TYPES,arrayOf("application/json","text/plain","application/octet-stream")),READ)}
        catch(_:Exception){reply("import",false,"Selectorul Android de fișiere este indisponibil.")}
    }
    fun result(request:Int,code:Int,data:Intent?):Boolean{
        if(request!=WRITE&&request!=READ)return false
        if(closed||request!=pending)return true
        val kind=if(request==WRITE)"export" else "import"
        val uri=data?.data
        if(code!=Activity.RESULT_OK||uri==null){reply(kind,false,"Operațiune anulată.");return true}
        if(uri.scheme!="content"){reply(kind,false,"Document indisponibil.");return true}
        val text=payload
        worker.execute{
            try{
                if(request==WRITE){
                    require(text!=null)
                    activity.contentResolver.openOutputStream(uri,"wt")?.use{it.write(text.toByteArray(Charsets.UTF_8))}
                        ?:error("Nu se poate scrie documentul.")
                    reply(kind,true,"Fișier JSON exportat.")
                }else{
                    val bytes=activity.contentResolver.openInputStream(uri)?.use{input->
                        val out=ByteArrayOutputStream();val buffer=ByteArray(8192)
                        while(true){val n=input.read(buffer);if(n<0)break;if(out.size()+n>MAX)error("Fișier prea mare.");out.write(buffer,0,n)}
                        out.toByteArray()
                    }?:error("Document indisponibil.")
                    val value=Charsets.UTF_8.newDecoder().decode(java.nio.ByteBuffer.wrap(bytes)).toString().removePrefix("\uFEFF")
                    reply(kind,true,"Fișier citit. Se verifică structura.",value)
                }
            }catch(e:Exception){reply(kind,false,e.message?.take(160)?:"Operațiunea a eșuat.")}
        }
        return true
    }
    fun close(){closed=true;pending=0;payload=null;worker.shutdownNow()}
}
