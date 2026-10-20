import {chromium} from 'playwright';
import {createHash} from 'node:crypto';
import {readFile,writeFile} from 'node:fs/promises';
import {join} from 'node:path';

const url=process.env.NEUROCITY_PRIVATE_REVIEW_URL;
const folder=process.env.NEUROCITY_PRIVATE_PREVIEW_DIR;
if(!url?.startsWith('http://127.0.0.1:')||!folder)
 throw Error('Only private localhost NeuroCity QA is supported');

const browser=await chromium.launch({headless:true,
 args:['--no-sandbox','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
const page=await browser.newPage({viewport:{width:1366,height:768},deviceScaleFactor:1});
const failures=[],jsErrors=[],shaderErrors=[];
page.on('pageerror',e=>jsErrors.push(String(e.stack||e.message).slice(0,1600)));
page.on('requestfailed',r=>failures.push(r.url()));
page.on('console',m=>{
 if(m.type()==='error'&&/WebGLProgram|VALIDATE_STATUS|shader.{0,35}(compile|error)/i.test(m.text()))
   shaderErrors.push(m.text().slice(0,400));
});
let report={status:'NOT_RUN'};
try{
 const serverQA=await (await page.request.get(url+'QA_CADASTRE_PUBLIC.json')).json();
 const glb=await (await page.request.get(url+'assets/alicante.glb')).body();
 const downloadedSHA=createHash('sha256').update(glb).digest('hex');
 if(downloadedSHA!==serverQA.model_glb_sha256)
  throw Error('Displayed GLB does not equal source-verified Blender file');
 await page.goto(url,{waitUntil:'domcontentloaded',timeout:35000});
 await page.waitForFunction(()=>window.NPL_READY?.cityOnly===true&&
   window.NEUROCITY_CITY_MODEL_QA?.wallTriangles>0,null,{timeout:55000});
 await page.waitForFunction(()=>window.NEUROCITY_WATER_QA?.programCount>=1,null,{timeout:15000});
 const initial=await page.evaluate(()=>({
  model:window.NEUROCITY_CITY_MODEL_QA,
  collision:window.NEUROCITY_COLLISION_QA,
  ready:window.NPL_READY,
  sea:window.NEUROCITY_WATER_QA,
  quality:window.NEUROCITY_RENDER_QUALITY,
  npl:window.NPL_MISSION,
  sourceText:document.querySelector('#nplConflictSummary')?.textContent||''
 }));
 if(initial.model.meshCount<3||initial.model.triangleCount<1000||
    initial.model.wallTriangles<250||initial.model.roofTriangles<250)
    throw Error('Real cadastral+OSM GLB has insufficient valid wall/roof geometry '+JSON.stringify(initial.model));
 if(initial.collision?.wallSegments<100||initial.collision?.inventedBarriers!==0||
    initial.collision?.spatialCells<10||
    initial.collision?.source!=='Blender_real_OSM_and_official_Catastro_wall_mesh')
    throw Error('Real building wall collisions missing: '+JSON.stringify(initial.collision));
 if(initial.collision?.physicalProbe?.examined<16||
    initial.collision?.physicalProbe?.allSampledBlocked!==true||
    initial.collision.physicalProbe.failed!==0||
    initial.collision.physicalProbe.blocked!==initial.collision.physicalProbe.examined)
    throw Error('Actual geographic wall penetration still possible: '+
      JSON.stringify(initial.collision?.physicalProbe));
 if(!initial.ready.cityOnly||initial.ready.privateAvatarLoaded!==false||
     initial.model.privateAvatarObjects!==0||initial.model.invalidGeometry!==0)
    throw Error('Private avatar or invalid mesh material in public scene');
 if(initial.sea.independentSeaLayer!==true||
    initial.sea.source!=='artistic_mediterranean_surface_not_surveyed')
    throw Error('Mediterranean sea shader is not composed with the recovered geographic model');
 await page.waitForFunction(()=>window.NPL_MISSION?.publicEvidenceReady===true,null,{timeout:12000});
 const choices=['Comprobar procedencia','Comparar mismo periodo','Explorar hipótesis','Proponer y evaluar'];
 for(const label of choices)
   await page.locator('#nplOptions button').filter({hasText:label}).click();
 const learning=await page.evaluate(()=>window.NPL_MISSION);
 if(learning?.completed!==true||learning?.stage!==4||learning.noTracking!==true)
   throw Error('NPL/Conflictometro mission failed inside real spatial model');

 // Validate switching quality does not unload any of the new city meshes.
 await page.locator('#fidelity').click();
 const after=await page.evaluate(()=>({model:window.NEUROCITY_CITY_MODEL_QA,
   quality:window.NEUROCITY_RENDER_QUALITY}));
 if(after.model.triangleCount!==initial.model.triangleCount||
    after.quality.high!==false||after.quality.shadowSize!==512)
   throw Error('Quality switch lost 3D model or broke DPR-1 policy');
 if(jsErrors.length||shaderErrors.length||failures.some(x=>x.includes('alicante.glb')))
   throw Error('Real Blender GLB produced a WebGL/runtime error: '+
     JSON.stringify({jsErrors,shaderErrors,failures}));

 // Screenshot is intentionally local and transient; it is never uploaded.
 await page.screenshot({path:join(folder,'PRIVATE_NOT_PUBLISHED_CADASTRE_RENDER.png')});
 report={
   status:'PASS',glbSha256:downloadedSHA,
   officialPartsRendered:serverQA.matched_official_parts+serverQA.native_official_parts,
   completeSourceTiles:serverQA.verified_source_tiles,
   model:initial.model,collision:initial.collision,
   sea:{source:initial.sea.source,programCount:initial.sea.programCount},
   qualityAtDpr1:after.quality,nplMissionVerified:true,
   syntheticNplDataOnly:true,device:'Chromium_headless_SwiftShader',
   realGpuFpsCertified:false,privateAvatarIncluded:false,
   screenshotUploaded:false,sourceGmlUploaded:false,
   shaderErrors,jsErrors
 };
}catch(error){
 report={status:'FAIL',error:String(error),jsErrors,shaderErrors,failedRequests:failures};
 throw error;
}finally{
 await writeFile(join(folder,'QA_PRIVATE_BROWSER.json'),JSON.stringify(report,null,2));
 await browser.close();
}
console.log('PASS real Catastro-derived geographic GLB rendered in private WebGL with NPL mission');
