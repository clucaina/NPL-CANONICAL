// NPL World: pure graphics budget controller (no data collection, no network).
export const QUALITY_MODES = Object.freeze(['auto','ultra','balanced','economy']);
const BUDGETS = Object.freeze({
 auto: Object.freeze({maxPixels:3000000, maxDpr:2, shadow:1024}),
 ultra: Object.freeze({maxPixels:12000000, maxDpr:3, shadow:2048}),
 balanced: Object.freeze({maxPixels:2000000, maxDpr:1.75, shadow:1024}),
 economy: Object.freeze({maxPixels:1000000, maxDpr:1.25, shadow:512})
});
export function qualityBudget(mode) {
 return BUDGETS[mode] || BUDGETS.auto;
}
export function choosePixelRatio({width,height,deviceRatio=1,mode='auto',autoScale=1}) {
 const b=qualityBudget(mode);
 if(!Number.isFinite(width)||!Number.isFinite(height)||width<=0||height<=0)return 1;
 const native=Number.isFinite(deviceRatio)&&deviceRatio>0?deviceRatio:1;
 const pixelBound=Math.sqrt(b.maxPixels/Math.max(1,width*height));
 const scale=mode==='auto'&&Number.isFinite(autoScale)?Math.max(.6,Math.min(1,autoScale)):1;
 return Math.round(Math.max(.5,Math.min(native,b.maxDpr,pixelBound)*scale)*100)/100;
}
export function nextAutoScale(scale,fps) {
 if(!Number.isFinite(fps)||fps<=0)return scale;
 if(fps<34)return Math.max(.6,Math.round((scale-.1)*100)/100);
 if(fps>56)return Math.min(1,Math.round((scale+.05)*100)/100);
 return scale;
}
