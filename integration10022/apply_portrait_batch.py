from pathlib import Path
import sys
root=Path(sys.argv[1])
p=root/"app/src/main/assets/bid_theme_builder.js"
s=p.read_text()
def replace(a,b):
 global s
 assert s.count(a)==1,a[:100]
 s=s.replace(a,b,1)
replace("function portraitRect(v){","""function portraitBatch(elements,mode){
 return elements.map(e=>{
 if(e.locked||e.group)return e;
 const next={...e};
 if(mode==='reset')delete next.portrait;
 else if(!next.portrait)next.portrait=portraitRect(next);
 return next;
 });
}
function portraitRect(v){""")
replace("const dialog=document.createElement('div');\n Object.assign(dialog.style,{position:'absolute',inset:'48px 0 0'","const existing=shell.querySelector('[data-bid-portrait-dialog]');if(existing)return;const dialog=document.createElement('div');dialog.dataset.bidPortraitDialog='true';\n Object.assign(dialog.style,{position:'absolute',inset:'48px 0 0'")
replace("controls.append(save,reset);const chosen=", """const initialize=document.createElement('button');initialize.textContent='Inițializează pozițiile verticale';const resetAll=document.createElement('button');resetAll.textContent='Resetează pozițiile verticale';controls.append(save,reset,initialize,resetAll);const applyBatch=mode=>{if(!allowed()||!dialog.isConnected||draft?.id!==originalTheme||draft?.pageId!==originalPage)return;if(!confirm(mode==='reset'?'Resetezi pozițiile verticale ale elementelor neblocate și negrupate?':'Inițializezi pozițiile verticale lipsă, fără să schimbi cele existente?'))return;checkpoint();draft.elements=portraitBatch(draft.elements,mode);fields();draw();};initialize.onclick=()=>applyBatch('init');resetAll.onclick=()=>applyBatch('reset');const chosen=""")
replace("const chosen=()=>draft?.elements.find(e=>e.id===pick.value);","const chosen=()=>draft?.id===originalTheme&&draft?.pageId===originalPage?draft.elements.find(e=>e.id===pick.value):null;")
# Declare dialog identity before first invocation of fields().
replace("const originalPage=draft.pageId,originalTheme=draft.id;const timer=setInterval","const timer=setInterval")
replace("dialog.dataset.bidPortraitDialog='true';","dialog.dataset.bidPortraitDialog='true';const originalPage=draft.pageId,originalTheme=draft.id;")
p.write_text(s)
(root/"tests/editor10022/test_portrait_batch.js").write_text("""const fs=require('fs'),vm=require('vm'),a=require('assert');const s=fs.readFileSync(__dirname+'/bid_theme_builder.js','utf8');const i=s.indexOf('function portraitBatch('),j=s.indexOf('function element(',i);a.ok(i>=0&&j>i);const c={};vm.createContext(c);vm.runInContext(s.slice(i,j),c);const e={id:'a',x:128,y:72,w:256,h:144},custom={...e,id:'b',portrait:{x:12,y:60,w:100,h:100}},locked={...custom,id:'c',locked:true},group={...custom,id:'d',group:'g'};const r=c.portraitBatch([e,custom,locked,group],'init');a.equal(r[0].portrait.x,72);a.equal(e.portrait,undefined);a.equal(r[1].portrait.x,12);a.equal(r[2],locked);a.equal(r[3],group);const z=c.portraitBatch(r,'reset');a.equal(z[0].portrait,undefined);a.equal(z[1].portrait,undefined);a.equal(z[2].portrait.x,12);a.equal(z[3].portrait.x,12);a.equal(z[0].x,128);console.log('10 portrait batch checks passed');
""")
