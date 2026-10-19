/** Input policy: joystick values never encode real-world coordinates or personal data. */
export function normalizedStick(dx, dy, radius) {
  if (![dx,dy,radius].every(Number.isFinite) || radius<=0) return {x:0,y:0};
  const nx=dx/radius, ny=dy/radius;
  const scale=Math.max(1,Math.hypot(nx,ny));
  return {x:nx/scale,y:ny/scale};
}

/** Preserve analog walking speed, but cap digital+touch diagonals at unit speed. */
export function combineMovement(keyForward,keyStrafe,stickForward,stickStrafe) {
  const values=[keyForward,keyStrafe,stickForward,stickStrafe];
  if(!values.every(Number.isFinite)) return {forward:0,strafe:0,magnitude:0};
  const f=Math.max(-2,Math.min(2,keyForward+stickForward));
  const s=Math.max(-2,Math.min(2,keyStrafe+stickStrafe));
  const length=Math.hypot(f,s);
  const scale=Math.max(1,length);
  return {forward:f/scale,strafe:s/scale,magnitude:Math.min(1,length)};
}
