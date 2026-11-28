from pathlib import Path
import sys
root=Path(sys.argv[1])
p=root/"app/src/main/assets/bid_theme_builder.js"
s=p.read_text()
def replace(a,b):
 global s
 assert s.count(a)==1,a[:100]
 s=s.replace(a,b,1)
replace("function active(){return pageView(state.applied,livePageId);}", """let portraitLive=false;
function portraitLiveTheme(t,enabled){return t&&enabled?{...t,elements:t.elements.map(e=>({...e,...portraitRect(e)}))}:t;}
function active(){return portraitLiveTheme(pageView(state.applied,livePageId),portraitLive);}
function setPortraitLive(enabled){
 portraitLive=!!enabled&&!!state.applied;
 stage.classList.toggle('bidPortraitLive',portraitLive);
 if(typeof fit==='function')fit();
}
""")
replace("function renderLive(){if(liveThemeId", "function renderLive(){if(!state.applied||edit)setPortraitLive(false);if(liveThemeId")
replace("mountLock66(bar);","const portraitSwitch=document.createElement('button');portraitSwitch.textContent=portraitLive?'Orizontal':'Vertical';portraitSwitch.onclick=()=>{if(globalLock66||moving()||panel.dataset.available!=='true')return;setPortraitLive(!portraitLive);renderLive();};if(!globalLock66)bar.append(portraitSwitch);mountLock66(bar);")
replace("function openFrom(source){if(!lockGuard66())return;", "function openFrom(source){if(!lockGuard66())return;")
# Restore the normal editor canvas before opening it.
replace("edit=true;shell.classList.add('on');","setPortraitLive(false);edit=true;shell.classList.add('on');")
replace("function activateMaster(){if(!lockGuard66())return;","function activateMaster(){if(!lockGuard66())return;")
p.write_text(s)
r=root/"app/src/main/assets/bid_runtime.js"
s=r.read_text()
a="const s=Math.min(innerWidth/1280,innerHeight/720);el.style.transform='scale('+s+')';el.style.left=((innerWidth-1280*s)/2)+'px';el.style.top=((innerHeight-720*s)/2)+'px'"
b="const portrait=el.classList.contains('bidPortraitLive'),w=portrait?720:1280,h=portrait?1280:720;const s=Math.min(innerWidth/w,innerHeight/h);el.style.transform='scale('+s+')';el.style.left=((innerWidth-w*s)/2)+'px';el.style.top=((innerHeight-h*s)/2)+'px'"
assert s.count(a)==1
r.write_text(s.replace(a,b,1))
css=root/"app/src/main/assets/bid_theme_builder.css"
with css.open("a") as out:
 out.write("\n#stage.bidPortraitLive{width:720px;height:1280px;background:#090609;}#stage.bidPortraitLive > :not(#bfLive){visibility:hidden;}#stage.bidPortraitLive .bfHomeBar{overflow-x:auto;white-space:nowrap;}#stage.bidPortraitLive .bfHomeBar > *{flex-shrink:0;}\n")
(root/"tests/editor10022/test_portrait_live.js").write_text("""const fs=require('fs'),vm=require('vm'),a=require('assert');const s=fs.readFileSync(__dirname+'/bid_theme_builder.js','utf8');const i=s.indexOf('function portraitLiveTheme(');a.ok(i>=0);const c={portraitRect:e=>({x:20,y:60,w:100,h:200})};vm.createContext(c);vm.runInContext(s.slice(i,s.indexOf('\\n',i)),c);const f=c.portraitLiveTheme,t={id:'a',elements:[{id:'e',x:10,y:40,w:50,h:60,action:'radio'}]};a.equal(f(t,false),t);a.equal(f(null,true),null);const r=f(t,true);a.equal(r.elements[0].x,20);a.equal(r.elements[0].h,200);a.equal(r.elements[0].action,'radio');a.equal(t.elements[0].x,10);console.log('6 live portrait geometry checks passed');
""")
