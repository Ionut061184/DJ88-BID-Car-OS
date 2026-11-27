from pathlib import Path
import sys
p=Path(sys.argv[1])/"app/src/main/assets/bid_theme_builder.js"
s=p.read_text()
a="ns.some(other=>other!==n&&intersects(r,other.getBoundingClientRect()))"
b="ns.some(other=>other!==n&&!other.classList.contains('bfExternal')&&intersects(r,other.getBoundingClientRect()))"
assert s.count(a)==1,"Native overlap guard changed"
s=s.replace(a,b,1)
p.write_text(s)
