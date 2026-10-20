import * as THREE from 'three';

/**
 * Alicante Explanada – wave mosaic study derived from the characteristic
 * black/cream/terracotta trencadís visual vocabulary.
 * Original procedural tesserae, NOT photogrammetry, measured tile layout or
 * copied photos. Historic local V50 PBR is preferred when available.
 */
export const MOSAIC_SOURCE='alicante_explanada_artistic_ceramic_study_v2';
export const MOSAIC_PALETTE=Object.freeze({
  cream:Object.freeze(['#f5eddb','#e9dfc8','#ddd1ba','#fff6e5']),
  terracotta:Object.freeze(['#a7604c','#bb765f','#cb8a72','#984c43']),
  slate:Object.freeze(['#1d3438','#2c4447','#3b5455','#12292f'])
});
const SEED=73171;
const clamp=(n,a,b)=>Math.max(a,Math.min(b,n));
const fract=x=>x-Math.floor(x);
export function tileVariation(col,row,channel=0){
 if(![col,row,channel].every(Number.isFinite))throw new TypeError('Invalid tile');
 return fract(Math.sin((col+1.7)*127.1+(row+2.3)*311.7+channel*17.9+SEED)*43758.5453);
}
export function waveBand(x,y,width=1024,height=1536){
 if(![x,y,width,height].every(Number.isFinite)||width<=0||height<=0)
   throw new TypeError('Nonfinite mosaic coordinates');
 // Waves rotate and run along the Paseo axis. All three traditional colors
 // alternate in curved ribbons rather than the former 4px sine checkerboard.
 const wave=0.076*width*Math.sin((y/height)*Math.PI*3.1+0.27)
       +0.015*width*Math.sin((y/height)*Math.PI*7.4+1.75);
 const across=(x+wave)/width;
 const phase=fract(across*5.6);
 if(phase<.24)return 'slate';
 if(phase<.47)return 'cream';
 if(phase<.71)return 'terracotta';
 return 'cream';
}
export function mosaicDesign(tier='desktop'){
 if(!['mobile','desktop'].includes(tier))throw new RangeError('Invalid texture tier');
 const width=tier==='mobile'?768:1024;
 const height=tier==='mobile'?1024:1536;
 const tile=tier==='mobile'?12:10;
 return Object.freeze({
  source:MOSAIC_SOURCE,tier,width,height,tile,
  estimatedPieces:Math.ceil(width/tile)*Math.ceil(height/tile),
  colors:['slate','cream','terracotta'],
  irregularGrout:true,ceramicShapes:'staggered_irregular_hexagonal_fragments',surfaceEstimated:true,photoDerived:false,
  geographicFootprintSurveyed:false,
  historicalV50PreferredWhenAvailable:true
 });
}
export function paintMosaic(ctx,{tier='desktop',relief=false}={}){
 if(typeof relief!=='boolean')throw new TypeError('Relief must be boolean');
 const spec=mosaicDesign(tier);
 if(!ctx||typeof ctx.fillRect!=='function'||typeof ctx.beginPath!=='function')
   throw new TypeError('Need real 2D canvas context');
 ctx.fillStyle=relief?'#464646':'#a69c8b';ctx.fillRect(0,0,spec.width,spec.height);
 let painted=0;
 for(let row=0,y=0;y<spec.height;row++,y+=spec.tile){
  for(let col=0,x=0;x<spec.width;col++,x+=spec.tile){
   const color=waveBand(x+spec.tile*.5,y+spec.tile*.5,spec.width,spec.height);
   const colors=MOSAIC_PALETTE[color];
   const shade=Math.min(colors.length-1,Math.floor(tileVariation(col,row,2)*colors.length));
   // Staggered six-sided broken ceramic tesserae. A regular square grid
   // recreated the old "LEGO" look even with better colors; asymmetric
   // facets and changing grout joints break that artificial alignment.
   const s=spec.tile,cx=x+s*(.49+(row%2)*.45),cy=y+s*.51;
   const corners=[];
   for(let k=0;k<6;k++){
     const ang=(Math.PI/3)*k+Math.PI/6+
       (tileVariation(col,row,11+k)-.5)*.17;
     const radial=s*(.465+.08*(tileVariation(col,row,18+k)-.5));
     corners.push([cx+Math.cos(ang)*radial,cy+Math.sin(ang)*radial]);
   }
   ctx.beginPath();
   ctx.moveTo(...corners[0]);
   for(const corner of corners.slice(1))ctx.lineTo(...corner);
   ctx.closePath();
   ctx.fillStyle=relief?'#dadada':colors[shade];ctx.fill();painted++;
   // Tiny glazed ridge, not fake deep tile bevels.
   if(spec.tier==='desktop'){
     ctx.strokeStyle=relief?'rgba(255,255,255,.19)':'rgba(255,246,229,.13)';ctx.lineWidth=.42;
     ctx.beginPath();ctx.moveTo(...corners[4]);ctx.lineTo(...corners[5]);
     ctx.lineTo(...corners[0]);ctx.stroke();
   }
  }
 }
 return {...spec,painted};
}
export function createExplanadaMosaic({tier='desktop',renderer=null}={}){
 if(typeof document==='undefined'||!document.createElement)
   throw Error('Browser canvas required for renderable tiles');
 const spec=mosaicDesign(tier),canvas=document.createElement('canvas');
 canvas.width=spec.width;canvas.height=spec.height;
 const ctx=canvas.getContext('2d',{alpha:false});
 if(!ctx)throw Error('Canvas 2D unavailable');
 const info=paintMosaic(ctx,{tier});
 const reliefCanvas=document.createElement('canvas');
 reliefCanvas.width=spec.width;reliefCanvas.height=spec.height;
 const reliefContext=reliefCanvas.getContext('2d',{alpha:false});
 if(!reliefContext)throw Error('Ceramic relief canvas unavailable');
 paintMosaic(reliefContext,{tier,relief:true});
 const bumpMap=new THREE.CanvasTexture(reliefCanvas);
 bumpMap.wrapS=bumpMap.wrapT=THREE.RepeatWrapping;
 bumpMap.repeat.set(1,5);
 bumpMap.generateMipmaps=true;
 bumpMap.anisotropy=Math.min(8,renderer?.capabilities?.getMaxAnisotropy?.()||4);
 const map=new THREE.CanvasTexture(canvas);
 map.colorSpace=THREE.SRGBColorSpace;
 map.wrapS=map.wrapT=THREE.RepeatWrapping;
 map.anisotropy=Math.min(12,renderer?.capabilities?.getMaxAnisotropy?.()||4);
 map.repeat.set(1,5);
 map.generateMipmaps=true;
 const mat=new THREE.MeshPhysicalMaterial({
  name:'NEUROCITY_ALICANTE_WAVE_TESSELLATED_CERAMIC',
  map,bumpMap,bumpScale:.008,color:0xffffff,roughness:.77,metalness:0,
  clearcoat:.12,clearcoatRoughness:.62
 });
 mat.userData={source:MOSAIC_SOURCE,uniqueTesserae:info.painted,
   material:'procedural_irregular_ceramic_with_grout',
   V50SourceAvailableOnlyInPrivateLocalPack:true,
   locationSurveyed:false};
 return {material:mat,texture:map,bumpMap,report:{...info,
    ceramicReliefBumpScaleMetres:.008,publicOriginalProcedural:true}};
}
