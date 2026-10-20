import { chromium } from 'playwright';
import { writeFile } from 'node:fs/promises';
const url=process.env.PREVIEW_URL || 'http://127.0.0.1:8766/';
const browser=await chromium.launch({
  headless:true,
  args:['--no-sandbox','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader']
});
const page=await browser.newPage({viewport:{width:1440,height:900},deviceScaleFactor:1});
const consoleErrors=[],failedRequests=[],shaderErrors=[];
page.on('pageerror',error=>consoleErrors.push(error.message));
page.on('console',message=>{
 if(message.type()==='error' && /WebGLProgram|shader.{0,35}(error|compile)|VALIDATE_STATUS/i.test(message.text()))
   shaderErrors.push(message.text().slice(0,300));
});
page.on('requestfailed',request=>failedRequests.push(request.url()));
let report={};
try{
  await page.goto(url,{waitUntil:'domcontentloaded',timeout:40000});
  await page.waitForFunction(()=>window.NPL_READY?.cityOnly===true,null,{timeout:60000});
  await page.waitForTimeout(1200);
  await page.waitForFunction(()=>window.NEUROCITY_WATER_QA?.programCount>0,null,{timeout:15000});
  const waterBefore=await page.evaluate(()=>window.NEUROCITY_WATER_QA);
  const initialQuality=await page.evaluate(()=>window.NEUROCITY_RENDER_QUALITY);
  if(waterBefore.source!=='artistic_mediterranean_surface_not_surveyed' ||
    waterBefore.triangleCount!==2||waterBefore.textures!==0||waterBefore.geometrySurveyed!==false ||
    waterBefore.programCount<1||initialQuality.high!==true||shaderErrors.length){
     throw Error('Procedural Mediterranean WebGL not ready: '+JSON.stringify({waterBefore,initialQuality,shaderErrors}));
  }
  // DPR=1 used to make the old fidelity toggle ineffective.
  await page.locator('#fidelity').click();
  const qualityLow=await page.evaluate(()=>window.NEUROCITY_RENDER_QUALITY);
  if(qualityLow.high!==false||qualityLow.shadowSize!==512||qualityLow.waterDetail!==0||
    await page.locator('#fidelity').getAttribute('aria-pressed')!=='false')
    throw Error('Quality-low toggle is not applied at DPR=1');
  await page.waitForFunction(()=>window.NEUROCITY_WATER_QA?.detail===0,null,{timeout:5000});
  await page.locator('#fidelity').click();
  const qualityHigh=await page.evaluate(()=>window.NEUROCITY_RENDER_QUALITY);
  if(qualityHigh.high!==true||qualityHigh.shadowSize!==2048||qualityHigh.waterDetail!==1||
    await page.locator('#fidelity').getAttribute('aria-pressed')!=='true')
    throw Error('Quality-high restore is not applied');
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
    ...state,waterBefore,initialQuality,qualityLow,qualityHigh,shaderErrors,
    mission_start:starting,mission_completed:completed,consoleErrors,failedRequests,
    frame:'REAL_CHROMIUM_SOFTWARE_WEBGL_SCREENSHOT_NOT_PERFORMANCE_BENCHMARK',
    preview_url:'local-only'
  };
  if(state.ready?.privateAvatarLoaded!==false || state.loadingVisible ||
     !state.webglCanvas || state.ready?.cityMeshes<1 ||
     state.ready?.windows<500 || state.ready?.facadeStyle!=='artistic_not_surveyed' ||
     state.ready?.urbanKit?.meshGroups!==9 || state.ready?.urbanKit?.palmCount<20 ||
     state.ready?.urbanKit?.scope!=='illustrative_placement_not_surveyed' ||
     state.ready?.hedges?.count<190 || state.ready?.hedges?.meshGroups!==5 ||
     !state.ready?.roadSurface?.asphaltMaterialApplied ||
     state.ready?.roadSurface?.source!=='OSM_centerline_width_estimated_not_surveyed' ||
     !state.selectedCamera.includes('Primera persona')){
    throw new Error('Public review did not load expected geo scene: '+JSON.stringify(reportCopy));
  }
  await page.screenshot({path:'demos/npl-world/visual_viewer/dist/QA_BROWSER_REAL_CHROME.png',fullPage:true});
  report={status:consoleErrors.length?'BROWSER_READY_WITH_SCRIPT_ERRORS':'BROWSER_READY',...reportCopy};
  if(consoleErrors.length||shaderErrors.length)
    throw new Error('JavaScript or shader console errors detected');
} catch(error) {
  report={status:'BROWSER_QA_FAILED',error:String(error),consoleErrors,failedRequests,...report};
  await page.screenshot({path:'demos/npl-world/visual_viewer/dist/QA_BROWSER_ERROR.png'}).catch(()=>{});
  throw error;
} finally{
  await writeFile('demos/npl-world/visual_viewer/dist/QA_BROWSER.json',JSON.stringify(report,null,2));
  await browser.close();
}
console.log(JSON.stringify(report,null,2));
