from pathlib import Path
import sys
root=Path(sys.argv[1])
p=root/"app/src/main/assets/bid_theme_builder.js"
s=p.read_text()
old="preview.textContent=e.name;preview.setAttribute('aria-label','Mostră de culori, nu captură a temei');"
new="""const canvas=document.createElement('canvas');canvas.width=320;canvas.height=180;canvas.style.cssText='width:100%;height:100%;display:block';canvas.setAttribute('aria-label','Previzualizare schematică a temei');const ctx=canvas.getContext('2d');if(ctx){ctx.fillStyle=e.preview.bg;ctx.fillRect(0,0,320,180);ctx.fillStyle=e.preview.fg;ctx.textAlign='center';ctx.font='22px sans-serif';ctx.fillText(e.name,160,40,300);ctx.font='12px sans-serif';ctx.fillText('Descarcă pentru previzualizarea completă',160,155,300);}preview.append(canvas);preview.setAttribute('aria-label','Previzualizare schematică, nu captură completă a temei');"""
assert s.count(old)==1,"Catalog preview anchor missing"
s=s.replace(old,new,1)
p.write_text(s)
