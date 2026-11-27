from pathlib import Path
import hashlib, json, sys
root=Path(sys.argv[1])
catalog=Path("theme-catalog")
index=catalog/"index.json"
doc=json.loads(index.read_text())
assert doc["format"]=="BID-theme-catalog" and doc["version"]==1
seen=set()
for entry in doc["themes"]:
    id=entry["id"]
    assert id in ("bordeaux","graphite") and id not in seen
    seen.add(id)
    p=catalog/"themes"/(id+".json")
    raw=p.read_bytes()
    theme=json.loads(raw)
    assert theme["format"]=="BID-full-theme" and theme["version"]==1
    assert theme["theme"]["name"]==entry["name"]
    assert len(raw)<=4000000
    assert entry["bytes"]==len(raw), "Incorrect theme size: "+id
    assert entry["sha256"]==hashlib.sha256(raw).hexdigest(), "Incorrect theme digest: "+id
print("Catalog integrity verified:", len(seen), "themes")
p=root/"app/src/main/java/ro/dj88bid/car/BidOnlineCatalog.kt"
s=p.read_text()
old="/DJ88-BID-Car-OS/main/theme-catalog/"
new="/DJ88-BID-Car-OS/feature/bid-10022-integration/theme-catalog/"
assert s.count(old)==1, "Catalog URL mismatch"
p.write_text(s.replace(old,new,1))
