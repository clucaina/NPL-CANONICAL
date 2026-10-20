/**
 * Coordinate bridge for the actual 2026-10-12 G19 / WORLD_MASTER archived tiles.
 *
 * SOURCE: ETRS89 / UTM zone 30N (EPSG:25830):
 *   master x = easting - 719700; master z = 4248300 - northing.
 * VIEWER: OSM WebMercator local EPSG:3857:
 *   x = mercator_east - origin_east, z = origin_north - mercator_north.
 *
 * Coefficients calculated with pyproj from EPSG:25830 -> EPSG:4326 ->
 * EPSG:3857 using three independent UTM anchors at (0,0),(500,0),(0,500).
 * This affine map is APPROXIMATE: max observed error ~0.4m across 2km.
 * Never label this geodetic mapping as millimeter accuracy.
 * Y datum of source G05 remains UNVERIFIED.
 */
export const SOURCE_CRS='EPSG:25830';
export const VIEWER_CRS='EPSG:3857';
export const SOURCE_ORIGIN=Object.freeze({easting:719700,northing:4248300});
export const WEB_ORIGIN=Object.freeze({lon:-0.48322,lat:38.34402});
export const A=Object.freeze({
  xx:1.27286336, xz:-0.03468129,
  zx:0.03486840, zz:1.27810318,
  tx:-268.417437, tz:-1690.702179
});
export const OBSERVED_MAX_AFFINE_RESIDUAL_M=0.38;
export const VERTICAL_DATUM_VERIFIED=false;
/**
 * Independent pyproj (PROJ 9.x / EPSG:25830 -> EPSG:3857) calculation,
 * 7x7 reference grid per archived tile, local finite-difference Jacobian.
 * Maximum sampled affine horizontal PROJECTION residual 0.0099 m per 500 m.
 * Not measured building/terrain accuracy; vertical datum remains unknown.
 */
export const MAX_SAMPLED_TILE_PROJECTION_ERROR_M=0.010;
export const MASTER_TILE_AFFINES=Object.freeze({
  r02_c00:Object.freeze({
    xx:1.272666757359,xz:-0.034705123471,zx:0.034848973155,zz:1.277942629531,
    tx:-268.379904197,tz:-1690.579833342
  }),
  r02_c01:Object.freeze({
    xx:1.272659001552,xz:-0.034783744195,zx:0.034928042442,zz:1.277934899554,
    tx:-268.277749767,tz:-1690.609724757
  }),
  r01_c01:Object.freeze({
    xx:1.272737624458,xz:-0.034791504731,zx:0.034935772419,zz:1.278013223782,
    tx:-268.328956879,tz:-1690.693851047
  }),
  r01_c02:Object.freeze({
    xx:1.272729859193,xz:-0.034870134550,zx:0.035014702007,zz:1.278005354106,
    tx:-268.262217333,tz:-1690.766897674
  })
});
export function masterTileToViewer(tileId,x,z){
 const affine=MASTER_TILE_AFFINES[tileId];
 if(!affine||!Number.isFinite(x)||!Number.isFinite(z))throw new TypeError('Unknown tile or nonfinite source UTM point');
 return {x:affine.xx*x+affine.xz*z+affine.tx,
         z:affine.zx*x+affine.zz*z+affine.tz};
}
export function matrixElementsForTile(tileId){
 const a=MASTER_TILE_AFFINES[tileId];
 if(!a)throw new Error('Unknown verified 500m tile projection');
 return [a.xx,0,a.zx,0,
         0,1,0,0,
         a.xz,0,a.zz,0,
         a.tx,0,a.tz,1];
}
const finite=(x)=>typeof x==='number'&&Number.isFinite(x);
export function masterToViewer(x,z){
 if(!finite(x)||!finite(z))throw new TypeError('Nonfinite UTM geometry');
 return {x:A.xx*x+A.xz*z+A.tx,z:A.zx*x+A.zz*z+A.tz};
}
export function viewerToMaster(x,z){
 if(!finite(x)||!finite(z))throw new TypeError('Nonfinite public viewer geometry');
 const dx=x-A.tx,dz=z-A.tz;
 const det=A.xx*A.zz-A.xz*A.zx;
 if(Math.abs(det)<1e-8)throw new Error('Singular CRS transform');
 return {x:(A.zz*dx-A.xz*dz)/det,z:(A.xx*dz-A.zx*dx)/det};
}
export function matrixElementsForMaster(){
 // Column major mat4, transforms every source GLB and its local children.
 // Master and viewer share physical Y up; the G05 vertical datum is NOT validated.
 return [A.xx,0,A.zx,0,
         0,1,0,0,
         A.xz,0,A.zz,0,
         A.tx,0,A.tz,1];
}
