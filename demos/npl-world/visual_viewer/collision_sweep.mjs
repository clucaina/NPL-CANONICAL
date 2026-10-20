// Exact 2D narrowphase for actual wall segments extracted from the loaded GLB.
// Local scene metres only; does not certify geodetic elevations.
const finite=(...v)=>v.every(Number.isFinite);
const EPS=1e-9;
const clamp01=t=>Math.max(0,Math.min(1,t));
const orient=(ax,az,bx,bz,cx,cz)=>(bx-ax)*(cz-az)-(bz-az)*(cx-ax);

export function pointSegmentDistance(x,z,ax,az,bx,bz){
 if(!finite(x,z,ax,az,bx,bz))throw new RangeError('Nonfinite collision geometry');
 const dx=bx-ax,dz=bz-az,den=dx*dx+dz*dz;
 if(den<EPS)return Math.hypot(x-ax,z-az);
 const t=clamp01(((x-ax)*dx+(z-az)*dz)/den);
 return Math.hypot(x-(ax+t*dx),z-(az+t*dz));
}

function properCross(ax,az,bx,bz,cx,cz,dx,dz){
 const o1=orient(ax,az,bx,bz,cx,cz);
 const o2=orient(ax,az,bx,bz,dx,dz);
 const o3=orient(cx,cz,dx,dz,ax,az);
 const o4=orient(cx,cz,dx,dz,bx,bz);
 return (o1>EPS&&o2< -EPS || o1< -EPS&&o2>EPS) &&
        (o3>EPS&&o4< -EPS || o3< -EPS&&o4>EPS);
}

export function sweptCircleHitsSegment(x,z,toX,toZ,e,radius){
 if(!e||!finite(x,z,toX,toZ,e.ax,e.az,e.bx,e.bz,radius)||radius<=0)
  throw new RangeError('Nonfinite or unsafe collision sweep');
 if(Math.hypot(e.bx-e.ax,e.bz-e.az)<EPS)return false;
 const fromDist=pointSegmentDistance(x,z,e.ax,e.az,e.bx,e.bz);
 const toDist=pointSegmentDistance(toX,toZ,e.ax,e.az,e.bx,e.bz);
 const crossed=properCross(x,z,toX,toZ,e.ax,e.az,e.bx,e.bz);
 if(crossed)return true;
 // A spawn already overlapping the wall must be allowed to escape or slide,
 // but cannot travel deeper into the collider.
 if(fromDist<radius-1e-7)return toDist<fromDist-1e-7;
 const minDist=Math.min(fromDist,toDist,
  pointSegmentDistance(e.ax,e.az,x,z,toX,toZ),
  pointSegmentDistance(e.bx,e.bz,x,z,toX,toZ));
 return minDist<radius-1e-7;
}

// Local-space guard; passing is NOT an official measured ground datum.
export function withinLocalFloorTolerance(wallBaseY,localGroundY=0,maxOffsetMeters=2){
 if(!finite(wallBaseY,localGroundY,maxOffsetMeters)||maxOffsetMeters<=0||maxOffsetMeters>2)
  throw new RangeError('Invalid local vertical tolerance');
 return Math.abs(wallBaseY-localGroundY)<=maxOffsetMeters+EPS;
}
