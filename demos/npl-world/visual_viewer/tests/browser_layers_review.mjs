import {chromium} from 'playwright';
import {writeFile} from 'node:fs/promises';
const browser=await chromium.launch({headless:true,args:['--no-sandbox','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
const page=await browser.newPage({viewport:{width:1440,height:900}});
const errors=[];page.on('pageerror',e=>errors.push(e.message));
const make=(origin,value)=>({schema:'neurocity.public-aggregates.v1',origin,dataset_id:'qa_only',published_at:'2026-10-19',license:'TEST ONLY',source_url:'https://example.org/qa',records:[{id:'qa_2025',indicator:'qa_index',label:'Dato sintético exclusivamente para pruebas',value,unit:'index',year:2025,geography_code:'03014',geography_label:'Alicante municipio',resolution:'municipality',source_url:'https://example.org/qa',scope:'public_aggregate'}]});
const upload=async(value,name)=>page.locator('#aggregateFile').setInputFiles({name,mimeType:'application/json',buffer:Buffer.from(JSON.stringify(value))});
let report={};
try{
 await page.goto('http://127.0.0.1:8766/observatory.html',{waitUntil:'domcontentloaded',timeout:30000});
 await page.waitForFunction(()=>document.querySelector('#city')?.contentWindow?.NPL_READY?.cityOnly===true,null,{timeout:70000});
 await upload(make('NPL',42),'npl-test.json');
 await page.getByText('42 index').waitFor();
 await upload(make('CONFLICTOMETRO',17),'conflict-test.json');
 await page.getByText('17 index').waitFor();
 await page.locator('#tabNpl').click();
 await page.getByText('42 index').waitFor();
 const invalid=make('NPL',12);invalid.records[0].name='REJECTED';
 await upload(invalid,'invalid.json');
 await page.getByText('Rechazado:',{exact:false}).waitFor();
 const state=await page.evaluate(()=>({data:window.NEUROCITY_DATA_STATUS,city:document.querySelector('#city')?.contentWindow?.NPL_READY,invalidRejected:document.querySelector('#status')?.textContent.includes('Rechazado:')}));
 if(!state.invalidRejected||state.data.summary[0].count!==1||state.data.summary[1].count!==1||state.city?.privateAvatarLoaded!==false)throw Error('Contract or privacy state failed');
 if(errors.length)throw Error('Browser script errors: '+errors.join('; '));
 await page.screenshot({path:'demos/npl-world/visual_viewer/dist/QA_OBSERVATORY.png',fullPage:true});
 report={status:'PASS',...state,scriptErrors:errors,syntheticFixturesOnly:true};
}catch(e){report={status:'FAIL',error:String(e),scriptErrors:errors};throw e;}
finally{await writeFile('demos/npl-world/visual_viewer/dist/QA_OBSERVATORY.json',JSON.stringify(report,null,2));await browser.close();}
console.log(JSON.stringify(report));
