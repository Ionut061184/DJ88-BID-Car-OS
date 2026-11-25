from pathlib import Path
from playwright.sync_api import sync_playwright
assets=Path("app/src/main/assets").resolve()
with sync_playwright() as p:
    browser=p.chromium.launch(headless=True,args=["--no-sandbox"])
    page=browser.new_page(viewport={"width":1280,"height":720})
    page.goto((assets/"index.html").as_uri())
    def open_service():
        page.locator("#qfSpeedTile").click()
        page.locator("#bidServiceOpen").click()
        assert page.locator("#bidServicePanel").is_visible()
        assert page.locator("#bidServiceRows section").count()==10
    open_service()
    row=page.locator("#bidServiceRows section").first
    assert "Neverificat" in row.inner_text()
    page.locator("#bidServiceOdo").fill("378584")
    page.locator("#bidServiceSaveOdo").click()
    row.get_by_role("button",name="Schimb efectuat").click()
    assert row.locator("input").nth(0).input_value()=="378584"
    assert "În termen" in row.inner_text()
    page.locator("#bidServiceOdo").fill("388000")
    page.locator("#bidServiceSaveOdo").click()
    assert "Se apropie" in row.inner_text()
    page.locator("#bidServiceOdo").fill("388584")
    page.locator("#bidServiceSaveOdo").click()
    assert "Depășit" in row.inner_text()
    page.locator("#bidServiceOdo").fill("1")
    page.locator("#bidServiceSaveOdo").click()
    assert "invalid" in page.locator("#bidServiceMessage").inner_text()
    page.reload()
    open_service()
    assert page.locator("#bidServiceOdo").input_value()=="388584"
    assert "Depășit" in row.inner_text()
    assert row.locator("input").nth(0).input_value()=="378584"
    distribution=page.locator("#bidServiceRows section").nth(5)
    assert distribution.locator("input").nth(2).input_value()==""
    assert "Neverificat" in distribution.inner_text()
    page.locator("#bidServiceClose").click()
    assert page.locator("#qfVehiclePanel").is_visible()
    assert not page.locator("#bidServicePanel").is_visible()
    page.evaluate("""window.reading={fresh:true,ageMs:100,verified:false,odometerCandidate:388600.8};window.BID={qfVehicleSnapshot:()=>JSON.stringify(reading)}""")
    page.locator("#bidServiceOpen").click()
    assert page.locator("#bidServiceOdo").input_value()=="388600"
    assert "TEST" in page.locator("#bidServiceOdoSource").inner_text()
    assert page.evaluate("JSON.parse(localStorage.getItem('bid.service.v1')).odo")==388584
    row.get_by_role("button",name="Schimb efectuat").click()
    assert "Confirmă" in page.locator("#bidServiceMessage").inner_text()
    page.locator("#bidServiceSaveOdo").click()
    assert page.evaluate("JSON.parse(localStorage.getItem('bid.service.v1')).odo")==388600
    page.locator("#bidServiceClose").click()
    page.evaluate("reading.verified=true;reading.odometerCandidate=388620.9")
    page.locator("#bidServiceOpen").click()
    assert page.locator("#bidServiceOdo").input_value()=="388620"
    page.evaluate("reading.odometerCandidate=388621.4")
    row.get_by_role("button",name="Schimb efectuat").click()
    assert row.locator("input").nth(0).input_value()=="388621"
    page.locator("#bidServiceClose").click()
    page.evaluate("reading.odometerCandidate=389000;reading.ageMs=6001")
    page.locator("#bidServiceOpen").click()
    assert page.locator("#bidServiceOdo").input_value()=="388621"
    assert "indisponibil" in page.locator("#bidServiceOdoSource").inner_text()
    browser.close()
print("PASS: maintenance defaults, missing data, local persistence, due warnings, rollback protection and return menu")
