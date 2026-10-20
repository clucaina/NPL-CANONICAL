/**
 * Bounded asset decode queue for owner-local G19/V50 glTF files.
 * It never changes geometry, caches personal models or opens external services.
 * Completed jobs are resolved in task order only by the caller; the queue
 * does not claim that returning HTTP bytes means a WebGL scene was accepted.
 */
export function createBoundedAssetQueue({concurrency=2}={}){
 if(!Number.isInteger(concurrency)||concurrency<1||concurrency>3)
   throw RangeError('Expected 1..3 concurrent GLB requests');
 let limit=concurrency,closed=false,running=0,maxObserved=0,completed=0,
   skipped=0,failed=0;
 const pending=[];
 function pump(){
   while(!closed&&running<limit&&pending.length){
     const task=pending.shift();
     if(task.cancelled()){
       skipped++;task.resolve(null);continue;
     }
     running++;maxObserved=Math.max(maxObserved,running);
     Promise.resolve().then(()=>{
       if(task.cancelled()){skipped++;return null;}
       return task.work();
     }).then(value=>{
       if(!task.cancelled())completed++;
       task.resolve(task.cancelled()?null:value);
     },error=>{
       failed++;task.reject(error);
     }).finally(()=>{running--;pump();});
   }
 }
 function schedule(work,{cancelled=()=>false}={}){
   if(typeof work!=='function'||typeof cancelled!=='function')
     throw TypeError('Expected a GLB operation and cancellation predicate');
   if(closed)return Promise.reject(Error('GLB queue closed'));
   if(cancelled()){skipped++;return Promise.resolve(null);}
   return new Promise((resolve,reject)=>{
     pending.push({work,cancelled,resolve,reject});pump();
   });
 }
 function discardCancelled(){
   let count=0;
   for(let i=pending.length-1;i>=0;i--){
     if(!pending[i].cancelled())continue;
     const [task]=pending.splice(i,1);
     skipped++;count++;task.resolve(null);
   }
   pump();return count;
 }
 function setConcurrency(next){
   if(!Number.isInteger(next)||next<1||next>3)
     throw RangeError('Expected 1..3 concurrent GLB requests');
   limit=next;pump();return limit;
 }
 function close(){
   if(closed)return;
   closed=true;
   for(const task of pending.splice(0)){skipped++;task.resolve(null);}
 }
 const stats=()=>Object.freeze({concurrencyLimit:limit,running,
   queued:pending.length,maxObserved,completed,failed,skipped,closed,
   userDataRead:false,remoteTelemetry:false});
 return Object.freeze({schedule,discardCancelled,setConcurrency,close,stats});
}
