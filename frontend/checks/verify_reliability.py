"""Interaction and recovery checks against the running local service."""
from pathlib import Path
import json
from playwright.sync_api import sync_playwright, expect

BASE='http://127.0.0.1:8000'
OUT=Path(__file__).resolve().parents[1]/'verification-output'
OUT.mkdir(exist_ok=True)
expect.set_options(timeout=180000)
MISSION={'start':'2027-01-01','utcTime':'06:30:00','days':1,'sunlight':0,'earth':0,'mast':2,'margin':0,'comms':False,'terrain':'unassessed'}
report={}
with sync_playwright() as p:
 browser=p.chromium.launch(channel='chrome',headless=True,args=['--enable-unsafe-swiftshader'])
 page=browser.new_page(viewport={'width':1440,'height':1000})
 page.set_default_timeout(180000)
 errors=[]
 page.on('pageerror',lambda e:errors.append(str(e)))
 page.add_init_script("window.testSockets=[];const RealSocket=window.WebSocket;window.WebSocket=class extends RealSocket{constructor(...args){super(...args);window.testSockets.push(this);}};if(!localStorage.getItem('lunascope.mission.v4'))localStorage.setItem('lunascope.mission.v4',"+json.dumps(json.dumps(MISSION))+");")
 page.goto(BASE+'/#/educator',wait_until='domcontentloaded')
 video=page.locator('.hero-orbit-video')
 page.wait_for_function("document.querySelector('.hero-orbit-video')?.readyState>=2")
 page.locator('.hero-action-row button').first.click()
 assert video.evaluate('(v)=>v.paused')
 page.locator('.orbit-slider').fill('180')
 assert abs(video.evaluate('(v)=>v.currentTime/v.duration')-.5)<.02
 page.locator('.hero-action-row button').nth(1).click()
 assert video.evaluate('(v)=>v.currentTime')<.1
 page.locator('.hero-action-row button').first.click()
 page.wait_for_function("document.querySelector('.hero-orbit-video').currentTime>0.1")
 background=page.locator('.video-background video')
 assert background.evaluate('(v)=>v.loop && v.muted && v.readyState>=2')
 background.evaluate('(v)=>v.currentTime=v.duration-.15')
 page.wait_for_function("document.querySelector('.video-background video').currentTime<1",timeout=15000)
 report['learning_video_and_background_loop']='PASS';print('Video controls and looping PASS',flush=True)
 tabs=['The Big Picture','Lunar South Pole','Sun & Earth Motion','Power & Illumination','Communication (DTE)','Mission Challenges','Key Terms']
 widths=[]
 for width in [320,390,768,1440]:
  page.set_viewport_size({'width':width,'height':900})
  for tab in tabs:
   print('Checking Learn',width,tab,flush=True);page.locator('.learn-sidebar-nav').get_by_role('button',name=tab,exact=True).click(timeout=15000)
   page.wait_for_timeout(150)
   actual=page.evaluate('document.documentElement.scrollWidth')
   if actual>width+1:widths.append({'viewport':width,'tab':tab,'actual':actual})
   ranges=page.locator('.learn-main-column input[type=range]')
   for i in range(ranges.count()):
    item=ranges.nth(i);item.focus();item.press('End')
 report['learning_layout_overflows']=widths;print('Learn layouts:',widths,flush=True)
 search=page.locator('.learn-main-column input[type=text]')
 if search.count():
  search.fill('libration');assert 'libration' in page.locator('.learn-main-column').inner_text().lower()
 page.set_viewport_size({'width':1440,'height':1000})
 page.evaluate("location.hash='/horizon'")
 stream=page.locator('.advanced-stream')
 stream.locator('summary').click();print('Waiting for streamed time',flush=True)
 expect(stream).to_contain_text('2027-01-01 06:30:00',timeout=240000)
 stream.get_by_role('button',name='+1h Step',exact=True).click()
 expect(stream).to_contain_text('2027-01-01 07:30:00',timeout=240000)
 stream.get_by_role('button',name='Start Live Sim',exact=True).click()
 expect(stream.get_by_role('button',name='Pause Live Stream',exact=True)).to_be_visible()
 stream.get_by_role('button',name='Pause Live Stream',exact=True).click()
 stream.locator('summary').click()
 report['stream_step_start_pause']='PASS';print('Stream controls PASS',flush=True)
 stream.locator('summary').click()
 page.evaluate("window.testSockets.filter(s=>s.url.includes('/ws/simulation')).forEach(s=>s.close())")
 expect(stream.get_by_role('alert')).to_contain_text('disconnected')
 stream.get_by_role('button',name='Reconnect simulation').click()
 expect(stream).to_contain_text('2027-01-01 06:30:00',timeout=240000)
 page.get_by_role('button',name='Power & battery model').click()
 dialog=page.get_by_role('dialog',name='Power and battery model')
 dialog.get_by_role('checkbox').uncheck()
 dialog.get_by_label('Close dialog').click()
 expect(stream).to_contain_text('Electrical model disabled')
 expect(stream.get_by_text('Battery SoC',exact=True)).to_have_count(0)
 stream.get_by_role('button',name='+1h Step',exact=True).click()
 expect(stream).to_contain_text('2027-01-01 07:30:00',timeout=240000)
 stream.locator('summary').click()
 report['stream_reconnect_and_disabled_power']='PASS'
 print('Stream reconnect and disabled power PASS',flush=True)
 # HTTP fallback: only matching WebSockets are blocked in this isolated page.
 fallback=browser.new_page();fallback.set_default_timeout(180000)
 fallback.add_init_script("localStorage.setItem('lunascope.mission.v4',"+json.dumps(json.dumps(MISSION))+");")
 fallback.route_web_socket('**/api/ws/matches',lambda ws:ws.close())
 fallback.goto(BASE+'/#/planner',wait_until='domcontentloaded')
 expect(fallback.locator('.mission-feedback').first).to_contain_text('HTTP connected')
 expect(fallback.locator('.mission-feedback').first).to_contain_text('13 evaluated',timeout=240000)
 report['matching_http_fallback']='PASS'
 fallback.close()
 # A failed initial catalog request must be recoverable without a full reload.
 retry=browser.new_page();retry.set_default_timeout(10000)
 attempts=[0]
 def catalog(route):
  attempts[0]+=1
  if attempts[0]==1:route.fulfill(status=503,content_type='application/json',body='{"detail":"Temporary catalog outage"}')
  else:route.continue_()
 retry.route('**/api/sites',catalog)
 retry.goto(BASE+'/#/planner',wait_until='domcontentloaded')
 retry.wait_for_timeout(2000)
 button=retry.get_by_role('button',name='Retry analysis',exact=True)
 if button.count():
  button.click()
  expect(retry.locator('.candidate-data-table tbody tr')).to_have_count(13,timeout=30000)
 report['catalog_retry']={'requests':attempts[0],'rows':retry.locator('.candidate-data-table tbody tr').count()}
 retry.close()
 # Valid JSON with an obsolete/invalid shape should recover to supported defaults.
 damaged=browser.new_page();damage_errors=[]
 damaged.on('pageerror',lambda e:damage_errors.append(str(e)))
 damaged.add_init_script("localStorage.setItem('lunascope.mission.v4','{}');localStorage.setItem('lunascope.compare.v4','{}');")
 damaged.goto(BASE+'/#/home',wait_until='domcontentloaded');damaged.wait_for_timeout(1000)
 report['saved_settings_recovery']={'errors':damage_errors,'main_visible':damaged.locator('main').count()>0}
 damaged.close()
 report['page_errors']=errors
 (OUT/'reliability.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
 print(json.dumps(report,indent=2),flush=True)
 browser.close()
assert not widths and not errors,report
assert report['catalog_retry']['rows']==13,report
assert report['saved_settings_recovery']=={'errors':[],'main_visible':True},report
