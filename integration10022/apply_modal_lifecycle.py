from pathlib import Path
import sys
root=Path(sys.argv[1])
p=root/"app/src/main/assets/bid_theme_builder.js"
s=p.read_text()
a="function update(){if(moving()||reduceMotion||edit||document.hidden||live.hidden)clearExits();"
b="""function modalMustClose(movingNow,available,hidden,editing){return movingNow||available!=='true'||hidden||editing;}
function update(){if(moving()||reduceMotion||edit||document.hidden||live.hidden)clearExits();"""
assert s.count(a)==1
s=s.replace(a,b,1)
a="||edit||document.hidden;for(const [root,t] of [[live,active()],[canvas,draft]])"
b="||edit||document.hidden;if(modalMustClose(moving(),panel.dataset.available,live.hidden||document.hidden,edit))for(const modal of live.querySelectorAll('.bfFolderOverlay'))modal.remove();for(const [root,t] of [[live,active()],[canvas,draft]])"
assert s.count(a)==1
s=s.replace(a,b,1)
p.write_text(s)
(root/"tests/editor10022/test_modal_lifecycle.js").write_text("""const fs=require('fs'),vm=require('vm'),a=require('assert');
const s=fs.readFileSync(__dirname+'/bid_theme_builder.js','utf8');
const i=s.indexOf('function modalMustClose(');a.ok(i>=0);
const c={};vm.createContext(c);vm.runInContext(s.slice(i,s.indexOf('\\n',i)),c);
const f=c.modalMustClose;
a.equal(f(false,'true',false,false),false);
a.equal(f(true,'true',false,false),true);
a.equal(f(false,'false',false,false),true);
a.equal(f(false,undefined,false,false),true);
a.equal(f(false,'true',true,false),true);
a.equal(f(false,'true',false,true),true);
console.log('6 modal lifecycle checks passed');
""")
