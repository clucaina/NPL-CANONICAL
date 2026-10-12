import {chromium} from "playwright";
import assert from "node:assert/strict";
import {pathToFileURL} from "node:url";
import {resolve} from "node:path";
import {mkdirSync} from "node:fs";

const browser=await chromium.launch({headless:true});
const errors=[];
const dir=resolve("qa-artifacts");
mkdirSync(dir,{recursive:true});
async function visit(page,name,path){
 page.on("pageerror",e=>errors.push(name+": "+e.message));
 await page.goto(pathToFileURL(resolve(path)).href,{waitUntil:"load"});
 await page.waitForTimeout(250);
}
try{
 const desktop=await browser.newPage({viewport:{width:1380,height:900},acceptDownloads:true});
 await visit(desktop,"tasa-base","educacion/inferencia-tasa-base/index.html");
 assert.equal(await desktop.locator("#mosaic svg.person").count(),400);
 const initial=await desktop.locator("#ppv").innerText();
 await desktop.locator("#prev").evaluate(el=>{el.value="50";el.dispatchEvent(new Event("input",{bubbles:true}));});
 const changed=await desktop.locator("#ppv").innerText();
 assert.notEqual(initial,changed);
 const download=desktop.waitForEvent("download");
 await desktop.locator("#json").click();
 assert.match((await download).suggestedFilename(),/evidencia\.json/);
 await desktop.screenshot({path:resolve(dir,"tasa-base-desktop.png"),fullPage:true});
 const witness=await browser.newPage({viewport:{width:1365,height:850},acceptDownloads:true});
 await visit(witness,"fuentes","educacion/fuentes-dependientes/index.html");
 assert.equal(await witness.locator(".person-card").count(),6);
 assert.equal((await witness.locator("#unknown").innerText()).trim(),"2");
 await witness.locator('button[data-person="b"]').click();
 await witness.locator("#origin").selectOption("unknown");
 await witness.locator("#apply").click();
 assert.equal((await witness.locator("#unknown").innerText()).trim(),"3");
 await witness.locator('button[data-person="a"]').click();
 await witness.locator("#origin").selectOption("d");
 await witness.locator("#apply").click();
 assert.match(await witness.locator("#warning").innerText(),/ciclo/i);
 await witness.screenshot({path:resolve(dir,"fuentes-desktop.png"),fullPage:true});
 for(const path of ["educacion/inferencia-tasa-base/index.html","educacion/fuentes-dependientes/index.html"]){
  const mobile=await browser.newPage({viewport:{width:390,height:844},isMobile:true,hasTouch:true});
  await visit(mobile,"mobile "+path,path);
  const bounds=await mobile.evaluate(()=>({scroll:document.documentElement.scrollWidth,width:window.innerWidth}));
  assert.ok(bounds.scroll<=bounds.width+2,JSON.stringify({path,...bounds}));
  await mobile.screenshot({path:resolve(dir,path.includes("tasa")?"tasa-base-mobile.png":"fuentes-mobile.png"),fullPage:true});
  await mobile.close();
 }
 assert.deepEqual(errors,[]);
 console.log("Browser QA PASSED: base-rate and witness labs; desktop, mobile, export, sliders and cycle.");
}finally{await browser.close();}
