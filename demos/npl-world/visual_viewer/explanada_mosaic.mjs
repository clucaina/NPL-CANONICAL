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
  irregularGrout:true,surfaceEstimated:true,photoDerived:false,
  geographicFootprintSurveyed:false,
  historicalV50PreferredWhenAvailable:true
 });
}
export function paintMosaic(ctx,{tier='desktop'}={}){
 const spec=mosaicDesign(tier);
 if(!ctx||typeof ctx.fillRect!=='function'||typeof ctx.beginPath!=='function')
   throw new TypeError('Need real 2D canvas context');
 ctx.fillStyle='#a69c8b';ctx.fillRect(0,0,spec.width,spec.height);
 let painted=0;
 for(let row=0,y=0;y<spec.height;row++,y+=spec.tile){
  for(let col=0,x=0;x<spec.width;col++,x+=spec.tile){
   const color=waveBand(x+spec.tile*.5,y+spec.tile*.5,spec.width,spec.height);
   const colors=MOSAIC_PALETTE[color];
   const shade=Math.min(colors.length-1,Math.floor(tileVariation(col,row,2)*colors.length));
   const s=spec.tile,j=.6,margin=.9;
   const corners=[
      [x+margin+tileVariation(col,row,3)*j,y+margin+tileVariation(col,row,4)*j],
      [x+s-margin-tileVariation(col,row,5)*j,y+margin+tileVariation(col,row,6)*j],
      [x+s-margin-tileVariation(col,row,7)*j,y+s-margin-tileVariation(col,row,8)*j],
      [x+margin+tileVariation(col,row,9)*j,y+s-margin-tileVariation(col,row,10)*j]
   ];
   ctx.beginPath();
   ctx.moveTo(...corners[0]);ctx.lineTo(...corners[1]);
   ctx.lineTo(...corners[2]);ctx.lineTo(...corners[3]);ctx.closePath();
   ctx.fillStyle=colors[shade];ctx.fill();painted++;
   // Tiny glazed ridge, not fake deep tile bevels.
   if(spec.tier==='desktop'){
     ctx.strokeStyle='rgba(255,246,229,.13)';ctx.lineWidth=.42;
     ctx.beginPath();ctx.moveTo(...corners[3]);ctx.lineTo(...corners[0]);
     ctx.lineTo(...corners[1]);ctx.stroke();
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
 const map=new THREE.CanvasTexture(canvas);
 map.colorSpace=THREE.SRGBColorSpace;
 map.wrapS=map.wrapT=THREE.RepeatWrapping;
 map.anisotropy=Math.min(12,renderer?.capabilities?.getMaxAnisotropy?.()||4);
 map.repeat.set(1,5);
 map.generateMipmaps=true;
 const mat=new THREE.MeshPhysicalMaterial({
  name:'NEUROCITY_ALICANTE_WAVE_TESSELLATED_CERAMIC',
  map,color:0xffffff,roughness:.77,metalness:0,
  clearcoat:.12,clearcoatRoughness:.62
 });
 mat.userData={source:MOSAIC_SOURCE,uniqueTesserae:info.painted,
   material:'procedural_irregular_ceramic_with_grout',
   V50SourceAvailableOnlyInPrivateLocalPack:true,
   locationSurveyed:false};
 return {material:mat,texture:map,report:{...info,publicOriginalProcedural:true}};
}
