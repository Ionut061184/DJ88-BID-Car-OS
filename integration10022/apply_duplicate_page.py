from pathlib import Path
import sys
root=Path(sys.argv[1])
p=root/"app/src/main/assets/bid_theme_builder.js"
s=p.read_text()
a="function pageAllowed(){"
assert s.count(a)==1
s=s.replace(a,"""function duplicatePagePayload(source,newId){
 const groups=new Map();
 return pagePayload({...copy(source),pageId:newId('p'),pageName:(source.pageName.slice(0,32)+' copie').slice(0,40),elements:source.elements.map(e=>{
 const v=copy(e);v.id=newId('e');if(v.group){if(!groups.has(v.group))groups.set(v.group,newId('g'));v.group=groups.get(v.group);}return v;
 })});
}
const duplicatePageButton=document.createElement('button');duplicatePageButton.type='button';duplicatePageButton.textContent='Duplică ecranul';$('bfPageAdd').after(duplicatePageButton);
duplicatePageButton.onclick=()=>{if(!pageAllowed()||!draft||draft.pageOrder.length>=MAX_PAGES)return;const other=duplicatePagePayload(draft,uid);checkpoint();draft.otherPages.push(other);draft.pageOrder.push(other.pageId);draft=pageView(draft,other.pageId);selected=null;render();message('Ecran duplicat. Widgeturile Android necesită asociere separată.');};
function pageAllowed(){""",1)
a="$('bfPageAdd').disabled=order.length>=MAX_PAGES;"
assert s.count(a)==1
s=s.replace(a,a+"duplicatePageButton.disabled=order.length>=MAX_PAGES;",1)
p.write_text(s)
(root/"tests/editor10022/test_duplicate_page.js").write_text("""const fs=require('fs'),vm=require('vm'),a=require('assert');
const s=fs.readFileSync(__dirname+'/bid_theme_builder.js','utf8');
const i=s.indexOf('function duplicatePagePayload('),j=s.indexOf('const duplicatePageButton=',i);
a.ok(i>=0&&j>i);
const c={copy:v=>JSON.parse(JSON.stringify(v)),pagePayload:v=>v};vm.createContext(c);vm.runInContext(s.slice(i,j),c);
let n=0;const original={pageId:'p1',pageName:'Ecran 1',background:'#123456',elements:[{id:'e1',group:'g1',locked:true,x:10},{id:'e2',group:'g1',x:20},{id:'e3',group:'',type:'external'}]};
const r=c.duplicatePagePayload(original,p=>p+(++n+10));
a.notEqual(r.pageId,original.pageId);a.notEqual(r.elements[0].id,'e1');a.equal(new Set(r.elements.map(e=>e.id)).size,3);
a.equal(r.elements[0].group,r.elements[1].group);a.notEqual(r.elements[0].group,'g1');a.equal(r.elements[2].group,'');
a.equal(r.elements[0].locked,true);a.equal(r.background,original.background);r.elements[0].x=100;a.equal(original.elements[0].x,10);
console.log('9 page duplication checks passed');
""")
