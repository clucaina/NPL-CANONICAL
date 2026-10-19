import {chromium} from 'playwright';
import {writeFile} from 'node:fs/promises';
// A real mobile viewport + coarse pointer; software WebGL checks functionality, not FPS.
const browser=await chromium.launch({headless:true,args:['--no-sandbox','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
const page=await browser.newPage({viewport:{width:390,height:844},deviceScaleFactor:1,isMobile:true,hasTouch:true});
const errors=[];page.on('pageerror',e=>errors.push(e.message));
let report={status:'NOT_RUN'};
try{
 await page.goto('http://127.0.0.1:8766/',{waitUntil:'domcontentloaded',timeout:40000});
 await page.waitForFunction(()=>window.NPL_READY?.cityOnly===true,null,{timeout:70000});
 const assets=await page.evaluate(()=>window.NPL_READY);
 if(assets?.hedges?.count<100||assets?.hedges?.count>=190||assets?.hedges?.tier!=='mobile'||
    !assets?.roadSurface?.asphaltMaterialApplied)throw Error('Mobile hedges/asphalt LOD unavailable: '+JSON.stringify(assets));
 const urban=await page.evaluate(()=>window.NPL_READY?.urbanKit);
 if(urban?.tier!=='mobile'||urban?.meshGroups!==9||urban?.palmCount<10||urban?.palmCount>=20)throw Error('Mobile instanced LOD is not active: '+JSON.stringify(urban));
 const pad=page.locator('#walkPad');
 if(!await pad.isVisible())throw Error('Mobile control is hidden in coarse-pointer viewport');
 const header=await page.locator('header.panel').boundingBox();
 const controls=await page.locator('#panelControls').boundingBox();
 if(!header||!controls||header.y<controls.y+controls.height+4)
   throw Error('Mobile title and camera controls overlap');
 const bounds=await pad.boundingBox();
 if(!bounds)throw Error('Mobile joystick has no touchable bounds');
 const centerX=bounds.x+bounds.width/2,centerY=bounds.y+bounds.height/2;
 await page.mouse.move(centerX,centerY);
 await page.mouse.down();
 await page.mouse.move(centerX,centerY-40,{steps:4});
 await page.waitForFunction(()=>window.NEUROCITY_INPUT?.forward>0.35,null,{timeout:8000});
 const moving=await page.evaluate(()=>window.NEUROCITY_INPUT);
 await page.waitForTimeout(800);
 await page.mouse.up();
 await page.waitForFunction(()=>window.NEUROCITY_INPUT?.forward===0&&window.NEUROCITY_INPUT?.strafe===0,null,{timeout:8000});
 const stopped=await page.evaluate(()=>window.NEUROCITY_INPUT);
 await page.screenshot({path:'demos/npl-world/visual_viewer/dist/QA_BROWSER_MOBILE.png',fullPage:true});
 if(errors.length)throw Error('Mobile JavaScript errors: '+errors.join('; '));
 report={status:'PASS',width:390,height:844,joystickVisible:true,moving,stopped,privateAvatarLoaded:false,syntheticInputsOnly:true,scriptErrors:errors};
}catch(error){
 report={status:'FAIL',error:String(error),scriptErrors:errors};
 await page.screenshot({path:'demos/npl-world/visual_viewer/dist/QA_BROWSER_MOBILE_ERROR.png'}).catch(()=>{});
 throw error;
}finally{
 await writeFile('demos/npl-world/visual_viewer/dist/QA_BROWSER_MOBILE.json',JSON.stringify(report,null,2));
 await browser.close();
}
console.log(JSON.stringify(report));
