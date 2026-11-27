from pathlib import Path
import sys
root=Path(sys.argv[1])
p=root/"app/src/main/assets/bid_theme_builder.js"
s=p.read_text()
def replace(a,b):
 global s
 assert s.count(a)==1, a[:100]
 s=s.replace(a,b,1)
replace("function element(v){", """function portraitRect(v){
 const r=v.portrait||{},n=(x,d,a,b)=>Math.max(a,Math.min(b,Math.round(Number.isFinite(x)?x:d)));
 const w=n(r.w,v.w*720/1280,48,720),h=n(r.h,v.h*1280/720,30,1232);
 return {x:n(r.x,v.x*720/1280,0,720-w),y:n(r.y,v.y*1280/720,48,1280-h),w,h};
}
function element(v){""")
replace("return {...advancedFields(v),hideInnerLabel:", "return {...advancedFields(v),...(v.portrait&&typeof v.portrait==='object'?{portrait:portraitRect({...v,w,h})}:{}),hideInnerLabel:")
replace("portraitButton.textContent='Schiță verticală 9:16'","portraitButton.textContent='Profil vertical 9:16'")
replace("caption.textContent='Schiță verticală independentă – fără comenzi active'","caption.textContent='Profil vertical independent – previzualizare fără comenzi active'")
replace("ctx.fillStyle=draft.background;ctx.fillRect(0,0,720,1280);","const controls=document.createElement('div');controls.style.cssText='display:flex;flex-wrap:wrap;gap:6px;align-items:center';const pick=document.createElement('select');for(const e of draft.elements)pick.append(new Option(e.label||types[e.type],e.id));controls.append(pick);const inputs={};for(const k of ['x','y','w','h']){const l=document.createElement('label');l.textContent=k.toUpperCase();const i=document.createElement('input');i.type='number';i.style.width='65px';i.step='1';l.append(i);controls.append(l);inputs[k]=i;}const save=document.createElement('button');save.textContent='Aplică poziția verticală';const reset=document.createElement('button');reset.textContent='Resetare verticală';controls.append(save,reset);const chosen=()=>draft?.elements.find(e=>e.id===pick.value);function fields(){const e=chosen();const blocked=!e||e.locked||!!e.group;for(const k of Object.keys(inputs)){inputs[k].disabled=blocked;inputs[k].value=e?portraitRect(e)[k]:'';}save.disabled=reset.disabled=blocked;}function draw(){ctx.clearRect(0,0,720,1280);ctx.fillStyle=draft.background;ctx.fillRect(0,0,720,1280);")
replace("const x=e.x*720/W,y=e.y*1280/H,w=e.w*720/W,h=e.h*1280/H;","const {x,y,w,h}=portraitRect(e);")
replace("dialog.append(close,caption,surface);shell.append(dialog);","}pick.onchange=fields;save.onclick=()=>{if(!allowed()||!dialog.isConnected)return;const e=chosen();if(!e||e.locked||e.group)return;const r=Object.fromEntries(Object.entries(inputs).map(([k,i])=>[k,i.valueAsNumber]));if(Object.values(r).some(v=>!Number.isFinite(v)))return;checkpoint();e.portrait=portraitRect({...e,portrait:r});fields();draw();};reset.onclick=()=>{if(!allowed())return;const e=chosen();if(!e||e.locked||e.group)return;checkpoint();delete e.portrait;fields();draw();};dialog.append(close,caption,controls,surface);shell.append(dialog);fields();draw();")
replace("const timer=setInterval(()=>{if(!dialog.isConnected)","const originalPage=draft.pageId,originalTheme=draft.id;const timer=setInterval(()=>{if(!dialog.isConnected)")
replace("if(!allowed()){dialog.remove();clearInterval(timer);}},250);","if(!allowed()||draft?.pageId!==originalPage||draft?.id!==originalTheme){dialog.remove();clearInterval(timer);}},250);")
p.write_text(s)
(root/"tests/editor10022/test_portrait_profile.js").write_text("""const fs=require('fs'),vm=require('vm'),a=require('assert');const s=fs.readFileSync(__dirname+'/bid_theme_builder.js','utf8');const i=s.indexOf('function portraitRect('),j=s.indexOf('function element(',i);a.ok(i>=0&&j>i);const c={};vm.createContext(c);vm.runInContext(s.slice(i,j),c);const f=c.portraitRect,e={x:128,y:72,w:256,h:144};const r=f(e);a.equal(r.x,72);a.equal(r.y,128);a.equal(r.w,144);a.equal(r.h,256);const q=f({...e,portrait:{x:999,y:-2,w:200,h:300}});a.equal(q.x,520);a.equal(q.y,48);a.equal(q.w,200);a.equal(q.h,300);a.equal(e.x,128);console.log('9 portrait profile checks passed');
""")
