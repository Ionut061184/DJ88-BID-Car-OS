from pathlib import Path
import sys
p=Path(sys.argv[1])/"app/src/main/java/ro/dj88bid/car/BidThemeWidgets.kt"
s=p.read_text()
def replace(a,b):
 global s
 assert s.count(a)==1,a
 s=s.replace(a,b,1)
replace('if(vw<=0||vh<=0||root.width<=0||root.height<=0)throw IllegalArgumentException()','if(!vw.isFinite()||!vh.isFinite()||vw<1||vh<1||root.width<=0||root.height<=0)throw IllegalArgumentException()')
replace('if(!validKey(k)||!binding(k,provider))continue','if(k in visible||!validKey(k)||!binding(k,provider))continue')
replace('val signature=rect.joinToString(",")','val signature=rect.joinToString(",")+":"+activity.resources.displayMetrics.densityDpi+":"+p.minWidth+":"+p.minHeight')
replace('val targetAlpha=e.optDouble("alpha",1.0).coerceIn(0.0,1.0).toFloat()','val rawAlpha=e.optDouble("alpha",1.0)\n                val targetAlpha=if(rawAlpha.isFinite())rawAlpha.coerceIn(0.0,1.0).toFloat() else 1f')
replace('}catch(_:Exception){}\n        for(k in slots.keys.toList())if(k !in visible)removeSlot(k)','}catch(_:Exception){visible.clear();clearExitViews()}\n        for(k in slots.keys.toList())if(k !in visible)removeSlot(k)')
p.write_text(s)
