from pathlib import Path
import sys
root=Path(sys.argv[1])
p=root/"app/src/main/assets/bid_general.js"
s=p.read_text()
s+="""
(function(){
'use strict';
let previous=null;
function notifyEditorVisibility(){
 const editor=document.querySelector('#bfShell');
 if(!editor)return;
 const visible=editor.classList.contains('on');
 if(previous===null){previous=visible;return;}
 if(previous===visible)return;
 previous=visible;
 try{window.BID.emitTaskerEvent(visible?'editor_open':'editor_closed');}catch(_){}
}
const observer=new MutationObserver(notifyEditorVisibility);
function bind(){
 const editor=document.querySelector('#bfShell');
 if(!editor)return false;
 observer.observe(editor,{attributes:true,attributeFilter:['class','style','hidden','aria-hidden']});
 notifyEditorVisibility();
 return true;
}
if(!bind()){
 const boot=new MutationObserver(()=>{if(bind())boot.disconnect();});
 boot.observe(document.body,{childList:true,subtree:true});
}
})();
"""
# Refuse to integrate against an editor without the required actual DOM anchor.
html=(root/"app/src/main/assets/index.html").read_text()
builder=(root/"app/src/main/assets/bid_theme_builder.js").read_text()
assert 'bfShell' in html or 'bfShell' in builder, "Editor visibility anchor missing"
p.write_text(s)
