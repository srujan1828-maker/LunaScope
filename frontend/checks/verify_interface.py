from playwright.sync_api import sync_playwright,expect
from pathlib import Path
import json,time
out=Path(__file__).resolve().parents[1]/'verification-output';out.mkdir(exist_ok=True)
with sync_playwright() as p:
 browser=p.chromium.launch(channel='chrome',headless=True,args=['--enable-unsafe-swiftshader'])
 page=browser.new_page(viewport={'width':1440,'height':1000});page.set_default_timeout(180000)
 errors=[];bad=[];evaluations=[]
 page.on('pageerror',lambda e:errors.append(str(e)))
 def response(r):
  if r.status>=400 and ('/assets/' in r.url or '/api/' in r.url):bad.append([r.url,r.status])
  if '/api/scenarios/evaluate' in r.url and r.status==200:
   try:evaluations.append(r.json())
   except Exception:pass
 page.on('response',response)
 page.goto('http://127.0.0.1:8000/#/planner',wait_until='domcontentloaded')
 expect(page.locator('.candidate-data-table tbody tr')).to_have_count(13)
 expect(page.locator('.mission-feedback').first).to_contain_text('13 evaluated',timeout=240000)
 expect(page.locator('.candidate-data-table tbody')).not_to_contain_text('Pending')
 first=page.locator('.selected-metric-grid').inner_text()
 page.screenshot(path=str(out/'imported-planner.png'),full_page=True)
 print('Planner catalog and live results PASS',flush=True)
 page.get_by_role('button',name='Select LOLA South Pole 11',exact=True).click()
 expect(page.locator('.mission-feedback').first).to_contain_text('LOLA South Pole 11')
 expect(page.locator('.mission-feedback').first).to_contain_text('13 evaluated',timeout=240000)
 second=page.locator('.selected-metric-grid').inner_text();assert first!=second,(first,second)
 page.get_by_role('button',name='Prepare backups',exact=True).click()
 expect(page.get_by_role('dialog')).to_be_visible();page.get_by_role('dialog').locator('input[type=checkbox]').first.check();page.get_by_role('button',name='Done',exact=True).click()
 page.get_by_label('Mission start time',exact=True).fill('06:30:00')
 expect(page.locator('.mission-feedback').first).to_contain_text('13 evaluated',timeout=240000)
 page.get_by_role('button',name='Explore selected site in 3D').click()
 expect(page.get_by_test_id('moon-globe').locator('canvas')).to_be_visible()
 expect(page.locator('.globe-caption')).to_contain_text('LROC color mosaic + LOLA global shape')
 page.get_by_role('button',name='Local surface',exact=True).click()
 expect(page.get_by_test_id('terrain-viewport').locator('canvas')).to_be_visible()
 page.get_by_role('button',name='Whole Moon',exact=True).click()
 page.locator('.terrain-stage').screenshot(path=str(out/'imported-moon.png'))
 page.get_by_role('button',name='Horizon View',exact=True).click()
 expect(page.locator('.live-horizon-chart svg')).to_be_visible(timeout=240000)
 page.get_by_label('Horizon time',exact=True).fill('10')
 assert evaluations and evaluations[-1]['inputs']['start_time_iso'].startswith('2027-01-01T06:30'),[e['inputs'] for e in evaluations]
 print('Site selection, UTC, backups, globe, local surface and computed horizon PASS',flush=True)
 page.locator('nav[aria-label="Main navigation"]').get_by_role('button',name='Timeline',exact=True).click()
 expect(page.locator('.timeline-main-column')).to_be_visible()
 expect(page.locator('.primary-time-display')).to_contain_text('2027')
 expect(page.locator('.metric-status-rows')).not_to_contain_text('Unknown',timeout=240000)
 page.get_by_label('Timeline time',exact=True).fill('0')
 data=evaluations[-1]['evaluated_sites']['lola-sp-011']
 expect(page.locator('.metric-status-rows .row-value').first).to_have_text(f"{data['solar_fractions'][0]:.2f}")
 page.screenshot(path=str(out/'imported-timeline.png'),full_page=True)
 print('Timeline agrees with API solar sample PASS',flush=True)
 page.locator('nav[aria-label="Main navigation"]').get_by_role('button',name='Data',exact=True).click()
 expect(page.locator('.hash-cell')).to_have_count(7)
 with page.expect_download() as dl:page.get_by_role('button',name='Location catalogue CSV').click()
 dl.value.save_as(out/'imported-locations.csv')
 assert 'lola-sp-011' in (out/'imported-locations.csv').read_text()
 page.locator('nav[aria-label="Main navigation"]').get_by_role('button',name='Learn',exact=True).click()
 expect(page.locator('.learning-scope')).to_be_visible()
 for name in ['Lunar South Pole','Sun & Earth Motion','Power & Illumination','Communication (DTE)','Mission Challenges','Key Terms']:
  page.locator('.learn-sidebar-nav').get_by_role('button',name=name,exact=True).click()
  assert not errors,errors
 print('Data hashes, downloads and seven Learn tabs PASS',flush=True)
 mobile=[]
 page.set_viewport_size({'width':390,'height':844})
 for route in ['home','planner','horizon','timeline','educator','sources']:
  page.evaluate('(route)=>location.hash="/"+route',route);page.wait_for_timeout(500)
  width=page.evaluate('document.documentElement.scrollWidth')
  mobile.append([route,width]);page.screenshot(path=str(out/f'imported-mobile-{route}.png'),full_page=True)
 print(json.dumps({'errors':errors,'failed_requests':bad,'mobile_widths':mobile},indent=2),flush=True)
 assert not errors and not bad,(errors,bad)
 assert all(width<=391 for _,width in mobile),mobile
 browser.close()
