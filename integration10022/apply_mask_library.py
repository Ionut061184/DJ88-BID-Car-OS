from pathlib import Path
import sys
p=Path(sys.argv[1])/"app/src/main/assets/bid_theme_builder.js"
s=p.read_text()
old="chamfer:'polygon(10% 0,90% 0,100% 15%,100% 85%,90% 100%,10% 100%,0 85%,0 15%)'"
assert s.count(old)==1
s=s.replace(old,old+",octagon:'polygon(29% 0,71% 0,100% 29%,100% 71%,71% 100%,29% 100%,0 71%,0 29%)',shield:'polygon(0 0,100% 0,100% 65%,50% 100%,0 65%)',trapezoid:'polygon(15% 0,85% 0,100% 100%,0 100%)',rounded:'inset(0 round 18%)',ticket:'polygon(0 0,100% 0,100% 35%,90% 50%,100% 65%,100% 100%,0 100%,0 65%,10% 50%,0 35%)'",1)
old='<option value="chamfer">Colțuri teșite</option>'
assert s.count(old)==1
s=s.replace(old,old+'<option value="octagon">Octogon</option><option value="shield">Scut</option><option value="trapezoid">Trapez</option><option value="rounded">Colțuri rotunjite</option><option value="ticket">Decupaje laterale</option>',1)
p.write_text(s)
