import {readFileSync} from "node:fs";
import {test} from "node:test";
import assert from "node:assert/strict";
import vm from "node:vm";

const html=readFileSync(new URL("../index.html",import.meta.url),"utf8");
const script=html.match(/<script>([\s\S]*?)<\/script>/)?.[1]??"";
test("Interfaz y script válidos",()=>{
 assert.doesNotThrow(()=>{try{new vm.Script(script,{filename:'fuentes-embedded.js'});}catch(e){console.error(e.stack);throw e;}});
 for(const token of ["id=\"graph\"","id=\"origin\"","id=\"routeList\"","id=\"memo\"","fuentes-dependientes.json","38298368"])assert.ok(html.includes(token),token);
});
const begin=script.indexOf("function routes(){"),end=script.indexOf("\nfunction render()",begin);
assert.ok(begin>0&&end>begin);
const context={people:[]};
const routes=vm.runInNewContext("("+script.slice(begin,end).trim()+")",context);
const initial=[
 {id:"a",origin:"self"},{id:"b",origin:"a"},{id:"c",origin:"self"},
 {id:"d",origin:"b"},{id:"e",origin:"unknown"},{id:"f",origin:"unknown"}
];
test("Una fuente repetida no se cuenta como dos fuentes directas",()=>{
 context.people=initial.map(x=>({...x}));
 const r=routes();
 assert.equal(r.a,"a");
 assert.equal(r.b,"a");
 assert.equal(r.d,"a");
 assert.equal(r.c,"c");
});
test("Orígenes desconocidos no se fusionan de manera ficticia",()=>{
 context.people=initial.map(x=>({...x}));
 const r=routes();
 assert.equal(r.e,"indeterminado:e");
 assert.equal(r.f,"indeterminado:f");
});
test("Se detectan ciclos y no se interpretan como observaciones válidas",()=>{
 context.people=initial.map(x=>({...x}));
 context.people[0].origin="d";
 const r=routes();
 assert.equal(r.a,"ciclo");
 assert.equal(r.b,"ciclo");
 assert.equal(r.d,"ciclo");
});
test("El cuaderno no envía relatos a servidores",()=>{
 assert.doesNotMatch(script,/fetch\(|XMLHttpRequest|navigator\.sendBeacon|localStorage|sessionStorage/);
 assert.ok(script.includes("replace(/^[=+\\-@\\t\\r]/"));
});
