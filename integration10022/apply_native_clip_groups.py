from pathlib import Path
import sys
root=Path(sys.argv[1])
p=root/"app/src/main/assets/bid_theme_builder.js"
s=p.read_text()
def replace(old,new):
    global s
    assert s.count(old)==1, "Missing or ambiguous anchor: "+old[:100]
    s=s.replace(old,new,1)
replace("function groupMembers(e){", """function groupCanChange(members){return Array.isArray(members)&&members.length>0&&members.every(v=>v&&!v.locked);}
function groupMembers(e){""")
replace("$('bfGroupSplit').disabled=members.length<1;", "$('bfGroupSplit').disabled=!groupCanChange(members);")
replace("if(!members.length)return;checkpoint();members.forEach(v=>{v.group='';v.groupMode='normal';});", "if(!groupCanChange(members))return;checkpoint();members.forEach(v=>{v.group='';v.groupMode='normal';});")
# A delete that would implicitly change the last locked peer's group is refused.
replace("checkpoint();const [e]=draft.elements.splice(i,1);", "if(dir===0&&draft.elements[i].group){const peers=draft.elements.filter(v=>v.group===draft.elements[i].group);if(peers.length===2&&!groupCanChange(peers))return;}checkpoint();const [e]=draft.elements.splice(i,1);")
# Allow native rounded clipping, not arbitrary polygon masks or native animations.
replace("n.disabled=!e||e.locked||(e.type==='external'", "n.disabled=!e||e.locked||(e.type==='external'&&k!=='clip'")
replace("if(!e||e.locked||e.type==='external'||(['googleMap','osm'].includes(e.type)&&k==='exit'))return;", "if(!e||e.locked||(e.type==='external'&&k!=='clip')||(['googleMap','osm'].includes(e.type)&&k==='exit'))return;")
replace("items.push({key:externalKey(t,e),provider:e.provider,x:r.x,y:r.y,w:r.width,h:r.height,alpha:e.alpha/100});", "items.push({key:externalKey(t,e),provider:e.provider,x:r.x,y:r.y,w:r.width,h:r.height,alpha:e.alpha/100,clip:e.clip===true,shape:e.shape,radius:e.radius});")
p.write_text(s)
k=root/"app/src/main/java/ro/dj88bid/car/BidThemeWidgets.kt"
s=k.read_text()
replace("slot.alpha=e.optDouble", """val clip = e.optBoolean("clip",false)
                val shape = e.optString("shape","rounded")
                val radius = when(shape) {
                    "square" -> 0f
                    "circle","pill" -> minOf(rect[2],rect[3])/2f
                    else -> (e.optDouble("radius",10.0).takeIf{it.isFinite()} ?: 10.0).coerceIn(0.0,60.0).toFloat() * root.width / vw.toFloat()
                }.coerceIn(0f,minOf(rect[2],rect[3])/2f)
                val clipTag = "$clip:$radius"
                if(slot.tag != clipTag){
                    slot.tag=clipTag
                    slot.outlineProvider=object:android.view.ViewOutlineProvider(){
                        override fun getOutline(v:View,o:android.graphics.Outline){
                            if(v.width>0&&v.height>0)o.setRoundRect(0,0,v.width,v.height,radius)
                        }
                    }
                    slot.clipToOutline=clip
                    slot.invalidateOutline()
                }
                slot.alpha=e.optDouble""")
k.write_text(s)
