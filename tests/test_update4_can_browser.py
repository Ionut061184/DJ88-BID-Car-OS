from pathlib import Path
from playwright.sync_api import sync_playwright

assets = Path(__file__).resolve().parents[1] / "app/src/main/assets"
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True,args=["--no-sandbox"])
    page=browser.new_page(viewport={"width":1280,"height":720})
    page.add_init_script("""window.sample={};window.calls=[];window.BID={qfVehicleSnapshot:()=>JSON.stringify(window.sample),open:x=>calls.push(x)};""")
    page.goto((assets/"index.html").as_uri())
    page.wait_for_selector("#qfSpeedTile")
    assert "— km/h" in page.locator("#qfSpeedTile").inner_text()
    assert "— L" in page.locator("#qfFuelTile").inner_text()
    for id,x1,x2 in [("qfSpeedTile",18,178),("qfFuelTile",1105,1263)]:
        box=page.locator("#"+id).bounding_box()
        assert box and box["x"]>=x1 and box["x"]+box["width"]<=x2 and box["y"]>=630 and box["y"]+box["height"]<=700, box
    page.evaluate("window.sample={fresh:true,ageMs:100,speedCandidate:0,fuelCandidate:18,rpmCandidate:828,messages:2,candidateFrames:1}")
    page.wait_for_function("document.querySelector('#qfFuelTile').textContent.includes('18.0 L')")
    assert "0 km/h" in page.locator("#qfSpeedTile").inner_text()
    assert "CAN TEST" in page.locator("#qfFuelTile").inner_text()
    car=page.locator('button[aria-label="Mașină"]')
    assert car.count()==1, "Original car menu button missing"
    car.click()
    assert page.evaluate("calls.includes('car')"), "Original Mașină action no longer opens OEM menu"
    assert not page.locator("#qfVehiclePanel").is_visible()
    page.evaluate("window.calls=[]")
    page.locator("#qfSpeedTile").click()
    assert page.locator("#qfVehiclePanel").is_visible()
    assert "828 RPM" in page.locator("#qfVehicleText").inner_text()
    page.locator("#qfOriginal").click()
    assert page.evaluate("calls.includes('car')")
    page.evaluate("window.sample.ageMs=6000")
    page.wait_for_function("document.querySelector('#qfFuelTile').textContent.includes('— L')")
    page.evaluate("window.sample={fresh:true,ageMs:100,speedCandidate:999,fuelCandidate:-1}")
    page.wait_for_timeout(1200)
    assert "— km/h" in page.locator("#qfSpeedTile").inner_text()
    assert "— L" in page.locator("#qfFuelTile").inner_text()
    browser.close()
print("PASS: CAN test tile geometry, original menu, valid zero, invalid and stale data")
