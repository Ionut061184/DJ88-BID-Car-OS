"""Advertise OEM HOME categories only on the existing opt-in HOME alias."""
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

p = Path(sys.argv[1]) / "app/src/main/AndroidManifest.xml"
ns = "http://schemas.android.com/apk/res/android"
key = "{" + ns + "}name"
ET.register_namespace("android", ns)
tree = ET.parse(p)
root = tree.getroot()
filters = [f for f in root.findall("./application/activity-alias/intent-filter")
           if any(c.get(key) == "android.intent.category.HOME" for c in f.findall("category"))]
assert len(filters) == 1, "Expected exactly one opt-in HOME alias"
f = filters[0]
for name in ("com.qf.intent.category.1280_720", "com.qf.intent.category.1280_650"):
    if not any(c.get(key) == name for c in f.findall("category")):
        ET.SubElement(f, "category", {key: name})
tree.write(p, encoding="utf-8", xml_declaration=True)
print("OEM HOME categories added; existing alias enablement unchanged.")
