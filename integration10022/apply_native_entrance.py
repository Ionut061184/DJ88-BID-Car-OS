from pathlib import Path
import sys
root=Path(sys.argv[1])
p=root/"app/src/main/assets/bid_theme_builder.js"
s=p.read_text()
old="clip:e.clip===true,shape:e.shape,radius:e.radius"
assert s.count(old)==1
s=s.replace(old,old+",animateEntrance:e.entrance!=='none'&&!reduceMotion&&!moving()&&panel.dataset.available==='true'&&!window.matchMedia?.('(prefers-reduced-motion: reduce)').matches",1)
# Enable only entrance selection for external widgets; exit remains unsupported.
s=s.replace("e.type==='external'&&k!=='clip'","e.type==='external'&&k!=='clip'&&k!=='entrance'")
s=s.replace("['clip','entrance','exit'].includes(k)","['exit'].includes(k)")
p.write_text(s)
p=root/"app/src/main/java/ro/dj88bid/car/BidThemeWidgets.kt"
s=p.read_text()
old="slot.alpha=e.optDouble(\"alpha\",1.0).coerceIn(0.0,1.0).toFloat();slot.visibility=View.VISIBLE;visible.add(k)"
assert s.count(old)==1
s=s.replace(old,'''val targetAlpha=e.optDouble("alpha",1.0).coerceIn(0.0,1.0).toFloat()
                val entering=slot.visibility!=View.VISIBLE || !visible.contains(k) && slot.getTag(android.R.id.custom)==null
                val animate=e.optBoolean("animateEntrance",false)
                slot.setTag(android.R.id.custom,true)
                slot.visibility=View.VISIBLE
                val child=slot.getChildAt(0)
                slot.alpha=targetAlpha
                if(!animate){
                    child.animate().cancel()
                    child.alpha=1f
                }else if(entering){
                    child.animate().cancel()
                    child.alpha=0f
                    child.animate().alpha(1f).setDuration(180).start()
                }
                visible.add(k)''',1)
p.write_text(s)
