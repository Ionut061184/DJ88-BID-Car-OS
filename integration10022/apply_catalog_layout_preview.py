from pathlib import Path
import hashlib,json,sys
root=Path(sys.argv[1])
catalog=Path("theme-catalog")
entries=json.loads((catalog/"index.json").read_text())["themes"]
layouts={}
for e in entries:
    raw=(catalog/"themes"/(e["id"]+".json")).read_bytes()
    assert len(raw)==e["bytes"] and hashlib.sha256(raw).hexdigest()==e["sha256"]
    t=json.loads(raw)["theme"]
    items=[]
    for v in t["elements"][:80]:
        x,y,w,h=[v[k] for k in ("x","y","w","h")]
        assert all(isinstance(n,(int,float)) for n in (x,y,w,h))
        assert x>=0 and y>=0 and w>0 and h>0 and x+w<=1280 and y+h<=720
        color=v.get("color","#e4d0b6")
        assert isinstance(color,str) and len(color)==7 and color[0]=="#"
        items.append({"x":x,"y":y,"w":w,"h":h,"color":color,"label":str(v.get("label") or {"clock":"12:30","speed":"0 km/h"}.get(v.get("type"),v.get("type","Widget")))[:48],"border":v.get("border")==True})
    layouts[e["id"]]={"sha256":e["sha256"],"revision":e["revision"],"items":items}
p=root/"app/src/main/assets/bid_theme_builder.js"
s=p.read_text()
anchor="function renderOnline(){"
assert s.count(anchor)==1
s=s.replace(anchor,"const bidCatalogLayouts="+json.dumps(layouts,ensure_ascii=True,separators=(",",":"))+";\n"+anchor,1)
old="ctx.textAlign='center';ctx.font='22px sans-serif';ctx.fillText(e.name,160,40,300);ctx.font='12px sans-serif';ctx.fillText('Descarcă pentru previzualizarea completă',160,155,300);"
new="""ctx.textAlign='center';const layout=bidCatalogLayouts[e.id];if(layout&&layout.revision===e.revision&&layout.sha256===e.sha256){for(const v of layout.items){const x=v.x/4,y=v.y/4,w=v.w/4,h=v.h/4;ctx.save();ctx.beginPath();ctx.rect(x,y,w,h);ctx.clip();ctx.fillStyle=v.color;ctx.strokeStyle=v.color;if(v.border)ctx.strokeRect(x+.5,y+.5,Math.max(0,w-1),Math.max(0,h-1));ctx.font=Math.max(7,Math.min(17,h*.45))+'px sans-serif';ctx.textBaseline='middle';ctx.fillText(v.label,x+w/2,y+h/2,Math.max(1,w-4));ctx.restore();}}else{ctx.font='22px sans-serif';ctx.fillText(e.name,160,40,300);ctx.font='12px sans-serif';ctx.fillText('Descarcă pentru previzualizarea completă',160,155,300);}"""
assert s.count(old)==1
s=s.replace(old,new,1)
s=s.replace("Previzualizare schematică, nu captură completă a temei","Miniatură a dispunerii reale; datele dinamice sunt demonstrative")
p.write_text(s)
print("Generated previews using verified theme coordinates:",len(layouts))
