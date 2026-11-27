from pathlib import Path
import sys
p=Path(sys.argv[1])/"app/src/main/assets/bid_theme_builder.js"
s=p.read_text()
a="function mountFolders(t){"
assert s.count(a)==1
s=s.replace(a,"""function folderTarget57(current,original,id,group){if(!current||current.id!==original.id||current.pageId!==original.pageId)return null;return current.elements.find(v=>v.id===id&&v.group===group&&v.groupMode==='folder'&&v.type==='button')||null;}
function mountFolders(t){""",1)
a="folder.onclick=()=>{if(moving()){"
assert s.count(a)==1
s=s.replace(a,"folder.onclick=()=>{if(moving()||panel.dataset.available!=='true'||document.hidden||edit){",1)
a="modal.remove();perform(e);};b.onkeydown=ev=>{if(ev.key==='Enter'||ev.key===' '){ev.preventDefault();if(widgetGesture64(e)==='none')return;modal.remove();perform(e);}};"
b="""runFolderAction();};b.onkeydown=ev=>{if(ev.key==='Enter'||ev.key===' '){ev.preventDefault();if(widgetGesture64(e)==='none')return;b.onclick(ev);}};"""
assert s.count(a)==1
s=s.replace(a,b,1)
a="if(widgetGesture64(e)!=='none'){let last=0;b.onclick=ev=>"
b="""if(widgetGesture64(e)!=='none'){let last=0;const runFolderAction=()=>{const target=folderTarget57(active(),t,e.id,anchor.group);modal.remove();if(!target||moving()||panel.dataset.available!=='true'||document.hidden||edit||globalLock66||widgetGesture64(target)==='none')return;perform(target);};b.onclick=ev=>"""
assert s.count(a)==1
s=s.replace(a,b,1)
p.write_text(s)
t=Path(sys.argv[1])/"tests/editor10022/test_folder_target.js"
t.write_text("""const fs=require('fs'),vm=require('vm'),a=require('assert');
const s=fs.readFileSync(__dirname+'/bid_theme_builder.js','utf8');
const i=s.indexOf('function folderTarget57(');a.ok(i>=0);
const c={};vm.createContext(c);vm.runInContext(s.slice(i,s.indexOf('\\n',i)),c);
const f=c.folderTarget57,e={id:'e1',group:'g1',groupMode:'folder',type:'button'},t={id:'t1',pageId:'p1',elements:[e]};
a.equal(f(t,t,'e1','g1'),e);a.equal(f({...t,pageId:'p2'},t,'e1','g1'),null);
a.equal(f({...t,id:'t2'},t,'e1','g1'),null);a.equal(f(t,t,'e2','g1'),null);
a.equal(f(t,t,'e1','g2'),null);a.equal(f({...t,elements:[{...e,groupMode:'normal'}]},t,'e1','g1'),null);
console.log('6 folder target checks passed');
""")
