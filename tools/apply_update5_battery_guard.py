"""Extend existing voltage monitor; preserve sampling, limits and artwork."""
from pathlib import Path
p=Path("app/src/main/assets/bid_battery.js")
s=p.read_text()
def replace(old,new):
    global s
    assert s.count(old)==1,old
    s=s.replace(old,new)
replace("const ns='http://www.w3.org/2000/svg';", """const ns='http://www.w3.org/2000/svg';
const guardStyle=document.createElement('style');
guardStyle.textContent='#bidVoltageText[data-bid-guard="low"],#bidVoltageText[data-bid-guard="high"]{color:#ffb9a9!important;background:#451321;border-radius:3px;box-shadow:inset 0 -2px #ffb9a9}';
document.head.appendChild(guardStyle);
function guard(){
 const badge=$('bidVoltageText');
 if(!badge)return;
 const state=last===null?'unavailable':notice||'normal';
 badge.dataset.bidGuard=state;
 badge.title=notice&&last!==null?message(notice)+' Valoare OEM cu vechime neconfirmată.':state==='unavailable'?'Tensiune auto indisponibilă':'Tensiune auto OEM · orientativă';
}""")
replace("function render(){if(box.hidden)return;", "function render(){guard();if(box.hidden)return;")
replace("function clearContinuity(){streak=null;notice=null;lastTime=null;last=null;}", "function clearContinuity(){streak=null;notice=null;lastTime=null;last=null;guard();}")
replace("BID Battery · 12 V</h1>", "BID Battery Guard · 12 V</h1>")
p.write_text(s)
print("Battery Guard: persistent warning within the existing voltage indicator; no permissions or background monitoring.")
