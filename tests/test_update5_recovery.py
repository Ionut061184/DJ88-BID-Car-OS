import json
from pathlib import Path
from playwright.sync_api import sync_playwright
assets=Path("app/src/main/assets").resolve()
with sync_playwright() as p:
    browser=p.chromium.launch(headless=True,args=["--no-sandbox"])
    page=browser.new_page(viewport={"width":1280,"height":720})
    page.add_init_script("""window.BID={open:()=>{},settingsPinEnabled:()=>false,settingsPinVerify:()=> 'ok',settingsPinChange:()=> 'ok'}""")
    page.goto((assets/"index.html").as_uri())
    page.locator("#qfSpeedTile").click()
    page.locator("#bidServiceOpen").click()
    page.locator("#bidServiceOdo").fill("378584")
    page.locator("#bidServiceSaveOdo").click()
    page.locator("#bidServiceRows section").first.get_by_role("button",name="Schimb efectuat").click()
    page.evaluate("localStorage.setItem('bid_favorites',JSON.stringify(['waze']));localStorage.setItem('test_private_pin','not-exported');localStorage.setItem('test_gps','not-exported');bidSystemOpen()")
    page.locator("#bidSystemExport").click()
    raw=page.locator("#bidSystemBackup").input_value()
    d=json.loads(raw)
    assert set(d)=={"format","version","preferences","service"} and d["version"]==2
    assert d["service"]["odo"]==378584 and d["service"]["records"][0]["km"]==378584
    assert d["preferences"]["bid_favorites"]==["waze"]
    assert "not-exported" not in raw
    page.evaluate("localStorage.setItem('bid_favorites','[]');localStorage.removeItem('bid.service.v1')")
    page.locator("#bidSystemImport").click()
    assert page.evaluate("JSON.parse(localStorage.getItem('bid.service.v1')).odo")==378584
    assert page.evaluate("JSON.parse(localStorage.getItem('bid_favorites'))")==["waze"]
    d["service"]["records"][0]["km"]=-1
    d["preferences"]["bid_favorites"]=["chrome"]
    page.locator("#bidSystemBackup").fill(json.dumps(d))
    page.locator("#bidSystemImport").click()
    assert "invalid" in page.locator("#bidSystemMessage").inner_text()
    assert page.evaluate("JSON.parse(localStorage.getItem('bid_favorites'))")==["waze"]
    assert page.evaluate("JSON.parse(localStorage.getItem('bid.service.v1')).odo")==378584
    legacy={"format":"DJ88-BID-preferences","version":1,"preferences":d["preferences"]}
    page.locator("#bidSystemBackup").fill(json.dumps(legacy))
    page.locator("#bidSystemImport").click()
    assert page.evaluate("JSON.parse(localStorage.getItem('bid_favorites'))")==["chrome"]
    assert page.evaluate("JSON.parse(localStorage.getItem('bid.service.v1')).odo")==378584
    page.evaluate("closeAll()")
    page.locator("#qfSpeedTile").click()
    page.locator("#bidServiceOpen").click()
    assert page.locator("#bidServiceOdo").input_value()=="378584"
    browser.close()
print("PASS: Recovery v2 roundtrip, allowlist, invalid data rejection, v1 compatibility and service refresh")
