from pathlib import Path
from playwright.sync_api import sync_playwright
assets=Path("app/src/main/assets").resolve()
with sync_playwright() as p:
    browser=p.chromium.launch(headless=True,args=["--no-sandbox"])
    page=browser.new_page(viewport={"width":1280,"height":720})
    page.add_init_script("""window.lux=15000;window.modes=[];window.BID={displaySnapshot:()=>JSON.stringify({lux:window.lux}),setDisplayMode:m=>modes.push(m)};""")
    page.goto((assets/"index.html").as_uri())
    page.evaluate("bidDisplayMode('auto')")
    stage=page.locator("#stage")
    assert stage.get_attribute("data-bid-anti-glare")=="active"
    assert page.evaluate("modes.at(-1)")=="sun"
    assert stage.evaluate("e=>getComputedStyle(e).backgroundBlendMode")=="multiply"
    page.evaluate("lux=9000")
    page.wait_for_timeout(2700)
    assert stage.get_attribute("data-bid-anti-glare")=="active"
    page.evaluate("lux=2000")
    page.wait_for_function("document.querySelector('#stage').dataset.bidAntiGlare==='inactive'")
    assert page.evaluate("modes.at(-1)")=="day"
    page.evaluate("lux=5")
    page.wait_for_function("modes.at(-1)==='night'")
    assert stage.get_attribute("data-bid-anti-glare")=="inactive"
    page.evaluate("bidDisplayMode('sun')")
    assert stage.get_attribute("data-bid-anti-glare")=="active"
    page.evaluate("bidDisplayMode('day')")
    assert stage.get_attribute("data-bid-anti-glare")=="inactive"
    page.evaluate("lux=null;bidDisplayMode('auto')")
    assert stage.get_attribute("data-bid-anti-glare")=="inactive"
    assert page.evaluate("modes.at(-1)")=="system"
    browser.close()
print("PASS: sunlight contrast, hysteresis, day/night, manual override and missing sensor")
