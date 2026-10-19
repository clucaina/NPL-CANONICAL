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
  const reportCopy={
    ...state,consoleErrors,failedRequests,
    frame:'REAL_CHROMIUM_SOFTWARE_WEBGL_SCREENSHOT_NOT_PERFORMANCE_BENCHMARK',
    preview_url:'local-only'
  };
  if(state.ready?.privateAvatarLoaded!==false || state.loadingVisible ||
     !state.webglCanvas || state.ready?.cityMeshes<1 ||
     state.ready?.windows<500 || state.ready?.facadeStyle!=='artistic_not_surveyed' ||
     state.ready?.urbanKit?.meshGroups!==9 || state.ready?.urbanKit?.palmCount<20 ||
     state.ready?.urbanKit?.scope!=='illustrative_placement_not_surveyed' ||
     !state.selectedCamera.includes('Primera persona')){
    throw new Error('Public review did not load expected geo scene: '+JSON.stringify(reportCopy));
  }
  await page.screenshot({path:'demos/npl-world/visual_viewer/dist/QA_BROWSER_REAL_CHROME.png',fullPage:true});
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
