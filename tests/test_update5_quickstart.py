from pathlib import Path
from playwright.sync_api import sync_playwright
assets=Path("app/src/main/assets").resolve()
with sync_playwright() as p:
    browser=p.chromium.launch(headless=True,args=["--no-sandbox"])
    page=browser.new_page(viewport={"width":1280,"height":720})
    page.add_init_script("""window.calls=[];window.BID={open:x=>calls.push(x)};""")
    page.goto((assets/"index.html").as_uri())
    page.evaluate("openMusicMenu()")
    assert page.locator("#bidQuickStart [data-quick-favorite]").count()==3
    page.locator('[data-quick-favorite="waze"]').click()
    assert page.evaluate("calls.at(-1)")=="waze"
    assert not page.locator("#bidSmartPanel").is_visible()
    page.evaluate("openMusicMenu()")
    page.locator("#bidQuickConfig").click()
    assert page.locator("#bidSystemPanel").is_visible()
    page.locator('[data-favorite="waze"]').click()
    page.locator('[data-favorite="chrome"]').click()
    page.locator("#bidSystemClose").click()
    assert page.locator('[data-quick-favorite="waze"]').count()==0
    assert page.locator('[data-quick-favorite="chrome"]').count()==1
    page.reload()
    page.evaluate("openMusicMenu()")
    assert page.locator('[data-quick-favorite="chrome"]').count()==1
    assert page.locator('[data-quick-favorite="waze"]').count()==0
    assert page.locator('[aria-label="Aplicații"]').count()==1
    assert page.locator('[aria-label="Mașină"]').count()==1
    browser.close()
print("PASS: quick launch, shared favorites, persistence and original controls")
