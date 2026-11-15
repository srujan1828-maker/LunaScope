from playwright.sync_api import sync_playwright,expect
from pathlib import Path
import json
out=Path(__file__).resolve().parents[1]/'verification-output'
out.mkdir(exist_ok=True)
expect.set_options(timeout=180000)
with sync_playwright() as p:
 browser=p.chromium.launch(channel='chrome',headless=True,args=['--enable-unsafe-swiftshader'])
 page=browser.new_page(viewport={'width':1440,'height':1000});page.set_default_timeout(180000)
 page.add_init_script("localStorage.setItem('lunascope.mission.v4',JSON.stringify({start:'2027-01-01',utcTime:'06:30:00',days:1,sunlight:0,earth:0,mast:2,margin:0,comms:false,terrain:'unassessed'}));")
 errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 page.goto('http://127.0.0.1:8000/#/planner',wait_until='domcontentloaded')
 page.get_by_role('button',name='Export analysis',exact=True).click()
 dialog=page.get_by_role('dialog',name='Export mission scenario')
 dialog.get_by_role('button',name='Generate Scenario Export Bundle').click()
 link=dialog.get_by_role('link',name='Download JSON');expect(link).to_be_visible()
 response=page.request.get('http://127.0.0.1:8000'+link.get_attribute('href'));assert response.status==200
 bundle=response.json();assert '06:30:00' in json.dumps(bundle)
 dialog.locator('input[type=text]').fill('Updated verification scenario')
 expect(dialog.get_by_role('link',name='Download JSON')).to_have_count(0)
 dialog.get_by_role('button',name='Generate Scenario Export Bundle').click()
 link=dialog.get_by_role('link',name='Download JSON');expect(link).to_be_visible()
 updated=page.request.get('http://127.0.0.1:8000'+link.get_attribute('href')).json()
 assert updated['title']=='Updated verification scenario'
 dialog.get_by_label('Close dialog').click()
 page.get_by_role('button',name='Find mission windows',exact=True).click()
 dialog=page.get_by_role('dialog',name='Find mission windows')
 assert dialog.locator('input[type=datetime-local]').first.input_value()=='2027-01-01T06:30'
 dialog.locator('input[type=datetime-local]').nth(1).fill('2027-01-02T06:30')
 for label,value in [('Minimum sunlight (%)','0'),('Maximum shadow gap (h)','200'),('Minimum Earth-center visibility (%)','0'),('Maximum Earth outage (h)','200'),('Minimum joint visibility (%)','0')]:dialog.get_by_label(label,exact=True).fill(value)
 dialog.get_by_role('button',name='Search Surface Operation Windows').click()
 dialog.get_by_role('button',name='Apply Window',exact=True).first.click()
 expect(page.get_by_label('Mission start time',exact=True)).to_have_value('06:30:00')
 print('Scenario save/export and real mission-window search/apply PASS',flush=True)
 page.get_by_role('button',name='Explore selected site in 3D').click()
 page.get_by_role('button',name='Power & battery model').click()
 expect(page.get_by_role('dialog',name='Power and battery model')).to_be_visible()
 page.get_by_role('dialog').get_by_label('Close dialog').click()
 page.get_by_role('button',name='Mast sensitivity',exact=True).click()
 dialog=page.get_by_role('dialog',name='Mast sensitivity');expect(dialog.locator('tbody tr')).to_have_count(8)
 dialog.get_by_label('Close dialog').click()
 page.get_by_role('button',name='Landing dispersion',exact=True).click()
 dialog=page.get_by_role('dialog',name='Landing dispersion')
 expect(dialog.locator('text=Median:').first).to_be_visible()
 assert dialog.get_by_role('alert').count()==0
 dialog.get_by_label('Close dialog').click()
 print('Power model, eight-height mast sweep and real dispersion API integration PASS',flush=True)
 # Hold requests until their controls change; obsolete responses must not render.
 held=[]
 page.route('**/api/simulation/dispersion',lambda route:held.append(route))
 page.get_by_role('button',name='Landing dispersion',exact=True).click()
 dialog=page.get_by_role('dialog',name='Landing dispersion')
 page.wait_for_timeout(500)
 assert held
 dialog.locator('input[type=range]').first.fill('300')
 expect(dialog.get_by_role('button',name='Sample Ellipse')).to_be_enabled()
 try:held[0].fulfill(status=503,content_type='application/json',body='{"detail":"Obsolete dispersion result"}')
 except Exception:pass  # Aborted requests may no longer accept a response.
 page.wait_for_timeout(200)
 expect(dialog.get_by_role('alert')).to_have_count(0)
 dialog.get_by_label('Close dialog').click()
 page.unroute('**/api/simulation/dispersion')
 page.locator('nav[aria-label="Main navigation"]').get_by_role('button',name='Mission Planner',exact=True).click()
 held_windows=[]
 page.route('**/api/windows/search',lambda route:held_windows.append(route))
 page.get_by_role('button',name='Find mission windows',exact=True).click()
 dialog=page.get_by_role('dialog',name='Find mission windows')
 dialog.get_by_role('button',name='Search Surface Operation Windows').click()
 page.wait_for_timeout(500);assert held_windows
 dialog.get_by_label('Minimum sunlight (%)',exact=True).fill('30')
 expect(dialog.get_by_role('button',name='Search Surface Operation Windows')).to_be_enabled()
 try:held_windows[0].fulfill(status=503,content_type='application/json',body='{"detail":"Obsolete window result"}')
 except Exception:pass
 page.wait_for_timeout(200)
 expect(dialog.get_by_text('Obsolete window result')).to_have_count(0)
 dialog.get_by_label('Close dialog').click()
 page.unroute('**/api/windows/search')
 page.get_by_role('button',name='Explore selected site in 3D').click()
 print('Edited exports and obsolete request cancellation PASS',flush=True)
 # Failure responses must remain visible and must not become synthetic results.
 page.route('**/api/simulation/dispersion',lambda route:route.fulfill(status=503,content_type='application/json',body='{"detail":"Terrain temporarily unavailable (integration test)"}'))
 page.get_by_role('button',name='Landing dispersion',exact=True).click()
 expect(page.get_by_role('dialog').get_by_role('alert')).to_contain_text('Terrain temporarily unavailable')
 page.get_by_role('dialog').get_by_label('Close dialog').click()
 page.route('**/api/scenarios/evaluate',lambda route:route.fulfill(status=503,content_type='application/json',body='{"detail":"Scientific inputs unavailable (integration test)"}'))
 page.locator('nav[aria-label="Main navigation"]').get_by_role('button',name='Timeline',exact=True).click()
 page.locator('#window-select').select_option('7')
 expect(page.locator('.timeline-main-column [role=alert]')).to_contain_text('Scientific inputs unavailable')
 expect(page.locator('.metric-status-rows .row-value').first).to_have_text('Unknown')
 print('Unavailable scientific data shown explicitly, no fabricated fallback PASS',flush=True)
 assert not errors,errors
 page.set_viewport_size({'width':390,'height':844})
 for route in ['planner','horizon','timeline','educator','sources']:
  page.evaluate('(route)=>location.hash="/"+route',route);page.wait_for_timeout(500)
  assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'),route
 print('Final build mobile layout and page errors PASS',flush=True)
 browser.close()
