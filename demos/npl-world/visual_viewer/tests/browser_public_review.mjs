import { chromium } from 'playwright';
import { writeFile } from 'node:fs/promises';
const url=process.env.PREVIEW_URL || 'http://127.0.0.1:8766/';
const browser=await chromium.launch({
  headless:true,
  args:['--no-sandbox','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader']
});
const page=await browser.newPage({viewport:{width:1440,height:900},deviceScaleFactor:1});
const consoleErrors=[],failedRequests=[];
page.on('pageerror',error=>consoleErrors.push(error.message));
page.on('requestfailed',request=>failedRequests.push(request.url()));
let report={};
try{
  await page.goto(url,{waitUntil:'domcontentloaded',timeout:40000});
  await page.waitForFunction(()=>window.NPL_READY?.cityOnly===true,null,{timeout:60000});
  await page.waitForTimeout(1200);
  const state=await page.evaluate(()=>({
    ready:window.NPL_READY||null,
    webglCanvas:!!document.querySelector('canvas#game'),
    loadingVisible:!!document.querySelector('#loading'),
    selectedCamera:document.querySelector('#cameraMode')?.textContent||'',
    pageTitle:document.title,
    width:document.querySelector('canvas#game')?.width,
    height:document.querySelector('canvas#game')?.height
  }));
  // Genuine client-side lesson: source linked, cognitive HUD visible, no accounts.
  await page.waitForFunction(()=>window.NPL_MISSION?.publicEvidenceReady===true,null,{timeout:15000});
  const starting=await page.evaluate(()=>({...window.NPL_MISSION,summary:document.querySelector('#nplConflictSummary')?.textContent||''}));
  if(starting.stage!==0||starting.mode!=='source_based'||starting.noSocialNetworking!==true||
      !starting.summary.includes('ES30') ){
    throw new Error('NPL/source binding failed: '+JSON.stringify(starting));
  }
  // The protected 437-structure NPL brain is intentionally NOT in PUBLIC CI.
  // No synthetic 2-sphere renderer may pretend to replace it.
  const newAtlas=await page.evaluate(()=>window.NPL_READY?.brain3D);
  if(newAtlas?.available!==false||newAtlas?.neverProcedural!==true||
     newAtlas?.expectedStructures!==437)
     throw Error('Public preview fabricated a second pseudo-brain');
  await page.locator('#nplCanonicalOpen').click();
  await page.waitForFunction(()=>window.NPL_CANONICAL_STATUS?.state===
    'SOURCE_NOT_PRESENT_OR_INTEGRITY_FAILED',null,{timeout:11000});
  const sourceGuard=await page.locator('#nplCanonicalStatus').innerText();
  if(!sourceGuard.includes('not installed')||await page.locator('#nplCanonicalFrame').isVisible())
    throw Error('Expected no public original NPL or misleading fake fallback');
  await page.locator('#neurohud > summary').click();
  const missionChoices=['Comprobar procedencia','Comparar mismo periodo','Explorar hipótesis','Proponer y evaluar'];
  for(const choice of missionChoices){
    await page.locator('#nplOptions button').filter({hasText:choice}).click();
  }
  const completed=await page.evaluate(()=>({...window.NPL_MISSION,
    narrative:document.querySelector('#nplFeedback')?.textContent||''}));
  if(!completed.completed||completed.stage!==4||completed.noTracking!==true){
    throw new Error('Mission progression or no-tracking guard failed: '+JSON.stringify(completed));
  }
  await page.locator('#nplOptions button').filter({hasText:'Nueva misión'}).click();
  if(await page.evaluate(()=>window.NPL_MISSION.stage)!==0)throw new Error('Mission restart failed');
  const reportCopy={
    ...state,mission_start:starting,mission_completed:completed,consoleErrors,failedRequests,
    frame:'REAL_CHROMIUM_SOFTWARE_WEBGL_SCREENSHOT_NOT_PERFORMANCE_BENCHMARK',
    preview_url:'local-only'
  };
  if(state.ready?.privateAvatarLoaded!==false || state.loadingVisible ||
     !state.webglCanvas || state.ready?.cityMeshes<1 ||
     state.ready?.windows<500 || state.ready?.facadeStyle!=='artistic_not_surveyed' ||
     state.ready?.urbanKit?.meshGroups!==11 || state.ready?.urbanKit?.palmCount<20 ||
     state.ready?.urbanKit?.scope!=='illustrative_placement_not_surveyed' ||
     state.ready?.urbanKit?.palmSilhouettes!==3 ||
     state.ready?.mosaic?.estimatedPieces<5000 ||
     state.ready?.brain3D?.neverProcedural!==true ||
     state.ready?.hedges?.count<190 || state.ready?.hedges?.meshGroups!==5 ||
     !state.ready?.roadSurface?.asphaltMaterialApplied ||
     state.ready?.roadSurface?.source!=='OSM_centerline_width_estimated_not_surveyed' ||
     !state.selectedCamera.includes('Primera persona')){
    throw new Error('Public review did not load expected geo scene: '+JSON.stringify(reportCopy));
  }
  await page.locator('#neurohud > summary').click();
  await page.locator('#nplCanonicalClose').click();
  if(await page.locator('#nplCanonicalDialog').isVisible())
    throw Error('Atlas modal cannot close and restore 3D city navigation');
  if(await page.locator('#nplBrainCanvas').count())
    throw Error('Fake brain canvas regressed into canonical NeuroCity');
  await page.waitForTimeout(300);
  // Actual Three.js canvas remains interactive while users cycle the
  // session-only dynamic rendering budget: no GLB/model geometry is replaced.
  const perfAtStart=await page.evaluate(()=>window.NEUROCITY_PERFORMANCE_QA);
  if(perfAtStart?.mode!=='auto'||perfAtStart?.plan?.geometryUnchanged!==true||
     perfAtStart?.privateModelInfoExcluded!==true||
     perfAtStart?.rendererDrawingBudgetApplied!==true)
    throw Error('Renderer quality governor did not start on live WebGL');
  await page.locator('#fidelity').click();
  const detail=await page.evaluate(()=>window.NEUROCITY_PERFORMANCE_QA);
  if(detail?.mode!=='detail'||detail?.plan?.tier!=='detail')
    throw Error('Manual quality DETAIL control did not affect live renderer');
  await page.locator('#fidelity').click();
  const low=await page.evaluate(()=>window.NEUROCITY_PERFORMANCE_QA);
  if(low?.mode!=='economy'||low?.plan?.shadowSize!==512)
    throw Error('Manual economy mode or draw-call budget unavailable');
  await page.locator('#fidelity').click();
  const restored=await page.evaluate(()=>window.NEUROCITY_PERFORMANCE_QA);
  if(restored?.mode!=='auto'||restored?.plan?.geometryUnchanged!==true||
     restored?.telemetryNetwork!==false)
    throw Error('Restored AUTO mode mutated private 3D models or opened telemetry');
  reportCopy.adaptive_quality={start:perfAtStart.mode,detail:detail.plan,
    economy:low.plan,restored:restored.mode,geometryProtected:true};
  await page.screenshot({path:'demos/npl-world/visual_viewer/dist/QA_BROWSER_REAL_CHROME.png',fullPage:true});
  // Not four invented photos: four actual WebGL camera frames at one source
  // starting point, to make facade/coast rendering regressions reviewable.
  const cameraBox=await page.locator('#game').boundingBox();
  if(!cameraBox)throw Error('No 3D canvas to inspect from multiple headings');
  const cx=cameraBox.x+cameraBox.width/2,cy=cameraBox.y+cameraBox.height/2;
  const views=[['RIGHT',170,0],['LEFT',-340,0],['UP',170,-90]];
  const captures=[];
  for(const [name,dx,dy] of views){
    await page.mouse.move(cx,cy);
    await page.mouse.down();
    await page.mouse.move(cx+dx,cy+dy,{steps:12});
    await page.mouse.up();
    await page.waitForTimeout(180);
    await page.screenshot({path:'demos/npl-world/visual_viewer/dist/QA_CAMERA_'+name+'.png',fullPage:true});
    captures.push({name,dragPixels:[dx,dy],type:'REAL_WEBGL_NO_PHOTOGRAMMETRIC_VERIFICATION'});
  }
  reportCopy.cameraCaptures=captures;
  report={status:consoleErrors.length?'BROWSER_READY_WITH_SCRIPT_ERRORS':'BROWSER_READY',...reportCopy};
  if(consoleErrors.length) throw new Error('JavaScript console errors detected');
} catch(error) {
  report={status:'BROWSER_QA_FAILED',error:String(error),consoleErrors,failedRequests,...report};
  await page.screenshot({path:'demos/npl-world/visual_viewer/dist/QA_BROWSER_ERROR.png'}).catch(()=>{});
  throw error;
} finally{
  await writeFile('demos/npl-world/visual_viewer/dist/QA_BROWSER.json',JSON.stringify(report,null,2));
  await browser.close();
}
console.log(JSON.stringify(report,null,2));
