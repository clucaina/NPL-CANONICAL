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
