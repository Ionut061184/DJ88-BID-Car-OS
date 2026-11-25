"""Finalize the existing display controller; do not add a competing controller."""
from pathlib import Path
p=Path("app/src/main/assets/bid_adaptive.js")
s=p.read_text()
def replace(a,b):
    global s
    assert s.count(a)==1,a
    s=s.replace(a,b)
replace("const lux=typeof d.lux==='number'", "const lux=d.sensorRegistered!==false&&typeof d.lux==='number'")
replace(" if(effective!==applied){", """ if(stage){
  stage.dataset.bidDisplayEffective=effective;
  stage.dataset.bidDisplaySource=mode!=='auto'?'manual':lux!==null?'sensor':daylight!==null?'weather':'system';
 }
 if(effective!==applied){""")
replace("try{if(window.BID&&typeof BID.setDisplayMode==='function')BID.setDisplayMode(effective);}catch(_){}\n  applied=effective;", "try{if(window.BID&&typeof BID.setDisplayMode==='function')BID.setDisplayMode(effective);applied=effective;}catch(_){applied=null;}")
replace("Mod '+effective+' · '", "Smart Display · '+({sun:'Soare',day:'Zi',night:'Noapte',system:'Sistem'}[effective]||effective)+' · '")
p.write_text(s)
p=Path("app/src/main/assets/bid_system.js")
s=p.read_text()
assert s.count("Update 3 · candidat software")==1
p.write_text(s.replace("Update 3 · candidat software","Update 5 · BID Smart System · candidat software"))
print("Smart Display: actual sensor state, explicit fallback, retry and correct version label.")
