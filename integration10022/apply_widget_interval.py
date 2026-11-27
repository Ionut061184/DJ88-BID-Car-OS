from pathlib import Path
import sys
root=Path(sys.argv[1])
p=root/"app/src/main/assets/bid_theme_builder.js"
s=p.read_text()
a="if(!interval||!n.dataset.bidRefreshAt||now-Number(n.dataset.bidRefreshAt)>=interval)"
b="if(!interval||n.dataset.bidRefreshInterval!==String(interval)||!n.dataset.bidRefreshAt||now-Number(n.dataset.bidRefreshAt)>=interval)"
assert s.count(a)==1
s=s.replace(a,b)
a="n.dataset.bidRefreshAt=String(now);"
assert s.count(a)==1
s=s.replace(a,a+"n.dataset.bidRefreshInterval=String(interval);")
p.write_text(s)
t=root/"tests/editor10022/test_advanced.js"
with t.open("a") as f:
 f.write("\nfor(const type of ['clock','date','weather','battery','wifi','bluetooth','cell']){eq(c.advancedRefresh({type,refreshSeconds:1}),1000);eq(c.advancedRefresh({type,refreshSeconds:60}),60000);}\nconsole.log('14 additional widget interval checks passed');\n")
