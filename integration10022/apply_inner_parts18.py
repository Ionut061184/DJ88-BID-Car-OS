from pathlib import Path
import sys
p=Path(sys.argv[1])/"app/src/main/assets/bid_theme_builder.js"
s=p.read_text()
def replace(a,b):
 global s
 assert s.count(a)==1,a[:100]
 s=s.replace(a,b,1)
replace("return {...advancedFields(v),id:v.id,type:v.type", "return {...advancedFields(v),hideInnerLabel:v.hideInnerLabel===true,hideInnerGraphic:v.hideInnerGraphic===true,id:v.id,type:v.type")
replace("if(bidMaskSupported(e)){for(const child of n.children)", "if(bidMaskSupported(e)){if(e.hideInnerLabel)label.hidden=true;if(e.hideInnerGraphic)for(const child of n.querySelectorAll('.bfGlyph,.bfAutoArt,[data-bid-gauge]'))child.hidden=true;for(const child of n.children)")
replace("function refreshPrecision(){", """function innerEditable18(e,k,supported){return !!e&&!e.locked&&supported===true&&['hideInnerLabel','hideInnerGraphic'].includes(k);}
function toggleInner18(k){
 if(!allowed()||!draft)return;
 const e=draft.elements.find(v=>v.id===selected);
 if(!innerEditable18(e,k,!!e&&bidMaskSupported(e)))return;
 checkpoint();e[k]=!e[k];render();
}
const inner18=document.createElement('div');const innerButtons18={};
for(const [k,title] of [['hideInnerLabel','Ascunde/arată textul interior'],['hideInnerGraphic','Ascunde/arată grafica interioară']]){
 const b=document.createElement('button');b.textContent=title;b.type='button';b.onclick=()=>toggleInner18(k);inner18.append(b);innerButtons18[k]=b;
}
$('bfControls').append(inner18);
function refreshInner18(){const e=draft?.elements.find(v=>v.id===selected);for(const [k,b] of Object.entries(innerButtons18)){b.disabled=!innerEditable18(e,k,!!e&&bidMaskSupported(e));b.setAttribute('aria-pressed',String(!!e?.[k]));}}\nfunction refreshPrecision(){refreshInner18();""")
p.write_text(s)

t=Path(sys.argv[1])/"tests/editor10022/test_inner_visibility.js"
t.write_text("""const fs=require('fs'),vm=require('vm'),a=require('assert');
const s=fs.readFileSync(__dirname+'/bid_theme_builder.js','utf8');const i=s.indexOf('function innerEditable18(');a.ok(i>=0);const c={};vm.createContext(c);vm.runInContext(s.slice(i,s.indexOf('\\n',i)),c);const f=c.innerEditable18;
a.equal(f({},'hideInnerLabel',true),true);a.equal(f({},'hideInnerGraphic',true),true);a.equal(f({locked:true},'hideInnerLabel',true),false);a.equal(f(null,'hideInnerLabel',true),false);a.equal(f({},'hideInnerGraphic',false),false);a.equal(f({},'id',true),false);console.log('6 inner visibility permission checks passed');
""")
