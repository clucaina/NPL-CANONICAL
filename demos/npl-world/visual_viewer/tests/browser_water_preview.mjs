import {chromium} from 'playwright';
import {writeFile} from 'node:fs/promises';
const browser=await chromium.launch({headless:true,args:['--no-sandbox','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
const page=await browser.newPage({viewport:{width:1280,height:720}});
const errors=[];
page.on('pageerror',e=>errors.push(e.message));
page.on('console',m=>{if(m.type()==='error'&&/WebGLProgram|shader|compile/i.test(m.text()))errors.push(m.text());});
try{
 await page.goto('http://127.0.0.1:8771/water_preview.html',{waitUntil:'load'});
 await page.waitForFunction(()=>window.NEUROCITY_WATER_QA?.programCount>0,null,{timeout:20000});
 const state=await page.evaluate(()=>window.NEUROCITY_WATER_QA);
 if(state.triangleCount!==2||state.textures!==0||state.geometrySurveyed||!state.noPrivateAssets||errors.length)
  throw Error('Water preview QA failed: '+JSON.stringify({state,errors}));
 await page.screenshot({path:'dist/WATER_WEBGL_REVIEW.png'});
 await writeFile('dist/WATER_WEBGL_QA.json',JSON.stringify({status:'PASS',state,errors},null,2));
 console.log('NEUROCITY_WATER_WEBGL_PASS',JSON.stringify(state));
}finally{await browser.close();}
