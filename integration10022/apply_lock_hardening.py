from pathlib import Path
import sys
root=Path(sys.argv[1])
p=root/"app/src/main/assets/bid_theme_builder.js"
s=p.read_text()
old="if(i<0)return;checkpoint();const [e]=draft.elements.splice(i,1);"
new="if(i<0||draft.elements[i].locked)return;checkpoint();const [e]=draft.elements.splice(i,1);"
assert s.count(old)==1,"Layer/delete guard anchor changed"
s=s.replace(old,new,1)
old="for(const id of ['bfFront','bfBack','bfDelete','bfIconPicker','bfOwnIcon','bfClearIcon'])$(id).disabled=!e;"
new="for(const id of ['bfFront','bfBack','bfDelete','bfIconPicker','bfOwnIcon','bfClearIcon'])$(id).disabled=!e||e.locked;"
assert s.count(old)==1,"Editor controls anchor changed"
s=s.replace(old,new,1)
p.write_text(s)
print("Locked elements: layer/delete controls and handler protected")
