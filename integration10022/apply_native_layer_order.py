from pathlib import Path
import sys
p=Path(sys.argv[1])/"app/src/main/java/ro/dj88bid/car/BidThemeWidgets.kt"
s=p.read_text()
a="for(k in slots.keys.toList())if(k !in visible)removeSlot(k)"
assert s.count(a)==1
s=s.replace(a,a+"""
        // The payload follows the theme element order. Reorder only hosted
        // widgets, leaving MASTER and all other native views in place.
        val ordered=visible.mapNotNull{slots[it]}
        val indices=ordered.map{root.indexOfChild(it)}.filter{it>=0}.sorted()
        if(indices.size==ordered.size && indices.map{root.getChildAt(it)}!=ordered){
            for(v in ordered)root.removeView(v)
            for((i,v) in ordered.withIndex())root.addView(v,indices[i])
        }
""",1)
p.write_text(s)
