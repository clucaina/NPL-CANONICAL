/** Deterministic WebGL quality policy. No user data, network or WebGL context. */
export function qualityProfile({high, coarse, devicePixelRatio} = {}) {
  if (typeof high !== 'boolean' || typeof coarse !== 'boolean')
    throw new TypeError('Quality and pointer type must be booleans');
  if (!Number.isFinite(devicePixelRatio) || devicePixelRatio <= 0)
    throw new RangeError('Device pixel ratio must be finite and positive');
  return Object.freeze({
    high,
    tier: coarse ? 'mobile' : 'desktop',
    pixelRatio: Math.min(devicePixelRatio, high ? (coarse ? 1.35 : 1.75) : 1),
    shadowSize: high ? (coarse ? 1024 : 2048) : 512,
    waterDetail: high && !coarse ? 1 : 0,
  });
}
