from pathlib import Path
import sys
root=Path(sys.argv[1])
p=root/"app/src/main/assets/bid_theme_builder.js"
s=p.read_text()
a="const current=active();const target=current?.id===t.id&&current?.pageId===t.pageId?current.elements.find(v=>v.id===e.id):null;"
assert s.count(a)==1
s=s.replace(a,"const target=resolveNativeAction64(active(),t,e.id);",1)
a="function mountNativeActions64(bar,t){"
assert s.count(a)==1
s=s.replace(a,"function resolveNativeAction64(current,original,id){if(!current||!original||current.id!==original.id||current.pageId!==original.pageId)return null;return current.elements.find(v=>v.id===id)||null;}\n"+a,1)
p.write_text(s)
(root/"tests/editor10022/test_native_action_target.js").write_text("""const fs=require('fs'),vm=require('vm'),a=require('assert');
const s=fs.readFileSync(__dirname+'/bid_theme_builder.js','utf8');
const start=s.indexOf('function resolveNativeAction64(');
a.ok(start>=0);
const c={};vm.createContext(c);vm.runInContext(s.slice(start,s.indexOf('\\n',start)),c);
const f=c.resolveNativeAction64;
const old={id:'a',pageId:'p',elements:[{id:'w',action:'radio'}]};
const updated={...old,elements:[{id:'w',action:'music'}]};
a.equal(f(updated,old,'w').action,'music');
a.equal(f({...updated,id:'b'},old,'w'),null);
a.equal(f({...updated,pageId:'q'},old,'w'),null);
a.equal(f({...updated,elements:[]},old,'w'),null);
a.equal(f(null,old,'w'),null);
a.equal(f(updated,null,'w'),null);
console.log('6 native action target checks passed');
""")
