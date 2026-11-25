from pathlib import Path
from playwright.sync_api import sync_playwright
assets=Path("app/src/main/assets").resolve()
with sync_playwright() as p:
    browser=p.chromium.launch(headless=True,args=["--no-sandbox"])
    page=browser.new_page(viewport={"width":1280,"height":720})
    page.add_init_script("""window.sample={lux:15000,sensorRegistered:true};window.modes=[];window.BID={displaySnapshot:()=>JSON.stringify(sample),setDisplayMode:m=>modes.push(m)};""")
    page.goto((assets/"index.html").as_uri())
    stage=page.locator("#stage")
    assert stage.get_attribute("data-bid-display-source")=="sensor"
    assert stage.get_attribute("data-bid-display-effective")=="sun"
    page.evaluate("sample.sensorRegistered=false;bidDisplayMode('auto')")
    assert stage.get_attribute("data-bid-display-effective")=="system"
    assert stage.get_attribute("data-bid-display-source")=="system"
    page.evaluate("updateGpsWeather({fresh:true,isDay:false,code:0})")
    assert stage.get_attribute("data-bid-display-source")=="weather"
    assert stage.get_attribute("data-bid-display-effective")=="night"
    page.evaluate("bidDisplayMode('day')")
    assert stage.get_attribute("data-bid-display-source")=="manual"
    assert stage.get_attribute("data-bid-display-effective")=="day"
    page.reload()
    assert stage.get_attribute("data-bid-display-effective")=="day"
    page.evaluate("bidDisplayMode('auto');sample.sensorRegistered=false;updateGpsWeather({fresh:false,isDay:false,code:0})")
    assert stage.get_attribute("data-bid-display-effective")=="system"
    page.evaluate("sample={lux:15000,sensorRegistered:true};BID.setDisplayMode=()=>{throw Error('bridge')};bidDisplayMode('auto')")
    page.evaluate("BID.setDisplayMode=m=>modes.push(m)")
    page.wait_for_function("modes.at(-1)==='sun'")
    browser.close()
print("PASS: sensor registration, weather fallback, manual persistence, stale weather and bridge retry")
