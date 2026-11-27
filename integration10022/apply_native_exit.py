from pathlib import Path
import sys
root=Path(sys.argv[1])
p=root/"app/src/main/assets/bid_theme_builder.js"
s=p.read_text()
def replace(old,new):
    global s
    assert s.count(old)==1, "Missing or ambiguous anchor: "+old[:100]
    s=s.replace(old,new,1)
replace("function shiftLivePage(d){", """function nativeExitAllowed(){return !moving()&&panel.dataset.available==='true'&&!reduceMotion&&!document.hidden&&!live.hidden&&!edit&&!window.matchMedia?.('(prefers-reduced-motion: reduce)').matches;}
function requestNativeExits(t){if(!nativeExitAllowed()||!t)return;const keys=t.elements.filter(e=>e.type==='external'&&e.exit!=='none'&&e.alpha).map(e=>externalKey(t,e));if(keys.length)try{window.BIDThemeWidgets?.animateExit(JSON.stringify(keys));}catch(_){}}
function shiftLivePage(d){""")
replace("livePageId=next;renderLive();playExits(items,active());","requestNativeExits(t);livePageId=next;renderLive();playExits(items,active());")
replace("function syncExternal(){if(!window.BIDThemeWidgets)return;","function syncExternal(){if(!window.BIDThemeWidgets)return;if(!nativeExitAllowed())try{BIDThemeWidgets.cancelExits();}catch(_){}")
# Enable exit property for external widgets without enabling unsupported map exits.
# Earlier entrance patch transforms these clauses; accept exact expected variants only.
old="(e.type==='external'&&k!=='clip'&&k!=='entrance'&&['exit'].includes(k))"
if old in s:
    replace(old,"false")
else:
    old="(e.type==='external'&&k!=='clip'&&k!=='entrance')"
    if old in s: replace(old,"false")
    else:
        old="(e.type==='external'&&['exit'].includes(k))"
        replace(old,"false")
old="(e.type==='external'&&k!=='clip'&&k!=='entrance')"
if old in s: replace(old,"false")
p.write_text(s)
k=root/"app/src/main/java/ro/dj88bid/car/BidThemeWidgets.kt"
s=k.read_text()
replace("    private var foreground=false","""    private val exitViews=mutableSetOf<android.widget.ImageView>()
    private var foreground=false
    private fun clearExitViews(){
        for(v in exitViews.toList()){
            v.animate().cancel()
            root.removeView(v)
            v.setImageDrawable(null)
        }
        exitViews.clear()
    }
    @JavascriptInterface fun cancelExits()=activity.runOnUiThread{clearExitViews()}
    @JavascriptInterface fun animateExit(raw:String)=activity.runOnUiThread{
        if(web.url!=trusted||!foreground||raw.length>2200)return@runOnUiThread
        clearExitViews()
        var budget=1000000
        try{
            val keys=JSONArray(raw)
            for(i in 0 until minOf(keys.length(),16)){
                val key=keys.getString(i)
                if(!validKey(key))continue
                val slot=slots[key]?:continue
                val w=slot.width;val h=slot.height
                if(slot.visibility!=View.VISIBLE||w<1||h<1||w.toLong()*h>budget||slot.alpha<=0f)continue
                val bitmap=android.graphics.Bitmap.createBitmap(w,h,android.graphics.Bitmap.Config.ARGB_8888)
                try{slot.draw(android.graphics.Canvas(bitmap))}catch(_:Exception){bitmap.recycle();continue}
                budget-=w*h
                val ghost=android.widget.ImageView(activity).apply{
                    setImageBitmap(bitmap)
                    isClickable=false;isFocusable=false;isLongClickable=false
                    importantForAccessibility=View.IMPORTANT_FOR_ACCESSIBILITY_NO
                    alpha=slot.alpha
                    scaleType=android.widget.ImageView.ScaleType.FIT_XY
                }
                root.addView(ghost,FrameLayout.LayoutParams(w,h).apply{leftMargin=slot.left;topMargin=slot.top})
                exitViews.add(ghost)
                ghost.animate().alpha(0f).setDuration(180).withEndAction{
                    exitViews.remove(ghost);root.removeView(ghost);ghost.setImageDrawable(null)
                }.start()
            }
        }catch(_:Exception){clearExitViews()}
    }""")
replace("fun stop(){foreground=false;","fun stop(){foreground=false;clearExitViews();")
replace('if(web.url!=trusted||!foreground||raw.length>24000){slots.values','if(web.url!=trusted||!foreground||raw.length>24000){clearExitViews();slots.values')
k.write_text(s)
