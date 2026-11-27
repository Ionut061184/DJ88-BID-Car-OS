from pathlib import Path
import sys
p=Path(sys.argv[1])/"app/src/main/assets/bid_theme_builder.js"
s=p.read_text()
a="item.onclick=()=>{if(moving()||panel.dataset.available!=='true'){modal.remove();return;}modal.remove();perform(e);};"
b="item.onclick=()=>{const current=active();const target=current?.id===t.id&&current?.pageId===t.pageId?current.elements.find(v=>v.id===e.id):null;if(moving()||panel.dataset.available!=='true'||document.hidden||edit||globalLock66||!target||!nativeAction64(target)){modal.remove();return;}modal.remove();perform(target);};"
assert s.count(a)==1
s=s.replace(a,b)
a="function mountNativeActions64(bar,t){const entries=t.elements.filter(nativeAction64);"
b="function mountNativeActions64(bar,t){if(globalLock66)return;const entries=t.elements.filter(nativeAction64);"
assert s.count(a)==1
s=s.replace(a,b)
p.write_text(s)
