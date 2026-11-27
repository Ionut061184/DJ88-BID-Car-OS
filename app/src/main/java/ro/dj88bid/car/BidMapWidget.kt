package ro.dj88bid.car

import android.app.Activity
import android.app.AlertDialog
import android.appwidget.AppWidgetHost
import android.appwidget.AppWidgetManager
import android.appwidget.AppWidgetProviderInfo
import android.content.Intent
import android.graphics.Color
import android.graphics.Outline
import android.os.Bundle
import android.view.View
import android.view.ViewOutlineProvider
import android.view.MotionEvent
import android.webkit.JavascriptInterface
import android.webkit.WebView
import android.widget.FrameLayout
import android.widget.LinearLayout
import android.widget.SeekBar
import android.widget.TextView
import android.widget.Toast
import kotlin.math.roundToInt

/** Hosts only published Android AppWidgets. No Maps SDK, no key, no private API. */
class BidMapWidget(private val activity: Activity, private val root: FrameLayout, private val web: WebView) {
    companion object {
        const val BIND = 731
        const val CONFIGURE = 732
        const val MAPS = "com.google.android.apps.maps"
    }
    private val manager = AppWidgetManager.getInstance(activity)
    private val host = AppWidgetHost(activity, 8801)
    private val prefs = activity.getSharedPreferences("bid_map_widget", Activity.MODE_PRIVATE)
    private var widgetId = prefs.getInt("id", -1)
    private var pending = prefs.getInt("pending", -1)
    private var enabled = prefs.getBoolean("enabled", false)
    private var opacity = prefs.getInt("opacity", 100).coerceIn(0,100)
    private var foreground = false
    private var visible = false
    private var moving = true
    private var radius = 0f
    private var lastBounds: IntArray? = null
    private var child: View? = null
    private val slot = object : FrameLayout(activity) {
        override fun onInterceptTouchEvent(ev: MotionEvent): Boolean = true
        override fun onTouchEvent(ev: MotionEvent): Boolean {
            if (ev.actionMasked == MotionEvent.ACTION_UP) performClick()
            return true
        }
        override fun performClick(): Boolean {
            super.performClick()
            if (!moving) menu()
            return true
        }
    }.apply {
        setBackgroundColor(Color.TRANSPARENT)
        clipToOutline = true
        outlineProvider = object : ViewOutlineProvider() {
            override fun getOutline(v: View, o: Outline) {
                o.setRoundRect(0, 0, v.width, v.height, radius.coerceAtMost(v.height / 2f))
            }
        }
        visibility = View.GONE
        contentDescription = "Widget Google Maps · atinge pentru setări la staționare"
        isClickable = true
    }
    init { root.addView(slot, FrameLayout.LayoutParams(1,1)); attach() }
    private fun toast(text: String) = Toast.makeText(activity,text,Toast.LENGTH_LONG).show()
    private fun emit() {
        val installed = try { providers().size } catch (_:Exception) { 0 }
        val state = org.json.JSONObject().put("available", installed).put("enabled", enabled && child != null)
        web.evaluateJavascript("if(window.bidWidgetState)window.bidWidgetState($state);",null)
    }
    private fun providers(): List<AppWidgetProviderInfo> =
        manager.installedProviders.filter { it.provider.packageName == MAPS }
            .sortedBy { it.loadLabel(activity.packageManager) }
    private fun showIfReady() {
        slot.visibility = if (foreground && enabled && child != null && visible && lastBounds != null) View.VISIBLE else View.GONE
        child?.alpha = opacity / 100f
    }
    private fun attach() {
        slot.removeAllViews(); child = null
        if (widgetId >= 0) {
            val info = try { manager.getAppWidgetInfo(widgetId) } catch (_:Exception) { null }
            if (info == null || info.provider.packageName != MAPS) {
                try { host.deleteAppWidgetId(widgetId) } catch (_:Exception) {}
                widgetId = -1; enabled = false; save()
            } else try {
                val v = host.createView(activity,widgetId,info)
                v.setPadding(0,0,0,0)
                slot.addView(v,FrameLayout.LayoutParams(-1,-1)); child = v
                lastBounds?.let { sizeWidget(it[2],it[3]) }
            } catch (_:Exception) { enabled = false; save() }
        }
        showIfReady(); emit()
    }
    private fun sizeWidget(w: Int,h: Int) {
        val density=activity.resources.displayMetrics.density
        val width=(w/density).roundToInt().coerceAtLeast(1)
        val height=(h/density).roundToInt().coerceAtLeast(1)
        try { manager.updateAppWidgetOptions(widgetId, Bundle().apply {
            putInt(AppWidgetManager.OPTION_APPWIDGET_MIN_WIDTH,width)
            putInt(AppWidgetManager.OPTION_APPWIDGET_MAX_WIDTH,width)
            putInt(AppWidgetManager.OPTION_APPWIDGET_MIN_HEIGHT,height)
            putInt(AppWidgetManager.OPTION_APPWIDGET_MAX_HEIGHT,height)
        }) } catch (_:Exception) {}
    }
    private fun save() {
        prefs.edit().putInt("id",widgetId).putInt("pending",pending).putBoolean("enabled",enabled).putInt("opacity",opacity).apply()
    }
    fun start() { foreground=true; try { host.startListening() } catch (_:Exception) {}; showIfReady() }
    fun stop() { foreground=false; slot.visibility=View.GONE; try { host.stopListening() } catch (_:Exception) {} }
    @JavascriptInterface fun sync(x: Double,y: Double,w: Double,h: Double,viewW: Double,viewH: Double,show: Boolean,stationary: Boolean) {
        activity.runOnUiThread {
            moving = !stationary
            visible = show
            if (listOf(x,y,w,h,viewW,viewH).all { it.isFinite() } && viewW>0 && viewH>0 && w>0 && h>0 && x>=0 && y>=0 && x+w<=viewW+1 && y+h<=viewH+1 && root.width>0 && root.height>0) {
                val sx=root.width/viewW; val sy=root.height/viewH
                val rect=intArrayOf((x*sx).roundToInt(),(y*sy).roundToInt(),(w*sx).roundToInt().coerceAtLeast(1),(h*sy).roundToInt().coerceAtLeast(1))
                if (lastBounds?.contentEquals(rect)!=true) {
                    radius=(25.0*rect[2]/155.5).toFloat()
                    slot.layoutParams=FrameLayout.LayoutParams(rect[2],rect[3]).apply { leftMargin=rect[0];topMargin=rect[1] }
                    slot.invalidateOutline();lastBounds=rect
                    if(widgetId>=0) sizeWidget(rect[2],rect[3])
                }
            } else { visible=false }
            showIfReady()
        }
    }
    @JavascriptInterface fun open() { activity.runOnUiThread { menu() } }
    @JavascriptInterface fun state() { activity.runOnUiThread { emit() } }
    @JavascriptInterface fun photo() { activity.runOnUiThread { enabled=false;save();showIfReady();emit() } }
    private fun menu() {
        if (moving) { toast("Setează widgetul când mașina staționează și GPS-ul este valid.");return }
        val list = arrayOf("Alege widget Google Maps", "Afișează widgetul salvat", "Transparență", "Revino la Smart Drive Foto", "Elimină widgetul")
        AlertDialog.Builder(activity).setTitle("BID · Widget Google Maps")
            .setItems(list) { _, i -> when(i) {
                0 -> choose()
                1 -> { enabled = child != null;save();showIfReady();emit();if(!enabled)choose() }
                2 -> transparency()
                3 -> { enabled=false;save();showIfReady();emit() }
                4 -> remove()
            } }.setNegativeButton("Închide",null).show()
    }
    private fun choose() {
        if (pending>=0) { cancelPending() }
        val entries = try { providers() } catch (_:Exception) { emptyList() }
        if(entries.isEmpty()) {
            AlertDialog.Builder(activity).setTitle("Google Maps · widget indisponibil")
                .setMessage("Versiunea Google Maps instalată nu publică widgeturi Android vizibile acestui launcher. Nu se poate integra o hartă prin AppWidgetHost. Smart Drive Foto rămâne disponibil.")
                .setPositiveButton("OK",null).show();emit();return
        }
        val labels=entries.map { it.loadLabel(activity.packageManager)+" · "+it.minWidth+" × "+it.minHeight+" dp\n"+it.provider.className.substringAfterLast('.') }.toTypedArray()
        AlertDialog.Builder(activity).setTitle("Widgeturi publicate de Google Maps")
            .setItems(labels){_, i ->
                val info=entries[i]
                AlertDialog.Builder(activity).setTitle(info.loadLabel(activity.packageManager))
                    .setMessage("Conținutul este oferit de Google Maps; poate fi hartă, trafic sau scurtătură. Caseta mică poate fi sub dimensiunea minimă. Confirmă pentru test.")
                    .setPositiveButton("Adaugă"){_,_->bind(info)}.setNegativeButton("Renunță",null).show()
            }.setNegativeButton("Renunță",null).show()
    }
    private fun bind(info:AppWidgetProviderInfo) {
        try {
            pending=host.allocateAppWidgetId();save()
            if(manager.bindAppWidgetIdIfAllowed(pending,info.profile,info.provider,null)) configure()
            else activity.startActivityForResult(Intent(AppWidgetManager.ACTION_APPWIDGET_BIND)
                .putExtra(AppWidgetManager.EXTRA_APPWIDGET_ID,pending)
                .putExtra(AppWidgetManager.EXTRA_APPWIDGET_PROVIDER,info.provider)
                .putExtra(AppWidgetManager.EXTRA_APPWIDGET_PROVIDER_PROFILE,info.profile),BIND)
        } catch (_:Exception) { cancelPending();toast("Android nu a permis adăugarea widgetului.") }
    }
    private fun configure() {
        val info=manager.getAppWidgetInfo(pending)
        if(info==null || info.provider.packageName!=MAPS){cancelPending();return}
        try {
            if(info.configure!=null) host.startAppWidgetConfigureActivityForResult(activity,pending,0,CONFIGURE,null)
            else finishBinding()
        } catch (_:Exception){cancelPending();toast("Configurarea widgetului nu este disponibilă.")}
    }
    fun result(request:Int,result:Int):Boolean {
        if(request!=BIND && request!=CONFIGURE)return false
        if(pending<0)return true
        if(result!=Activity.RESULT_OK){cancelPending();return true}
        if(request==BIND)configure() else finishBinding()
        return true
    }
    private fun finishBinding(){
        if(manager.getAppWidgetInfo(pending)?.provider?.packageName!=MAPS){cancelPending();return}
        if(widgetId>=0)try{host.deleteAppWidgetId(widgetId)}catch(_:Exception){}
        widgetId=pending;pending=-1;enabled=true;save();attach()
    }
    private fun cancelPending(){if(pending>=0)try{host.deleteAppWidgetId(pending)}catch(_:Exception){};pending=-1;save()}
    private fun remove(){if(widgetId>=0)try{host.deleteAppWidgetId(widgetId)}catch(_:Exception){};widgetId=-1;enabled=false;save();attach()}
    private fun transparency(){
        val layout=LinearLayout(activity).apply{orientation=LinearLayout.VERTICAL;setPadding(24,16,24,16)}
        val txt=TextView(activity).apply{text="Opacitate: $opacity%";layout.addView(this)}
        layout.addView(SeekBar(activity).apply{max=100;progress=opacity;setOnSeekBarChangeListener(object:SeekBar.OnSeekBarChangeListener{
            override fun onProgressChanged(s:SeekBar,p:Int,fromUser:Boolean){opacity=p;txt.text="Opacitate: $p%";showIfReady()}
            override fun onStartTrackingTouch(s:SeekBar){}
            override fun onStopTrackingTouch(s:SeekBar){save()}
        })})
        AlertDialog.Builder(activity).setTitle("Transparență widget (0% opacitate = transparent)").setView(layout).setPositiveButton("Salvează"){_,_->save()}.setOnDismissListener{save()}.show()
    }
}
