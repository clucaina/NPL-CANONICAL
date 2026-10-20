import {readFileSync} from "node:fs";
import {test} from "node:test";
import assert from "node:assert/strict";
import vm from "node:vm";

const html=readFileSync(new URL("../index.html",import.meta.url),"utf8");
const script=html.match(/<script>([\s\S]*?)<\/script>/)?.[1]??"";
test("Aplicación autónoma con contenido real",()=>{
 assert.ok(html.includes('id="mosaic"')&&html.includes('id="interpretation"'));
 assert.ok(html.includes('role="img"')&&html.includes('aria-live="polite"'));
 assert.ok(html.includes("BMJ")&&html.includes("https://www.bmj.com/content/345/bmj.e3999"));
 assert.ok(html.includes("no almacena respuestas")||html.includes("No utiliza cookies"));
});
test("Sintaxis del JavaScript principal",()=>{assert.doesNotThrow(()=>new vm.Script(script));});
const start=script.indexOf("function calc("),end=script.indexOf("\nfunction exportFile",start);
assert.ok(start>0&&end>start,"No se ha localizado el calculador");
const calc=vm.runInNewContext("("+script.slice(start,end).trim().replace(/^function calc/,"function calc")+")");
test("Los recuentos conservan toda la población",()=>{
 for(const p of [.1,1,2,10,33.3,50,80])for(const se of [1,30,72,95,100])for(const sp of [1,55,83,96,100]){
  const d=calc(1000,p,se,sp);
  assert.equal(d.tp+d.fp+d.fn+d.tn,1000);
  assert.equal(d.tp+d.fn,d.D);
  assert.equal(d.fp+d.tn,1000-d.D);
  assert.equal(d.tp+d.fp,d.pos);
  assert.ok([d.tp,d.fp,d.fn,d.tn].every(x=>x>=0&&Number.isInteger(x)));
 }
});
test("La tasa base modifica el valor predictivo positivo",()=>{
 const rare=calc(1000,1,90,95);
 const common=calc(1000,50,90,95);
 assert.ok(rare.ppv < common.ppv);
 assert.equal(rare.tp,9);
 assert.equal(rare.fp,50);
 assert.equal(rare.pos,59);
 assert.ok(Math.abs(rare.ppv-100*9/59)<1e-9);
});
test("Sin positivos evita dividir por cero",()=>{
 const x=calc(100,0,90,100);
 assert.equal(x.ppv,null);
 assert.equal(x.pos,0);
 assert.equal(x.tp,0);
 assert.equal(x.fp,0);
});
test("No se recopilan respuestas por telemetría",()=>{
 assert.doesNotMatch(script,/navigator\.sendBeacon|fetch\(|XMLHttpRequest|indexedDB|localStorage|sessionStorage/);
});
