import json, sys
from playwright.sync_api import sync_playwright

import os, pathlib
URL = os.environ.get("APP_URL", (pathlib.Path(__file__).resolve().parent.parent / "index.html").as_uri())
results = []
errors = []

def rec(id_, scenario, expected, ok, actual=""):
    results.append({"id": id_, "scenario": scenario, "expected": expected, "pass": bool(ok), "actual": actual})

with sync_playwright() as p:
    b = p.chromium.launch(args=["--no-sandbox"])
    ctx = b.new_context(viewport={"width": 390, "height": 844})
    pg = ctx.new_page()
    pg.on("pageerror", lambda e: errors.append(str(e)))
    pg.on("dialog", lambda d: (errors.append("native dialog: " + d.message), d.dismiss()))
    pg.goto(URL); pg.wait_for_timeout(300)
    txt = lambda: pg.inner_text("#app")

    # C1 first open shows sample data + the failed batch story
    t = txt()
    rec("C1", "Evaluator opens app cold", "Sample banner, 1 open purchase, closed rejected batch visible",
        "sample data" in t and "Floor pan sheet – replacement" in t and "Rejected" in t, t[:200])

    # C2 new purchase with vague spec -> risks flagged
    pg.click("#new-order")
    pg.fill("#f-title", "Side pod sheet")
    pg.fill("#f-thickness", "1.5")
    pg.select_option("#f-temper", "Not sure")
    pg.uncheck("#f-mtc")
    pg.select_option("#f-pay", "Full advance")
    t = txt()
    rec("C2", "Buyer writes spec the way the team did last time (no temper, no MTC, full advance)",
        "All 3 risks flagged before saving", t.count("Temper is not specified") == 1 and "No mill test certificate" in t and "Full advance payment" in t, "")

    # C3 fix spec -> tight
    pg.select_option("#f-temper", "T6"); pg.check("#f-mtc"); pg.select_option("#f-pay", "Pay after inspection")
    rec("C3", "Buyer fixes the spec", "Shows 'Spec is tight'", "Spec is tight" in txt(), "")

    # C4 save -> message contains spec + MTC + payment
    pg.click("#save-spec"); pg.wait_for_timeout(100)
    msg = pg.inner_text("#msg")
    rec("C4", "Generated seller message", "Message has grade-temper, thickness ± tol, MTC-before-dispatch, pay after inspection",
        "6061-T6" in msg and "1.5 mm (tolerance ±0.1 mm)" in msg and "BEFORE dispatch" in msg and "after we inspect" in msg, msg[:300])

    # C5 add new seller, WhatsApp link format
    pg.fill("#n-name", "Test Metals"); pg.fill("#n-phone", "98765 43210"); pg.click("#add-new"); pg.wait_for_timeout(100)
    href = pg.get_attribute("a:has-text('Send on WhatsApp')", "href") or ""
    rec("C5", "Add a new seller and open WhatsApp", "wa.me link with 91 prefix and prefilled message",
        href.startswith("https://wa.me/919876543210?text=") and "6061-T6" in __import__("urllib.parse").parse.unquote(href), href[:80])

    # C6 choose seller without MTC -> warning modal, no native dialog
    pg.click("button[data-choose]"); pg.wait_for_timeout(100)
    modal = pg.inner_text("#modal-root") if pg.query_selector(".modal") else ""
    rec("C6", "Choose a seller who hasn't confirmed spec or sent MTC", "In-page warning naming both gaps",
        "not confirmed grade" in modal and "MTC" in modal, modal[:200])
    pg.click("#m-ok"); pg.wait_for_timeout(100)

    # C7 delivery check: one reading out -> reject, accept disabled
    for i, v in enumerate(["1.5", "1.52", "1.31", "1.49", "1.5"]):
        pg.fill(f"[data-read='{i}']", v); pg.dispatch_event(f"[data-read='{i}']", "change"); pg.wait_for_timeout(50)
    t = txt()
    acc_disabled = pg.is_disabled("#accept")
    rec("C7", "Batch arrives, one point measures 1.31 mm on a 1.5 ± 0.1 spec", "Verdict = reject, 1 of 5 out; Accept disabled",
        "1 of 5 readings out of tolerance" in t and acc_disabled, "")

    # C8 reject -> seller record shows failure
    pg.click("#reject"); pg.click("#m-ok"); pg.wait_for_timeout(100)
    pg.click("#nav-sellers"); t = txt()
    row = [l for l in t.split("\n")]
    rec("C8", "Reject batch, then look at Sellers", "Test Metals shows 'Failed 1 batch'", "Failed 1 batch" in t and "Test Metals" in t, "")

    # C9 sample: sample seller who failed shows up flagged when adding to a new purchase
    pg.click("#nav-orders"); pg.click("#new-order"); pg.fill("#f-title", "Bracket sheet"); pg.fill("#f-thickness", "3"); pg.click("#save-spec")
    opts = pg.inner_text("#pick-seller")
    rec("C9", "Next purchase: picking a known seller", "Dropdown marks sellers who failed before", "Shree Metals (sample) – failed before" in opts, opts[:200])

    # C10 sample: dead-number flag
    pg.click("#nav-sellers"); t = txt()
    rec("C10", "Seller who never replies twice", "Flagged 'number may be dead'", "number may be dead" in t, "")

    # ---------- edge cases ----------
    # E1 empty state
    pg.click("#nav-orders"); pg.click("#clear-sample"); pg.click("#m-ok"); pg.wait_for_timeout(100)
    t = txt()
    rec("E1", "Start empty", "Empty state message, no sample banner", "No open purchases" in t and "sample data" not in t, t[:120])
    pg.click("#nav-sellers")
    rec("E1b", "Empty sellers page", "Helpful empty message", "No sellers yet" in txt(), "")

    # E2 bad input
    pg.click("#nav-orders"); pg.click("#new-order")
    pg.fill("#f-title", ""); pg.fill("#f-thickness", "abc"); pg.fill("#f-tol", "-1"); pg.click("#save-spec")
    t = txt()
    rec("E2", "Save spec with blank name, 'abc' thickness, negative tolerance", "Blocked with 3 field errors",
        "Give it a short name" in t and "Enter a thickness" in t and "Enter a tolerance" in t and pg.query_selector("#msg") is None, "")

    # E3 comma decimal
    pg.fill("#f-title", "Comma test"); pg.fill("#f-thickness", "2,5"); pg.fill("#f-tol", "0,1"); pg.click("#save-spec"); pg.wait_for_timeout(100)
    rec("E3", "Thickness typed with comma (2,5)", "Accepted as 2.5", pg.query_selector("#msg") is not None, "")

    # E4 bad phone + duplicate
    pg.fill("#n-name", "X"); pg.fill("#n-phone", "12345"); pg.click("#add-new")
    bad = "valid 10-digit" in txt()
    pg.fill("#n-phone", "9000000001"); pg.click("#add-new"); pg.wait_for_timeout(50)
    pg.fill("#n-name", "X again"); pg.fill("#n-phone", "+91 90000 00001"); pg.click("#add-new"); pg.wait_for_timeout(50)
    dup = "already on this purchase" in txt()
    rec("E4", "Invalid phone, then same number added twice in different formats", "Rejects bad number; detects duplicate", bad and dup, "")

    # E5 out of order: go to step 3 before choosing
    pg.click("[data-step='check']"); pg.wait_for_timeout(50)
    rec("E5", "Jump to 'Check delivery' before choosing a seller", "Blocked; stays on step 2", pg.query_selector("#msg") is not None, "")

    # E6 non-numeric reading
    pg.click("button[data-choose]"); pg.wait_for_timeout(50)
    if pg.query_selector("#m-ok"): pg.click("#m-ok")
    pg.fill("[data-read='0']", "two"); pg.dispatch_event("[data-read='0']", "change"); pg.wait_for_timeout(50)
    rec("E6", "Reading typed as 'two'", "Field marked, cannot decide", "Fix the readings" in txt() and pg.is_disabled("#reject"), "")

    # E7 reload persists
    pg.reload(); pg.wait_for_timeout(300)
    t = txt()
    rec("E7", "Reload page mid-purchase", "Purchases still there", "Comma test" in t, t[:150])

    # E8 large input
    pg.evaluate("""() => { const s = JSON.parse(localStorage.getItem('batchproof.v1'));
      for (let i=0;i<300;i++){ s.sellers.push({id:'bulk'+i,name:'Bulk seller '+i,phone:'9'+String(100000000+i),source:'IndiaMART',city:'X',addedAt:'2026-11-01'}); }
      for (let i=0;i<100;i++){ s.orders.push({id:'bo'+i,title:'Bulk order '+i,material:'Aluminium sheet',grade:'6061',temper:'T6',thickness:'2',tol:'0.1',size:'',qty:'1',needBy:'',pay:'Pay after inspection',mtc:true,createdAt:'2026-11-01',status:'inquiry',chosen:null,quotes:[{sellerId:'bulk'+i,sentAt:'2026-11-01',responded:false,specOk:false,mtcShared:false,price:'',lead:''}],check:null}); }
      localStorage.setItem('batchproof.v1', JSON.stringify(s)); }""")
    pg.reload(); pg.wait_for_timeout(300)
    import time; t0 = time.time(); pg.click("#nav-sellers"); pg.fill("#seller-search", "Bulk seller 29"); dt = time.time() - t0
    rec("E8", "300 sellers, 100 purchases; search sellers", "Renders and filters in < 2 s", "Bulk seller 299" in txt() and dt < 2, f"{dt:.2f}s")

    # E9 HTML injection
    pg.click("#nav-orders"); pg.click("#new-order"); pg.fill("#f-title", "<img src=x onerror=alert(1)>"); pg.fill("#f-thickness", "2"); pg.click("#save-spec"); pg.wait_for_timeout(100)
    rec("E9", "Name contains HTML/script", "Shown as text, nothing executes", pg.query_selector("#app img") is None and not any("native dialog" in e for e in errors), "")

    # E10 storage blocked
    ctx2 = b.new_context(); pg2 = ctx2.new_page()
    pg2.add_init_script("Object.defineProperty(window,'localStorage',{get(){throw new Error('blocked')}})")
    e2 = []; pg2.on("pageerror", lambda e: e2.append(str(e)))
    pg2.goto(URL); pg2.wait_for_timeout(300)
    rec("E10", "Browser blocks storage", "App still loads with sample data, no crash", "Floor pan sheet" in pg2.inner_text("#app") and not e2, ";".join(e2))


    # ---------- round 2 evals (added after reviewing screenshots) ----------
    c3 = b.new_context(viewport={"width": 390, "height": 844}); q = c3.new_page()
    q.on("pageerror", lambda e: errors.append(str(e)))
    q.goto(URL); q.wait_for_timeout(300); T = lambda: q.inner_text("#app")
    q.click("[data-open='o2']"); q.wait_for_timeout(100)
    t = T()
    rec("C11", "Compare 3 quotes on the replacement order", "Recommends National (spec+MTC) over cheaper Patel (no MTC) and says why",
        "Safest quote: National Aluminium Traders" in t and "Patel Sheet House (sample) is ₹800 cheaper but hasn't sent the MTC" in t, t[t.find('Compare'):t.find('Compare')+300])
    q.click("text=← Purchases"); q.click("[data-open='o1']"); q.click("[data-step='spec']"); q.wait_for_timeout(100)
    rec("E13", "Open spec of a closed (rejected) purchase", "Spec is read-only", q.query_selector("#save-spec") is None and "spec is locked" in T(), "")
    q.click("#nav-sellers")
    ov = q.evaluate("document.documentElement.scrollWidth <= window.innerWidth + 1")
    rec("E15", "Sellers page on a 390px phone", "No horizontal overflow", ov, "")
    q.click("#nav-orders"); q.click("#new-order")
    q.fill("#f-title", "Firewall"); q.select_option("#f-material", "Steel tube (CDS/ERW)"); q.select_option("#f-grade", "Other")
    q.fill("#f-thickness", "1"); q.click("#save-spec")
    blocked = "Type the grade" in T() and q.query_selector("#msg") is None
    q.fill("#f-grade-other", "AISI 304"); q.select_option("#f-temper", "Other"); q.fill("#f-temper-other", "Annealed"); q.click("#save-spec"); q.wait_for_timeout(100)
    m = q.inner_text("#msg") if q.query_selector("#msg") else ""
    rec("E11", "Grade not in the list ('Other')", "Blocks blank 'Other'; typed grade/temper appear in message", blocked and "AISI 304-Annealed" in m, m[:160])
    q.fill("#n-name", "Fresh"); q.fill("#n-phone", "9111111111"); q.click("#add-new"); q.wait_for_timeout(50)
    q.click("#nav-sellers")
    fresh = [c for c in q.inner_text("#app").split("Fresh")[1:2]]
    rec("E14", "Seller asked today, no reply yet", "Not flagged as dead number", fresh and "may be dead" not in fresh[0].split("\n\n")[0], "")
    q.click("#nav-orders"); q.click("text=Firewall"); q.click("button[data-choose]"); q.wait_for_timeout(50)
    if q.query_selector("#m-ok"): q.click("#m-ok")
    for i, v in enumerate(["1.1", "0.9", "1.0", "1.1", "0.9"]):
        q.fill(f"[data-read='{i}']", v); q.dispatch_event(f"[data-read='{i}']", "change"); q.wait_for_timeout(30)
    rec("E12", "Readings exactly on the tolerance limit (1.0 ± 0.1 → 0.9 / 1.1)", "Counted as in tolerance, not 'Out'", "out of tolerance" not in T() and "Out" not in T(), "")
    c3.close()

    b.close()

rec("JS", "No uncaught JS errors or native dialogs during run", "0 errors", not errors, "; ".join(errors)[:300])
json.dump(results, open(str(pathlib.Path(__file__).resolve().parent / "results.json"), "w"), indent=1)
for r in results:
    print(("PASS" if r["pass"] else "FAIL"), r["id"], "-", r["scenario"], "|", r["actual"][:120] if not r["pass"] else "")
print(sum(r["pass"] for r in results), "/", len(results))
